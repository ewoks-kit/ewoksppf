import os
import pprint
import warnings
from contextlib import contextmanager
from typing import Generator
from typing import List
from typing import Optional
from typing import Sequence

from ewokscore import events
from ewokscore import execute_graph_decorator
from ewokscore import load_graph
from ewokscore import ppftasks
from ewokscore.graph import TaskGraph
from ewokscore.graph import analysis
from ewokscore.inittask import task_executable
from ewokscore.inittask import task_executable_info
from ewokscore.node import NodeIdType
from ewokscore.node import get_node_label
from ewokscore.node import get_varinfo
from ewokscore.node import node_id_as_string
from ewokscore.variable import value_from_transfer
from pypushflow.AbstractActor import AbstractActor
from pypushflow.ErrorHandler import ErrorHandler
from pypushflow.JoinActor import JoinActor
from pypushflow.persistence import register_actorinfo_filter
from pypushflow.PythonActor import PythonActor
from pypushflow.StartActor import StartActor
from pypushflow.StopActor import StopActor
from pypushflow.ThreadCounter import ThreadCounter
from pypushflow.Workflow import Workflow

from . import ppfrunscript


def ppfname(node_id: NodeIdType) -> str:
    return node_id_as_string(node_id, sep="/")


def varinfo_from_indata(inData: dict) -> Optional[dict]:
    if ppfrunscript.INFOKEY not in inData:
        return None
    varinfo = inData[ppfrunscript.INFOKEY].get("varinfo", None)
    node_attrs = inData[ppfrunscript.INFOKEY].get("node_attrs", dict())
    return get_varinfo(node_attrs, varinfo=varinfo)


def is_ppfmethod(node_id: NodeIdType, node_attrs: dict) -> bool:
    task_type, _ = task_executable_info(node_id, node_attrs)
    return task_type in ("ppfmethod", "ppfport")


def actordata_filter(actorData: dict) -> dict:
    skip = (ppfrunscript.INFOKEY, ppftasks.PPF_DICT_ARGUMENT)
    for key in ["inData", "outData"]:
        data = actorData.get(key, None)
        if data is None:
            continue
        varinfo = varinfo_from_indata(data)
        actorData[key] = {
            k: value_from_transfer(v, varinfo=varinfo)
            for k, v in data.items()
            if k not in skip
        }
        if ppftasks.PPF_DICT_ARGUMENT in data:
            ppfdict = value_from_transfer(
                data[ppftasks.PPF_DICT_ARGUMENT], varinfo=varinfo
            )
            if ppfdict:
                actorData[key].update(ppfdict)
    return actorData


register_actorinfo_filter(actordata_filter)


class EwoksPythonActor(PythonActor):
    def __init__(self, node_id, node_attrs, **kw):
        self.node_id = node_id
        self.node_attrs = node_attrs
        kw["name"] = ppfname(node_id)
        super().__init__(**kw)

    def trigger(self, inData: dict):
        # Update the INFOKEY with node information
        infokey = ppfrunscript.INFOKEY
        inData[infokey] = dict(inData[infokey])
        inData[infokey]["node_id"] = self.node_id
        inData[infokey]["node_attrs"] = self.node_attrs
        return super().trigger(inData)

    def compileDownstreamData(self, result: dict) -> dict:
        # Merging inputs and outputs to trigger the next task
        # is not an ewoks convention. `ppfmethod` tasks still
        # have it thanks to `ewokscore.ppftasks`.
        #
        # We do need to take INFOKEY from the inputs.
        return {ppfrunscript.INFOKEY: self.inData[ppfrunscript.INFOKEY], **result}

    def uploadInDataToMongo(self, **kw):
        task_identifier = self.node_attrs.get("task_identifier")
        if task_identifier:
            kw["script"] = task_identifier
            super().uploadInDataToMongo(**kw)

    def uploadOutDataToMongo(self, **kw):
        task_identifier = self.node_attrs.get("task_identifier")
        if task_identifier:
            super().uploadOutDataToMongo(**kw)


