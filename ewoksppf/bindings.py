import sys
import logging

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
from ewokscore.variable import value_from_transfer
from ewokscore.inittask import task_executable
from ewokscore.inittask import get_varinfo
from ewokscore.inittask import task_executable_info
from ewokscore.graph import CONDITIONS_ELSE_VALUE
from ewokscore.subgraph import flatten_node_name

# Scheme: task graph
# Workflow: instance of a task graph
# Actor: task scheduler mechanism (trigger downstream taskactors)
# PythonActor: trigger execution of an method (full qualifier name)
#              in subprocess (python's multiprocessing)


logger = logging.getLogger(__name__)


def varinfo_from_indata(inData):
    varinfo = inData[ppfrunscript.INFOKEY].get("varinfo")
    node_attrs = inData[ppfrunscript.INFOKEY].get("node_attrs", dict())
    return get_varinfo(node_attrs, varinfo=varinfo)


def actor_name(node_name):
    return ":".join(flatten_node_name(node_name))


def is_ppfmethod(node_attrs: dict):
    task_type, _ = task_executable_info(node_attrs)
    return task_type in ("ppfmethod", "ppfport")


def actordata_filter(actorData):
    for key in ["inData", "outData"]:
        data = actorData.get(key, None)
        if data is None:
            continue
        varinfo = varinfo_from_indata(data)
        actorData[key] = {
            k: value_from_transfer(v, varinfo=varinfo)
            for k, v in data.items()
            if k != ppfrunscript.INFOKEY
        }
    return actorData


register_actorinfo_filter(actordata_filter)


class EwoksPythonActor(PythonActor):
    def __init__(self, node_name, node_attrs, **kw):
        self.node_name = node_name
        self.node_attrs = node_attrs
        kw["name"] = actor_name(node_name)
        super().__init__(**kw)

    def trigger(self, inData):
        """
        :param dict inData: output from the previous task
        """
        infokey = ppfrunscript.INFOKEY
        inData[infokey] = dict(inData[infokey])
        inData[infokey]["node_name"] = self.node_name
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
            value = inData["ppfdict"]
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
        if value in self.dictValues:
            return value
        else:
            return CONDITIONS_ELSE_VALUE

    def trigger(self, inData):
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
            logger.exception(e)
            raise


class InputMergeActor(AbstractActor):
    """Requires triggers from some input actors before triggering
    the downstream actors.

    It remembers the last input from the required uptstream actors.
    Only the last non-required input is remembered.
    """

    def __init__(self, parent=None, name="Input merger", **kw):
        super().__init__(parent=parent, name=name, **kw)
        self.requiredDownStreamActor = list()
        self.startInData = list()
        self.requiredInData = list()
        self.nonrequiredInData = dict()

    def _required_actor(self, actor):
        if actor.required:
            self.requiredDownStreamActor.append(actor)
            self.requiredInData.append(None)

    def trigger(self, inData, source=None):
        self.setStarted()
        self.setFinished()
        if source is None:
            self.startInData.append(inData)
        else:
            try:
                i = self.requiredDownStreamActor.index(source)
            except ValueError:
                self.nonrequiredInData = inData
            else:
                self.requiredInData[i] = inData
        if None in self.requiredInData:
            return
        newInData = dict()
        for data in self.startInData:
            newInData.update(data)
        for data in self.requiredInData:
            newInData.update(data)
        newInData.update(self.nonrequiredInData)
        for actor in self.listDownStreamActor:
            actor.trigger(newInData)


