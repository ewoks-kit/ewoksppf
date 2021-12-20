import sys
import pprint
from typing import Optional, List
import numpy

from pypushflow.Workflow import Workflow
from pypushflow.StopActor import StopActor
from pypushflow.StartActor import StartActor
from pypushflow.PythonActor import PythonActor
from pypushflow.JoinActor import JoinActor
from pypushflow.RouterActor import RouterActor
from pypushflow.ErrorHandler import ErrorHandler
from pypushflow.AbstractActor import AbstractActor
from pypushflow.ThreadCounter import ThreadCounter
from pypushflow.persistence import register_actorinfo_filter

from . import ppfrunscript
from ewokscore import load_graph
from ewokscore import ppftasks
from ewokscore.variable import value_from_transfer
from ewokscore.inittask import task_executable
from ewokscore.inittask import get_varinfo
from ewokscore.inittask import task_executable_info
from ewokscore.graph import CONDITIONS_ELSE_VALUE
from ewokscore.node import get_node_label

# Scheme: task graph
# Workflow: instance of a task graph
# Actor: task scheduler mechanism (trigger downstream taskactors)
# PythonActor: trigger execution of an method (full qualifier name)
#              in subprocess (python's multiprocessing)


def varinfo_from_indata(inData) -> Optional[dict]:
    if ppfrunscript.INFOKEY not in inData:
        return None
    varinfo = inData[ppfrunscript.INFOKEY].get("varinfo", None)
    node_attrs = inData[ppfrunscript.INFOKEY].get("node_attrs", dict())
    return get_varinfo(node_attrs, varinfo=varinfo)


def is_ppfmethod(node_attrs: dict) -> bool:
    task_type, _ = task_executable_info(node_attrs)
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
        kw["name"] = get_node_label(node_attrs, node_id=node_id)
        super().__init__(**kw)

    def trigger(self, inData):
        """
        :param dict inData: output from the previous task
        """
        self.logger.info("triggered with inData =\n %s", pprint.pformat(inData))
        infokey = ppfrunscript.INFOKEY
        inData[infokey] = dict(inData[infokey])
        inData[infokey]["node_id"] = self.node_id
        inData[infokey]["node_attrs"] = self.node_attrs
        return super().trigger(inData)


