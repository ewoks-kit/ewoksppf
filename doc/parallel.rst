# Parallel execution

Options for parallel execution can be provided when executing a workflow

.. code:: python

    from ewoksppf import execute_graph

    result = execute_graph("/path/to/graph.json", pool_type=..., scaling_workers=..., max_workers=...)

The options are

  * `pool_type`: _thread_, _process_ (default), _ndprocess_, _multiprocessing_,
                 _ndmultiprocessing_, _billiard_, _gevent_ (default)
  * `scaling_workers`: _True_ (default) or _False_
  * `max_workers`: only applies when _scaling_workers=False_
  * `context`: _spawn_ or _fork_ (only applies when using processes)