class EwoksWorkflow(Workflow):
    def __init__(self, ewoksgraph, varinfo=None, enable_logging=False):
        name = repr(ewoksgraph)
        super().__init__(name)

        # When triggering a task, the output dict of the previous task
        # is merged with the input dict of the current task.
        if varinfo is None:
            varinfo = dict()
        self.startargs = {
            ppfrunscript.INFOKEY: {"varinfo": varinfo, "enable_logging": enable_logging}
        }
        self.graph_to_actors(ewoksgraph, varinfo)

    def _clean_workflow(self):
        # task_name -> EwoksPythonActor
        self._taskactors = dict()
        self.listActorRef = list()  # values of taskactors

        # source_name -> condition_name -> DecodeRouterActor
        self._routeractors = dict()

        # source_name -> target_name -> NameMapperActor
        self._sourceactors = dict()

        # target_name -> EwoksPythonActor or InputMergeActor
        self._targetactors = dict()

        self._threadcounter = ThreadCounter()

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
        logger.debug(msg)

    def _create_task_actors(self, taskgraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        error_actor = self._error_actor
        imported = set()
        for node_name, node_attrs in taskgraph.graph.nodes.items():
            # Pre-import to speedup execution
            name, importfunc = task_executable(node_attrs, node_name=node_name)
            if name not in imported:
                imported.add(name)
                if importfunc:
                    importfunc(name)

            actor = EwoksPythonActor(
                node_name,
                node_attrs,
                script=ppfrunscript.__name__ + ".dummy",
                **self._actor_arguments,
            )
            if not taskgraph.has_successors(node_name, on_error=True):
                self._connect_actors(actor, error_actor)
            taskactors[node_name] = actor
            self.addActorRef(actor)

    def _create_router_actors(self, taskgraph):
        """Insert router actors (one per target and output name) behind
        actors with conditions.
        """
        # source_name -> condition_name -> DecodeRouterActor
        routeractors = self._routeractors
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        for source_name in taskgraph.graph.nodes:
            # We will get 1 router for each output variable
            routers = routeractors[source_name] = dict()
            source_actor = taskactors[source_name]
            for target_name in taskgraph.successors(source_name):
                link_attrs = taskgraph.graph[source_name][target_name]
                conditions = link_attrs.get("conditions", list())
                for item in conditions:
                    outname = item["source_output"]
                    outvalue = item["value"]
                    router = routers.get(outname)
                    if router is None:
                        router = self._create_router_actor(
                            source_actor,
                            source_name,
                            outname,
                            taskgraph,
                        )
                        routers[outname] = router
                    if outvalue not in router.listPort:
                        router.listPort.append(outvalue)

    def _create_router_actor(self, source_actor, source_name, outname, taskgraph):
        """
        :returns DecodeRouterActor:
        """
        source_attrs = taskgraph.graph.nodes[source_name]
        routername = f"Route output {repr(outname)} of {actor_name(source_name)}"
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
        # source_name -> target_name -> NameMapperActor
        sourceactors = self._sourceactors
        for source_name in taskgraph.graph.nodes:
            sourceactors[source_name] = dict()
            for target_name in taskgraph.graph.successors(source_name):
                actor = self._create_source_actor(taskgraph, source_name, target_name)
                sourceactors[source_name][target_name] = actor

    def _create_source_actor(
        self, taskgraph, source_name, target_name
    ) -> NameMapperActor:
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        # source_name -> condition_name -> DecodeRouterActor
        routeractors = self._routeractors

        link_attrs = taskgraph.graph[source_name][target_name]
        conditions = link_attrs.get("conditions", list())
        on_error = link_attrs.get("on_error", False)
        if on_error:
            return self._create_source_on_error_actor(
                taskgraph, source_name, target_name
            )
        if conditions:
            conditions = {item["source_output"]: item["value"] for item in conditions}

        # One router actor for each output name
        routers = dict()
        for outname in conditions:
            routers[outname] = routeractors[source_name][outname]

        # Merge routers into one single source actor
        connectkw = dict()
        nrouters = len(routers)
        if nrouters == 0:
            # EwoksTaskActor
            source_actor = taskactors[source_name]
        elif nrouters == 1:
            # DecodeRouterActor
            for outname, router_actor in routers.items():
                value = conditions[outname]
                source_actor = router_actor
                connectkw["expectedValue"] = value
        else:
            # JoinActor
            name = f"Join routers {source_name} -> {target_name}"
            source_actor = JoinActor(name=name, **self._actor_arguments)
            for outname, router_actor in routers.items():
                value = conditions[outname]
                self._connect_actors(router_actor, source_actor, expectedValue=value)

        # The final actor of this link does the name mapping
        final_source = self._create_name_mapper(taskgraph, source_name, target_name)
        self._connect_actors(source_actor, final_source, **connectkw)

        return final_source

    def _create_source_on_error_actor(
        self, taskgraph, source_name, target_name
    ) -> NameMapperActor:
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors

        link_attrs = taskgraph.graph[source_name][target_name]
        if not link_attrs.get("on_error", False):
            raise ValueError("The link does not have on_error=True")

        # EwoksTaskActor
        source_actor = taskactors[source_name]
        # NameMapperActor
        final_source = self._create_name_mapper(taskgraph, source_name, target_name)
        self._connect_actors(source_actor, final_source, on_error=True)

        return final_source

    def _create_name_mapper(
        self, taskgraph, source_name, target_name
    ) -> NameMapperActor:
        link_attrs = taskgraph.graph[source_name][target_name]
        map_all_data = link_attrs.get("map_all_data", False)
        data_mapping = link_attrs.get("data_mapping", list())
        data_mapping = {
            item["target_input"]: item["source_output"] for item in data_mapping
        }
        on_error = link_attrs.get("on_error", False)
        required = taskgraph.link_is_required(source_name, target_name)

        source_name = actor_name(source_name)
        target_name = actor_name(target_name)
        if on_error:
            name = f"Name mapper <{source_name} -only on error- {target_name}>"
        else:
            name = f"Name mapper <{source_name} - {target_name}>"
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
        # target_name -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        for target_name in taskgraph.graph.nodes:
            predecessors = list(taskgraph.predecessors(target_name))
            npredecessors = len(predecessors)
            if npredecessors == 0:
                targetactor = None
            else:
                # InputMergeActor
                targetactor = InputMergeActor(
                    name=f"Input merger of {taskactors[target_name].name}",
                    **self._actor_arguments,
                )
                self._connect_actors(targetactor, taskactors[target_name])
            targetactors[target_name] = targetactor

    def _connect_sources_to_targets(self, taskgraph):
        # source_name -> target_name -> NameMapperActor
        sourceactors = self._sourceactors
        # target_name -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        for source_name, sources in sourceactors.items():
            for target_name, source_actor in sources.items():
                target_actor = targetactors[target_name]
                self._connect_actors(source_actor, target_actor)

    def _connect_start_actor(self, taskgraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        # target_name -> EwoksPythonActor or InputMergeActor
        targetactors = self._targetactors
        start_actor = self._start_actor
        for target_name in taskgraph.start_nodes():
            target_actor = targetactors.get(target_name)
            if target_actor is None:
                target_actor = taskactors[target_name]
            self._connect_actors(start_actor, target_actor)

    def _connect_stop_actor(self, taskgraph):
        # task_name -> EwoksPythonActor
        taskactors = self._taskactors
        stop_actor = self._stop_actor
        for source_name in taskgraph.end_nodes():
            source_actor = taskactors[source_name]
            self._connect_actors(source_actor, stop_actor)

    def run(self, inputs=None, raise_on_error=True, timeout=None):
        startargs = dict(self.startargs)
        if inputs:
            startargs.update(inputs)
        self._start_actor.trigger(startargs)
        self._stop_actor.join(timeout=timeout)
        result = self._stop_actor.outData
        if result is None:
            return None
        result = self.__parse_result(result)
        ex = result.get("WorkflowException")
        if ex is None or not raise_on_error:
            return result
        else:
            info = result.get(ppfrunscript.INFOKEY, dict())
            print("\n".join(ex["traceBack"]), file=sys.stderr)
            node_name = info.get("node_name")
            err_msg = f"Task {node_name} failed"
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
    representation=None,
    varinfo=None,
    inputs=None,
    raise_on_error=True,
    timeout=None,
    log_task_execution=False,
    **load_options,
):
    ewoksgraph = load_graph(source=graph, representation=representation, **load_options)
    ppfgraph = EwoksWorkflow(
        ewoksgraph, varinfo=varinfo, enable_logging=log_task_execution
    )
    return ppfgraph.run(inputs=inputs, raise_on_error=raise_on_error, timeout=timeout)