class ConditionalActor(AbstractActor):
    """Triggers downstream actors when conditions are fulfilled."""

    def __init__(
        self,
        conditions: dict,
        all_conditions: dict,
        conditions_else_value,
        is_ppfmethod: bool = False,
        **kw,
    ):
        self.conditions = conditions
        self.all_conditions = all_conditions
        self.conditions_else_value = conditions_else_value
        self.is_ppfmethod = is_ppfmethod
        super().__init__(**kw)

    def _conditions_fulfilled(self, inData: dict) -> bool:
        if not self.conditions:
            return True

        varinfo = varinfo_from_indata(inData)
        compareDict = dict(inData)
        if self.is_ppfmethod:
            ppfdict = compareDict.pop(ppftasks.PPF_DICT_ARGUMENT, None)
            compareDict.update(value_from_transfer(ppfdict, varinfo=varinfo))
        compareDict.pop(ppfrunscript.INFOKEY)

        for varname, value in self.conditions.items():
            if varname not in compareDict:
                return False
            invalue = value_from_transfer(compareDict[varname], varinfo=varinfo)
            if value == self.conditions_else_value:
                if (
                    invalue != self.conditions_else_value
                    and invalue in self.all_conditions[varname]
                ):
                    return False
            else:
                if invalue != value:
                    return False
        return True

    def trigger(self, inData):
        self.logger.info("triggered with inData =\n %s", pprint.pformat(inData))
        self.setStarted()
        trigger = self._conditions_fulfilled(inData)
        self.setFinished()
        if trigger:
            for actor in self.listDownStreamActor:
                actor.trigger(inData)


class NameMapperActor(AbstractActor):
    """Maps output names to downstream input names for
    one source-target pair.
    """

    def __init__(
        self,
        namemap=None,
        map_all_data=False,
        name="Name mapper",
        trigger_on_error=False,
        required=False,
        **kw,
    ):
        super().__init__(name=name, **kw)
        self.namemap = namemap
        self.map_all_data = map_all_data
        self.trigger_on_error = trigger_on_error
        self.required = required

    def connect(self, actor):
        super().connect(actor)
        if isinstance(actor, InputMergeActor):
            actor.require_input_from_actor(self)

    def trigger(self, inData: dict):
        self.logger.info("triggered with inData =\n %s", pprint.pformat(inData))
        is_error = "WorkflowExceptionInstance" in inData and inData.get(
            "_NewWorkflowException"
        )
        if is_error and not self.trigger_on_error:
            return
        try:
            if is_error:
                inData = dict(inData)
                inData["_NewWorkflowException"] = False
            # Map output names of this task to input
            # names of the downstream task
            newInData = dict()
            if self.map_all_data:
                newInData.update(inData)
            for input_name, output_name in self.namemap.items():
                newInData[input_name] = inData[output_name]

            newInData[ppfrunscript.INFOKEY] = dict(inData[ppfrunscript.INFOKEY])
            for actor in self.listDownStreamActor:
                if isinstance(actor, InputMergeActor):
                    actor.trigger(newInData, source=self)
                else:
                    actor.trigger(newInData)
        except Exception as e:
            self.logger.exception(e)
            raise


