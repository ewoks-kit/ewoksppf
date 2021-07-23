import itertools
import pytest
from ewoksppf import execute_graph
from ewokscore import load_graph
from ewokscore.tests.examples.graphs import graph_names
from ewokscore.tests.examples.graphs import get_graph
from ewokscore.tests.utils import assert_taskgraph_result
from ewokscore.tests.utils import assert_workflow_merged_result

# Logging makes multiprocessing hangs?
# https://pythonspeed.com/articles/python-multiprocessing/


@pytest.mark.parametrize(
    "graph_name,persist", itertools.product(graph_names(), (True, False))
)
def test_execute_graph(graph_name, persist, ppf_logging, tmpdir):
    g, expected = get_graph(graph_name)
    if persist:
        varinfo = {"root_uri": str(tmpdir)}
    else:
        varinfo = None
    ewoksgraph = load_graph(g)
    if ewoksgraph.is_cyclic:
        result = execute_graph(g, varinfo=varinfo)
        assert_workflow_merged_result(result, expected, varinfo)
    else:
        execute_graph(g, varinfo=varinfo)
        if persist:
            assert_taskgraph_result(g, expected, varinfo=varinfo)
        else:
            pytest.skip(
                "The expected result is the output of each task when the binding gives the output of the workflow"
            )
