from ewoksppf import job
from ewokscore.tests.examples import graphs
from ewokscore.tests.utils import assert_taskgraph_result
from ewokscore.tests.utils import assert_taskgraph_result_output

# Logging makes multiprocessing hangs?
# https://pythonspeed.com/articles/python-multiprocessing/


def test_acyclic_job1(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.acyclic_graph1()
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)


def test_acyclic_job2(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.acyclic_graph2()
    job(graph, varinfo=varinfo)
    assert_taskgraph_result(graph, expected, varinfo)


def test_cyclic_job1(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.cyclic_graph1()
    result = job(graph, varinfo=varinfo)
    assert_taskgraph_result_output(result, expected, varinfo)


def test_cyclic_job2(ppf_logging, tmpdir):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.cyclic_graph2()
    result = job(graph, varinfo=varinfo)
    assert_taskgraph_result_output(result, expected, varinfo)
