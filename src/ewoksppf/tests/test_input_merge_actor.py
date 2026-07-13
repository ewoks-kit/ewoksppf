import threading

from pypushflow.AbstractActor import AbstractActor
from pypushflow.ThreadCounter import ThreadCounter

from ..bindings import InputMergeActor


def test_input_merge_actor_reentrant_trigger():
    """
    Deterministic counterpart to test_ppf_workflow26's real
    (but timing-dependent) graph reproduction of the same bug.
    """
    thread_counter = ThreadCounter()
    merger = InputMergeActor(thread_counter=thread_counter, name="merger")
    looping_actor = _SelfLoopingActor(merger, thread_counter)
    merger.connect(looping_actor)

    thread = threading.Thread(target=merger.trigger, args=({},), daemon=True)
    thread.start()
    thread.join(timeout=5)

    assert not thread.is_alive(), "InputMergeActor deadlocked on a reentrant trigger"
    assert looping_actor.triggered == 2
    assert thread_counter.nthreads == 0


class _SelfLoopingActor(AbstractActor):
    def __init__(self, merger: InputMergeActor, thread_counter: ThreadCounter):
        super().__init__(thread_counter=thread_counter, name="looping actor")
        self.merger = merger
        self.triggered = 0

    def _execute(self, inData: dict, _scope_id=None) -> None:
        self.triggered += 1
        if self.triggered == 1:
            # call InputMergeActor in the current thread
            self.merger.trigger(inData)