class InputMergeActor(AbstractActor):
    """Requires triggers from some input actors before triggering
    the downstream actors.

    It remembers the last input from the required uptstream actors.
    Only the last non-required input is remembered.
    """

    def __init__(self, parent=None, name="Input merger", **kw):
        super().__init__(parent=parent, name=name, **kw)
        self.startInData = list()
        self.requiredInData = dict()
        self.nonrequiredInData = dict()

    def require_input_from_actor(self, actor):
        if actor.required:
            self.requiredInData[actor] = None

    def trigger(self, inData: dict, source=None):
        self.logger.info("triggered with inData =\n %s", pprint.pformat(inData))
        self.setStarted()
        self.setFinished()
        if source is None:
            self.startInData.append(inData)
        else:
            if source in self.requiredInData:
                self.requiredInData[source] = inData
            else:
                self.nonrequiredInData = inData
        missing = {k: v for k, v in self.requiredInData.items() if v is None}
        if missing:
            self.logger.info(
                "not triggering downstream actors because missing inputs from actors %s",
                [actor.name for actor in missing],
            )
            return
        self.logger.info(
            "triggering downstream actors (%d start inputs, %d required inputs, %d optional inputs)",
            len(self.startInData),
            len(self.requiredInData),
            int(bool(self.nonrequiredInData)),
        )
        newInData = dict()
        for data in self.startInData:
            newInData.update(data)
        for data in self.requiredInData.values():
            newInData.update(data)
        newInData.update(self.nonrequiredInData)
        for actor in self.listDownStreamActor:
            actor.trigger(newInData)


