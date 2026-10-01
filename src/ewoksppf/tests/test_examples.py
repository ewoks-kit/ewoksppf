import pytest
from ewokscore import load_graph
from ewokscore.tests.examples.graphs import get_graph
from ewokscore.tests.examples.graphs import graph_names
from ewokscore.tests.utils.results import assert_execute_graph_default_result
from pypushflow.concurrent.factory import get_pool
from pypushflow.concurrent.factory import get_pool_types


def _graph_name_param(name):
    if name == "triangle1":
        return pytest.param(
            name,
            marks=pytest.mark.filterwarnings(
                "ignore:Merged workflow results.*are overwritten by actor.*:UserWarning"
            ),
        )
    return name


@pytest.mark.parametrize("graph_name", [_graph_name_param(n) for n in graph_names()])
@pytest.mark.parametrize("scheme", (None, "json"))
@pytest.mark.parametrize("pool_type", get_pool_types())
def test_execute_graph(engine, graph_name, scheme, pool_type, ppf_log_config, tmpdir):
    if graph_name == "self_trigger":
        pytest.skip(
            "Self-triggering workflow execution is inconsistent: https://github.com/ewoks-kit/ewoksppf/issues/16"
        )

    try:
        get_pool(pool_type)
    except ImportError as e:
        pytest.skip(str(e))

    graph, expected = get_graph(graph_name)
    if scheme:
        varinfo = {"root_uri": str(tmpdir), "scheme": scheme}
    else:
        varinfo = None

    ewoksgraph = load_graph(graph)
    result = engine.execute_graph(
        graph, varinfo=varinfo, timeout=10, pool_type=pool_type
    )
    assert_execute_graph_default_result(ewoksgraph, result, expected, varinfo)
