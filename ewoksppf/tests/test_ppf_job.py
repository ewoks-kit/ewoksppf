from ewoksppf import execute_graph
from ewokscore.tests.examples import graphs
from ewokscore.tests.utils import assert_taskgraph_result
from ewokscore.tests.utils import assert_taskgraph_result_output

# Logging makes multiprocessing hangs?
# https://pythonspeed.com/articles/python-multiprocessing/


def test_acyclic_graph1(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.acyclic_graph1()
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)


def test_acyclic_graph2(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.acyclic_graph2()
    execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)


def test_cyclic_graph1(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.cyclic_graph1()
    result = execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result_output(result, expected, varinfo)


def test_cyclic_graph2(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.cyclic_graph2()
    result = execute_graph(graph, varinfo=varinfo)
    assert_taskgraph_result_output(result, expected, varinfo)
