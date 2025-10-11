ewoksppf |version|
==================

*ewoksppf* provides task scheduling for cyclic `ewoks <https://ewoks.readthedocs.io/>`_ workflows.

*ewoksppf* has been developed by the `Software group <http://www.esrf.fr/Instrumentation/software>`_ of the `European Synchrotron <https://www.esrf.fr/>`_.

Getting started
---------------

Install requirements

.. code-block:: bash

    pip install ewoksppf

Execute a workflow

.. code-block:: python

    from ewoksppf import execute_graph

    result = execute_graph("/path/to/graph.json")

Run the tests

.. code-block:: bash

    pip install ewoksppf[test]
    pytest --pyargs ewoksppf.tests

.. toctree::
    :hidden:

    parallel
    actors
    reference/index
