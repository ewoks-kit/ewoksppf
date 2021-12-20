import pytest
from ewokscore import load_graph
from ewoksppf import execute_graph
from ewokscore.tests.examples.graphs import graph_names
from ewokscore.tests.examples.graphs import get_graph
from ewokscore.tests.utils.results import assert_execute_graph_all_tasks
from ewokscore.tests.utils.results import assert_execute_graph_values
from ewokscore.tests.utils.results import filter_expected_results


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
    assert_results(graph, ewoksgraph, result, expected, varinfo)


def assert_results(graph, ewoksgraph, result, expected, varinfo):
    if varinfo:
        scheme = varinfo.get("scheme")
    else:
        scheme = None
    if ewoksgraph.is_cyclic:
        expected = filter_expected_results(
            ewoksgraph, expected, end_only=True, merge=True
        )
        assert_execute_graph_values(result, expected, varinfo)
    elif scheme:
        assert_execute_graph_all_tasks(graph, expected, varinfo=varinfo)
        expected = filter_expected_results(
            ewoksgraph, expected, end_only=True, merge=True
        )
        assert_execute_graph_values(result, expected, varinfo)
    else:
        expected = filter_expected_results(
            ewoksgraph, expected, end_only=True, merge=True
        )
        assert_execute_graph_values(result, expected, varinfo)
