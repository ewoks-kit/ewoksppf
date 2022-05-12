import pytest
from ewokscore import load_graph
from ewoksppf import execute_graph
from ewokscore.tests.examples.graphs import graph_names
from ewokscore.tests.examples.graphs import get_graph
from ewokscore.tests.utils.results import assert_execute_graph_default_result


@pytest.mark.parametrize("graph_name", graph_names())
@pytest.mark.parametrize("scheme", (None, "json"))
def test_execute_graph(graph_name, scheme, ppf_log_config, tmpdir):
    graph, expected = get_graph(graph_name)
    if scheme:
        varinfo = {"root_uri": str(tmpdir), "scheme": scheme}
    else:
        varinfo = None
    ewoksgraph = load_graph(graph)
    result = execute_graph(graph, varinfo=varinfo, timeout=10)
    assert_execute_graph_default_result(ewoksgraph, result, expected, varinfo)
