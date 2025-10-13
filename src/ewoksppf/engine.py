from typing import Any
from typing import List
from typing import Optional
from typing import Sequence

from ewokscore.engine_interface import RawExecInfoType
from ewokscore.engine_interface import WorkflowEngine

from . import bindings


class PpfWorkflowEngine(WorkflowEngine):

    def execute_graph(
        self,
        graph: Any,
        *,
        inputs: Optional[List[dict]] = None,
        load_options: Optional[dict] = None,
        varinfo: Optional[dict] = None,
        execinfo: RawExecInfoType = None,
        task_options: Optional[dict] = None,
        outputs: Optional[List[dict]] = None,
        merge_outputs: Optional[bool] = True,
        # Engine specific:
        pre_import: Optional[bool] = None,
        stop_on_signals: bool = False,
        forced_interruption: bool = False,
        stop_signals: Optional[Sequence] = None,
        db_options: Optional[dict] = None,
        startargs: Optional[dict] = None,
        raise_on_error: Optional[bool] = True,
        timeout: Optional[float] = None,
        pool_type: Optional[str] = None,
        pool_options: Optional[dict] = None,
        max_workers: Optional[int] = None,
        scaling_workers: bool = True,
        **deprecated_pool_options,
    ) -> dict:
        return bindings.execute_graph(
            graph,
            inputs=inputs,
            load_options=load_options,
            pre_import=pre_import,
            stop_on_signals=stop_on_signals,
            forced_interruption=forced_interruption,
            stop_signals=stop_signals,
            db_options=db_options,
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
            pool_options=pool_options,
            **deprecated_pool_options,
        )
