Parallel Execution
==================

Ewoks workflows can be executed in parallel using various concurrency backends.
Parallel execution options are configured when calling :func:`execute_graph`.

.. code-block:: python

    from ewoksppf import execute_graph

    result = execute_graph(
        "/path/to/graph.json",
        pool_type=...,          # Select the concurrency backend
        scaling_workers=...,    # Enable or disable worker scaling
        max_workers=...,        # Maximum number of workers (when not scaling)
        context=...             # Process start method ("spawn" or "fork")
    )

Options
-------

**pool_type**
    Specifies the type of worker pool to use:

    * ``"thread"`` — Use system threads (``concurrent.futures.ThreadPoolExecutor``).
    * ``"process"`` *(default)* — Use standard process pools (``concurrent.futures.ProcessPoolExecutor``).
    * ``"ndprocess"`` — Use **non-daemonic** process pools with ``concurrent.futures``.
      Allows Ewoks tasks to spawn their own subprocesses.
    * ``"multiprocessing"`` — Use process pools from the built-in ``multiprocessing`` module.
    * ``"ndmultiprocessing"`` — Use **non-daemonic** process pools with ``multiprocessing``.
      Allows Ewoks tasks to create subprocesses.
    * ``"billiard"`` — Use **non-daemonic** process pools from the `billiard <https://billiard.readthedocs.io/>`_ library.
      Enables safe subprocess creation in Ewoks tasks.
    * ``"gevent"`` *(default when gevent is installed)* — Use cooperative green threads.

**scaling_workers**
    Whether to dynamically scale the number of worker processes or threads.

    * ``True`` *(default)* — The pool scales automatically based on workload.
    * ``False`` — A fixed number of workers is used.

**max_workers**
    The maximum number of worker processes or threads.
    Only applies when ``scaling_workers=False``.

**context**
    Process start method for multiprocessing backends.
    Accepts ``"spawn"`` or ``"fork"``.

Daemonic vs. Non-daemonic Processes
-----------------------------------

When using process-based pools, it's important to understand the difference between *daemonic* and *non-daemonic* processes:

**Daemonic processes:**
    * Terminate automatically when the parent process exits.
    * Cannot create their own child processes.

**Non-daemonic processes:**
    * Run independently of their parent process.
    * Continue executing even if the parent exits (until they complete).
    * Can create their own child processes.

Non-daemonic processes are required when Ewoks tasks need to spawn additional subprocesses.