class EwoksWorkflow(Workflow):
    def __init__(self, ewoksgraph: TaskGraph, pre_import: Optional[bool] = None, **kw):
        name = ewoksgraph.graph_label
        super().__init__(name, **kw)
        self._pre_import = pre_import

        # When triggering a task, the output dict of the previous task
        # is merged with the input dict of the current task.
        self.startargs = {ppfrunscript.INFOKEY: {"varinfo": None, "execinfo": None}}
        self.graph_to_actors(ewoksgraph)
        self.__ewoksgraph = ewoksgraph

    def _clean_workflow(self):
        # task_name -> EwoksPythonActor
        self._taskactors = dict()
        self.listActorRef = list()  # values of taskactors

        # source_id -> target_id -> NameMapperActor
        self._sourceactors = dict()

        # target_id -> EwoksPythonActor or InputMergeActor
        self._targetactors = dict()

        self._threadcounter = ThreadCounter(parent=self)

        self._start_actor = StartActor(name="Start", **self._actor_arguments)
        self._stop_actor = StopActor(name="Stop", **self._actor_arguments)

        self._error_actor = ErrorHandler(name="Stop on error", **self._actor_arguments)
        self._connect_actors(self._error_actor, self._stop_actor)

    @property
    def _actor_arguments(self):
        return {"parent": self, "thread_counter": self._threadcounter}

    def graph_to_actors(self, taskgraph: TaskGraph):
        self._clean_workflow()
        self._create_task_actors(taskgraph)
        self._compile_source_actors(taskgraph)
        self._compile_target_actors(taskgraph)
        self._connect_start_actor(taskgraph)
        self._connect_stop_actor(taskgraph)
        self._connect_sources_to_targets(taskgraph)

    def _connect_actors(self, source_actor, target_actor, on_error=False, **kw):
        on_error |= isinstance(target_actor, ErrorHandler)
        if on_error:
            source_actor.connectOnError(target_actor, **kw)
        else:
            source_actor.connect(target_actor, **kw)
        if isinstance(target_actor, JoinActor):
            target_actor.increaseNumberOfThreads()

    def _create_task_actors(self, taskgraph: TaskGraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        error_actor = self._error_actor
        imported = set()
        for node_id, node_attrs in taskgraph.graph.nodes.items():
            if self._pre_import:
                # Pre-import to speedup execution
                name, importfunc = task_executable(node_id, node_attrs)
                if name not in imported:
                    imported.add(name)
                    if importfunc:
                        importfunc(name)

            node_label = get_node_label(node_id, node_attrs)
            actor = EwoksPythonActor(
                node_label,
                node_attrs,
                script=ppfrunscript.__name__ + ".dummy",
                **self._actor_arguments,
            )
            if not analysis.node_has_successors(
                taskgraph.graph, node_id, link_has_on_error=True
            ):
                self._connect_actors(actor, error_actor)
            taskactors[node_id] = actor

    def _create_conditional_actor(
        self,
        source_actor,
        source_id: NodeIdType,
        target_id: NodeIdType,
        taskgraph: TaskGraph,
        conditions: dict,
        all_conditions: dict,
        conditions_else_value,
    ) -> ConditionalActor:
        source_is_ppfmethod = is_ppfmethod(source_id, taskgraph.graph.nodes[source_id])
        source_label = ppfname(source_id)
        target_label = ppfname(target_id)
        name = f"Conditional actor between '{source_label}' and '{target_label}'"
        actor = ConditionalActor(
            conditions,
            all_conditions,
            conditions_else_value,
            is_ppfmethod=source_is_ppfmethod,
            name=name,
            **self._actor_arguments,
        )
        self._connect_actors(source_actor, actor)
        return actor

    def _compile_source_actors(self, taskgraph: TaskGraph):
        """Compile a dictionary NameMapperActor instances for each link.
        These actors will serve as the source actor of each link.
        """
        # source_id -> target_id -> NameMapperActor
        sourceactors = self._sourceactors
        for source_id in taskgraph.graph.nodes:
            sourceactors[source_id] = dict()
            for target_id in taskgraph.graph.successors(source_id):
                actor = self._create_source_actor(taskgraph, source_id, target_id)
                sourceactors[source_id][target_id] = actor

    def _create_source_actor(
        self, taskgraph: TaskGraph, source_id: NodeIdType, target_id: NodeIdType
    ) -> NameMapperActor:
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors

        link_attrs = taskgraph.graph[source_id][target_id]
        conditions = link_attrs.get("conditions", None)
        on_error = link_attrs.get("on_error", False)
        if on_error:
            return self._create_source_on_error_actor(taskgraph, source_id, target_id)

        # EwoksTaskActor
        source_actor = taskactors[source_id]
        if conditions:
            conditions = {c["source_output"]: c["value"] for c in conditions}
            all_conditions = analysis.node_condition_values(taskgraph.graph, source_id)
            conditions_else_value = taskgraph.graph.nodes[source_id].get(
                "conditions_else_value", None
            )

            # ConditionalActor
            source_actor = self._create_conditional_actor(
                source_actor,
                source_id,
                target_id,
                taskgraph,
                conditions,
                all_conditions,
                conditions_else_value,
            )

        # The final actor of this link does the name mapping
        final_source = self._create_name_mapper(taskgraph, source_id, target_id)
        self._connect_actors(source_actor, final_source)

        return final_source

    def _create_source_on_error_actor(
        self, taskgraph: TaskGraph, source_id: NodeIdType, target_id: NodeIdType
    ) -> NameMapperActor:
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors

        link_attrs = taskgraph.graph[source_id][target_id]
        if not link_attrs.get("on_error", False):
            raise ValueError("The link does not have on_error=True")

        # EwoksTaskActor
        source_actor = taskactors[source_id]
        # NameMapperActor
        final_source = self._create_name_mapper(taskgraph, source_id, target_id)
        self._connect_actors(source_actor, final_source, on_error=True)

        return final_source

    def _create_name_mapper(
        self, taskgraph: TaskGraph, source_id: NodeIdType, target_id: NodeIdType
    ) -> NameMapperActor:
        link_attrs = taskgraph.graph[source_id][target_id]
        map_all_data = link_attrs.get("map_all_data", False)
        data_mapping = link_attrs.get("data_mapping", list())
        data_mapping = {
            item["target_input"]: item["source_output"] for item in data_mapping
        }
        on_error = link_attrs.get("on_error", False)
        required = analysis.link_is_required(taskgraph.graph, source_id, target_id)
        source_label = ppfname(source_id)
        target_label = ppfname(target_id)
        if on_error:
            name = f"Name mapper <{source_label} -only on error- {target_label}>"
        else:
            name = f"Name mapper <{source_label} - {target_label}>"
        return NameMapperActor(
            name=name,
            namemap=data_mapping,
            map_all_data=map_all_data,
            trigger_on_error=on_error,
            required=required,
            **self._actor_arguments,
        )

    def _compile_target_actors(self, taskgraph: TaskGraph):
        """Compile a dictionary of InputMergeActor actors for each node
        with predecessors. The actors will serve as the destination of
        each link.
        """
        # target_id -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        for target_id in taskgraph.graph.nodes:
            predecessors = list(analysis.node_predecessors(taskgraph.graph, target_id))
            npredecessors = len(predecessors)
            if npredecessors == 0:
                targetactor = None
            else:
                # InputMergeActor
                targetactor = InputMergeActor(
                    name=f"Input merger of '{taskactors[target_id].name}'",
                    **self._actor_arguments,
                )
                self._connect_actors(targetactor, taskactors[target_id])
            targetactors[target_id] = targetactor

    def _connect_sources_to_targets(self, taskgraph: TaskGraph):
        # source_id -> target_id -> NameMapperActor
        sourceactors = self._sourceactors
        # target_id -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        for source_id, sources in sourceactors.items():
            for target_id, source_actor in sources.items():
                target_actor = targetactors[target_id]
                self._connect_actors(source_actor, target_actor)

    def _connect_start_actor(self, taskgraph: TaskGraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        # target_id -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        start_actor = self._start_actor
        has_start_node = False
        for target_id in analysis.start_nodes(taskgraph.graph):
            has_start_node = True
            target_actor = targetactors.get(target_id)
            if target_actor is None:
                target_actor = taskactors[target_id]
            self._connect_actors(start_actor, target_actor)
        if not has_start_node and taskgraph.graph.nodes:
            raise RuntimeError(f"{taskgraph} has no start node")

    def _connect_stop_actor(self, taskgraph: TaskGraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        stop_actor = self._stop_actor
        has_end_node = False
        for source_id in analysis.end_nodes(taskgraph.graph):
            has_end_node = True
            source_actor = taskactors[source_id]
            self._connect_actors(source_actor, stop_actor)
        if not has_end_node and taskgraph.graph.nodes:
            raise RuntimeError(f"{taskgraph} has no end node")

    @contextmanager
    def _run_context(
        self,
        varinfo: Optional[dict] = None,
        execinfo: Optional[dict] = None,
        task_options: Optional[dict] = None,
        max_workers: Optional[int] = None,
        scaling_workers: bool = True,
        pool_type: Optional[str] = None,
        **pool_options,
    ) -> Generator[None, None, None]:
        self.startargs[ppfrunscript.INFOKEY]["varinfo"] = varinfo
        self.startargs[ppfrunscript.INFOKEY]["task_options"] = task_options
        graph = self.__ewoksgraph.graph
        with events.workflow_context(execinfo, workflow=graph) as execinfo:
            self.startargs[ppfrunscript.INFOKEY]["execinfo"] = execinfo
            with super()._run_context(
                max_workers=max_workers,
                scaling_workers=scaling_workers,
                pool_type=pool_type,
                **pool_options,
            ):
                yield

    def run(
        self,
        startargs: Optional[dict] = None,
        raise_on_error: Optional[bool] = True,
        outputs: Optional[List[dict]] = None,
        merge_outputs: Optional[bool] = True,
        timeout: Optional[float] = None,
        varinfo: Optional[dict] = None,
        execinfo: Optional[dict] = None,
        task_options: Optional[dict] = None,
        max_workers: Optional[int] = None,
        scaling_workers: bool = True,
        pool_type: Optional[str] = None,
        **pool_options,
    ) -> dict:
        if outputs is None:
            outputs = [{"all": False}]
            # TODO: pypushflow returns the values of the last task that was
            # executed, not all end nodes as is expected here
        if outputs and (outputs != [{"all": False}] or not merge_outputs):
            raise ValueError(
                "the Pypushflow engine can only return the merged results of end tasks"
            )
        self._stop_actor.reset()
        with self._run_context(
            varinfo=varinfo,
            execinfo=execinfo,
            task_options=task_options,
            max_workers=max_workers,
            scaling_workers=scaling_workers,
            pool_type=pool_type,
            **pool_options,
        ):
            startindata = dict(self.startargs)
            if startargs:
                startindata.update(startargs)

            self._start_actor.trigger(startindata)
            self._stop_actor.join(timeout=timeout)
            result = self._stop_actor.outData
            if result is None:
                return dict()
            result = self.__parse_result(result)
            ex = result.get("WorkflowExceptionInstance")
            if ex is not None and raise_on_error:
                raise ex
            if outputs:
                return result
            return dict()

    def __parse_result(self, result) -> dict:
        varinfo = varinfo_from_indata(self.startargs)
        return {
            name: value_from_transfer(value, varinfo=varinfo)
            for name, value in result.items()
            if name is not ppfrunscript.INFOKEY
        }


@execute_graph_decorator(engine="ppf")
def execute_graph(
    graph,
    inputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    pre_import: Optional[bool] = None,
    stop_on_signals: bool = False,
    forced_interruption: bool = False,
    stop_signals: Optional[Sequence] = None,
    db_options: Optional[dict] = None,
    startargs: Optional[dict] = None,
    raise_on_error: Optional[bool] = True,
    outputs: Optional[List[dict]] = None,
    merge_outputs: Optional[bool] = True,
    timeout: Optional[float] = None,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    task_options: Optional[dict] = None,
    max_workers: Optional[int] = None,
    scaling_workers: bool = True,
    pool_type: Optional[str] = None,
    pool_options: Optional[dict] = None,
    **deprecated_pool_options,
) -> dict:
    if load_options is None:
        load_options = dict()
    ewoksgraph = load_graph(graph, inputs=inputs, **load_options)

    _besdb_request_id(db_options=db_options, execinfo=execinfo)

    if deprecated_pool_options:
        warnings.warn(
            f"Provide pool options with the argument `pool_options = {deprecated_pool_options}`",
            DeprecationWarning,
            stacklevel=2,
        )
        if pool_options is None:
            pool_options = deprecated_pool_options
        else:
            pool_options = {**deprecated_pool_options, **pool_options}
    elif pool_options is None:
        pool_options = dict()

    ppfgraph = EwoksWorkflow(
        ewoksgraph,
        pre_import=pre_import,
        stop_on_signals=stop_on_signals,
        forced_interruption=forced_interruption,
        stop_signals=stop_signals,
        db_options=db_options,
    )
    return ppfgraph.run(
        startargs=startargs,
        raise_on_error=raise_on_error,
        outputs=outputs,
        merge_outputs=merge_outputs,
        timeout=timeout,
        varinfo=varinfo,
        execinfo=execinfo,
        task_options=task_options,
        max_workers=max_workers,
        scaling_workers=scaling_workers,
        pool_type=pool_type,
        **pool_options,
    )


def _besdb_request_id(
    db_options: Optional[dict] = None, execinfo: Optional[dict] = None
) -> None:
    """Set the BESDB request ID to the Ewoks job ID when needed."""
    if db_options is None:
        db_options = dict()

    db_type = db_options.get("db_type")
    if db_type is None:
        # We are still using the deprecated PYPUSHFLOW_* environment variables.

        if not os.environ.get("PYPUSHFLOW_MONGOURL", None):
            return

        # pypushflow assumes db_type = "besdb" when PYPUSHFLOW_MONGOURL is defined.
        # pypushflow needs PYPUSHFLOW_OBJECTID to be defined. All the others have defaults.

        if os.environ.get("PYPUSHFLOW_OBJECTID", None):
            return

        if not execinfo:
            return

        job_id = execinfo.get("job_id", None)
        if not job_id:
            return

        # We do have an Ewoks job ID so use it for PYPUSHFLOW_OBJECTID.

        os.environ["PYPUSHFLOW_OBJECTID"] = str(job_id)
    elif db_type == "besdb":
        # pypushflow needs db_options["request_id"] to be defined
        if db_options.get("request_id"):
            return

        if not execinfo:
            return

        job_id = execinfo.get("job_id", None)
        if not job_id:
            return

        # We do have an Ewoks job ID so use it for db_options["request_id"].

        db_options["request_id"] = str(job_id)