class DecodeRouterActor(RouterActor):
    """For PPF methods, the conditions do not apply to the
    output value (which is a dict) but to the values
    of the dict.
    """

    def __init__(self, is_ppfmethod=False, **kw):
        self.is_ppfmethod = is_ppfmethod
        super().__init__(**kw)

    def _extractValue(self, inData):
        if self.is_ppfmethod:
            value = inData[ppftasks.PPF_DICT_ARGUMENT]
        else:
            if self.itemName in inData:
                value = inData[self.itemName]
            else:
                return CONDITIONS_ELSE_VALUE
        varinfo = varinfo_from_indata(inData)
        value = value_from_transfer(value, varinfo=varinfo)
        if self.is_ppfmethod:
            if self.itemName in value:
                value = value[self.itemName]
            else:
                return CONDITIONS_ELSE_VALUE

        if isinstance(value, numpy.ndarray):
            value = value.item()
        if value in self.dictValues:
            return value
        else:
            return CONDITIONS_ELSE_VALUE

    def trigger(self, inData):
        self.logger.info("triggered with inData =\n %s", pprint.pformat(inData))
        self.setStarted()
        self.setFinished()
        value = self._extractValue(inData)
        actors = self.dictValues.get(value, list())
        for actor in actors:
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
            actor._required_actor(self)

    def trigger(self, inData):
        self.logger.info("triggered with inData =\n %s", pprint.pformat(inData))
        is_error = "WorkflowException" in inData
        if is_error and not self.trigger_on_error:
            return
        try:
            newInData = dict()
            if not is_error:
                # Map output names of this task to input
                # names of the downstream task
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

    def _required_actor(self, actor):
        if actor.required:
            self.requiredInData[actor] = None

    def trigger(self, inData, source=None):
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
                "not triggering downstream actors (missing inputs %s)",
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
    def __init__(self, ewoksgraph, varinfo: Optional[dict] = None):
        name = repr(ewoksgraph)
        super().__init__(name)

        # When triggering a task, the output dict of the previous task
        # is merged with the input dict of the current task.
        if varinfo is None:
            varinfo = dict()
        self.startargs = {ppfrunscript.INFOKEY: {"varinfo": varinfo}}
        self.graph_to_actors(ewoksgraph, varinfo)

    def _clean_workflow(self):
        # task_name -> EwoksPythonActor
        self._taskactors = dict()
        self.listActorRef = list()  # values of taskactors

        # source_id -> condition_name -> DecodeRouterActor
        self._routeractors = dict()

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

    def graph_to_actors(self, taskgraph, varinfo):
        self._clean_workflow()
        self._create_task_actors(taskgraph)
        self._create_router_actors(taskgraph)
        self._compile_source_actors(taskgraph)
        self._compile_target_actors(taskgraph)
        self._connect_start_actor(taskgraph)
        self._connect_stop_actor(taskgraph)
        self._connect_sources_to_targets(taskgraph)

    def _connect_actors(self, source_actor, target_actor, on_error=False, **kw):
        on_error |= isinstance(target_actor, ErrorHandler)
        if on_error:
            source_actor.connectOnError(target_actor, **kw)
            msg = "\nPpf actor connection (on error):\n source ({}): {}\n ->\n target ({}): {}"
        else:
            source_actor.connect(target_actor, **kw)
            msg = "\nPpf actor connection:\n source ({}): {}\n ->\n target ({}): {}"

        if isinstance(target_actor, JoinActor):
            target_actor.increaseNumberOfThreads()
        msg = msg.format(
            type(source_actor).__name__,
            source_actor.name,
            type(target_actor).__name__,
            target_actor.name,
        )

    def _create_task_actors(self, taskgraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        error_actor = self._error_actor
        imported = set()
        for node_id, node_attrs in taskgraph.graph.nodes.items():
            # Pre-import to speedup execution
            name, importfunc = task_executable(node_attrs, node_id=node_id)
            if name not in imported:
                imported.add(name)
                if importfunc:
                    importfunc(name)

            actor = EwoksPythonActor(
                node_id,
                node_attrs,
                script=ppfrunscript.__name__ + ".dummy",
                **self._actor_arguments,
            )
            if not taskgraph.has_successors(node_id, on_error=True):
                self._connect_actors(actor, error_actor)
            taskactors[node_id] = actor
            self.addActorRef(actor)

    def _create_router_actors(self, taskgraph):
        """Insert router actors (one per target and output name) behind
        actors with conditions.
        """
        # source_id -> condition_name -> DecodeRouterActor
        routeractors = self._routeractors
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        for source_id in taskgraph.graph.nodes:
            # We will get 1 router for each output variable
            routers = routeractors[source_id] = dict()
            source_actor = taskactors[source_id]
            for target_id in taskgraph.successors(source_id):
                link_attrs = taskgraph.graph[source_id][target_id]
                conditions = link_attrs.get("conditions", list())
                for item in conditions:
                    outname = item["source_output"]
                    outvalue = item["value"]
                    router = routers.get(outname)
                    if router is None:
                        router = self._create_router_actor(
                            source_actor,
                            source_id,
                            outname,
                            taskgraph,
                        )
                        routers[outname] = router
                    if outvalue not in router.listPort:
                        router.listPort.append(outvalue)

    def _create_router_actor(self, source_actor, source_id, outname, taskgraph):
        """
        :returns DecodeRouterActor:
        """
        source_attrs = taskgraph.graph.nodes[source_id]
        source_label = get_node_label(source_attrs, node_id=source_id)
        routername = f"Route output {repr(outname)} of {source_label}"
        router = DecodeRouterActor(
            name=routername,
            itemName=outname,
            is_ppfmethod=is_ppfmethod(source_attrs),
            **self._actor_arguments,
        )
        self._connect_actors(source_actor, router)
        return router

    def _compile_source_actors(self, taskgraph):
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

    def _create_source_actor(self, taskgraph, source_id, target_id) -> NameMapperActor:
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        # source_id -> condition_name -> DecodeRouterActor
        routeractors = self._routeractors

        link_attrs = taskgraph.graph[source_id][target_id]
        conditions = link_attrs.get("conditions", list())
        on_error = link_attrs.get("on_error", False)
        if on_error:
            return self._create_source_on_error_actor(taskgraph, source_id, target_id)
        if conditions:
            conditions = {item["source_output"]: item["value"] for item in conditions}

        # One router actor for each output name
        routers = dict()
        for outname in conditions:
            routers[outname] = routeractors[source_id][outname]

        # Merge routers into one single source actor
        connectkw = dict()
        nrouters = len(routers)
        if nrouters == 0:
            # EwoksTaskActor
            source_actor = taskactors[source_id]
        elif nrouters == 1:
            # DecodeRouterActor
            for outname, router_actor in routers.items():
                value = conditions[outname]
                source_actor = router_actor
                connectkw["expectedValue"] = value
        else:
            # JoinActor
            source_attrs = taskgraph.graph.nodes[source_id]
            target_attrs = taskgraph.graph.nodes[target_id]
            source_label = get_node_label(source_attrs, node_id=source_id)
            target_label = get_node_label(target_attrs, node_id=target_id)
            name = f"Join routers {source_label} -> {target_label}"
            source_actor = JoinActor(name=name, **self._actor_arguments)
            for outname, router_actor in routers.items():
                value = conditions[outname]
                self._connect_actors(router_actor, source_actor, expectedValue=value)

        # The final actor of this link does the name mapping
        final_source = self._create_name_mapper(taskgraph, source_id, target_id)
        self._connect_actors(source_actor, final_source, **connectkw)

        return final_source

    def _create_source_on_error_actor(
        self, taskgraph, source_id, target_id
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

    def _create_name_mapper(self, taskgraph, source_id, target_id) -> NameMapperActor:
        link_attrs = taskgraph.graph[source_id][target_id]
        map_all_data = link_attrs.get("map_all_data", False)
        data_mapping = link_attrs.get("data_mapping", list())
        data_mapping = {
            item["target_input"]: item["source_output"] for item in data_mapping
        }
        on_error = link_attrs.get("on_error", False)
        required = taskgraph.link_is_required(source_id, target_id)

        source_attrs = taskgraph.graph.nodes[source_id]
        target_attrs = taskgraph.graph.nodes[target_id]
        source_label = get_node_label(source_attrs, node_id=source_id)
        target_label = get_node_label(target_attrs, node_id=target_id)
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

    def _compile_target_actors(self, taskgraph):
        """Compile a dictionary of InputMergeActor actors for each node
        with predecessors. The actors will serve as the destination of
        each link.
        """
        # target_id -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        for target_id in taskgraph.graph.nodes:
            predecessors = list(taskgraph.predecessors(target_id))
            npredecessors = len(predecessors)
            if npredecessors == 0:
                targetactor = None
            else:
                # InputMergeActor
                targetactor = InputMergeActor(
                    name=f"Input merger of {taskactors[target_id].name}",
                    **self._actor_arguments,
                )
                self._connect_actors(targetactor, taskactors[target_id])
            targetactors[target_id] = targetactor

    def _connect_sources_to_targets(self, taskgraph):
        # source_id -> target_id -> NameMapperActor
        sourceactors = self._sourceactors
        # target_id -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        for source_id, sources in sourceactors.items():
            for target_id, source_actor in sources.items():
                target_actor = targetactors[target_id]
                self._connect_actors(source_actor, target_actor)

    def _connect_start_actor(self, taskgraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        # target_id -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        start_actor = self._start_actor
        for target_id in taskgraph.start_nodes():
            target_actor = targetactors.get(target_id)
            if target_actor is None:
                target_actor = taskactors[target_id]
            self._connect_actors(start_actor, target_actor)

    def _connect_stop_actor(self, taskgraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        stop_actor = self._stop_actor
        for source_id in taskgraph.end_nodes():
            source_actor = taskactors[source_id]
            self._connect_actors(source_actor, stop_actor)

    def run(
        self,
        startargs: Optional[dict] = None,
        raise_on_error: Optional[bool] = True,
        results_of_all_nodes: Optional[bool] = False,
        outputs: Optional[List[dict]] = None,
        timeout: Optional[float] = None,
    ):
        startindata = dict(self.startargs)
        if startargs:
            startindata.update(startargs)
        self._start_actor.trigger(startindata)
        self._stop_actor.join(timeout=timeout)
        result = self._stop_actor.outData
        if result is None:
            return None
        info = result.pop(ppfrunscript.INFOKEY, dict())
        result = self.__parse_result(result)
        ex = result.get("WorkflowException")
        if ex is None or not raise_on_error:
            return result
        else:
            print("\n".join(ex["traceBack"]), file=sys.stderr)
            node_id = info.get("node_id")
            err_msg = f"Task {node_id} failed"
            if ex["errorMessage"]:
                err_msg += " ({})".format(ex["errorMessage"])
            raise RuntimeError(err_msg)

    def __parse_result(self, result) -> dict:
        varinfo = varinfo_from_indata(self.startargs)
        return {
            name: value_from_transfer(value, varinfo=varinfo)
            for name, value in result.items()
        }


def execute_graph(
    graph,
    inputs: Optional[dict] = None,
    startargs: Optional[dict] = None,
    varinfo: Optional[dict] = None,
    timeout: Optional[float] = None,
    load_options: Optional[dict] = None,
    **execute_options,
):
    if load_options is None:
        load_options = dict()
    ewoksgraph = load_graph(source=graph, **load_options)
    if inputs:
        ewoksgraph.update_default_inputs(inputs)
    ppfgraph = EwoksWorkflow(ewoksgraph, varinfo=varinfo)
    return ppfgraph.run(startargs=startargs, timeout=timeout, **execute_options)
