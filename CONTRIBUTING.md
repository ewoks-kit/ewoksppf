# Contribution guide

You can find the common Python package contribution guide [here](https://github.com/ewoks-kit/.github/blob/main/shared/CONTRIBUTING.md).

## Scheduler threads

The pypushflow workflow engine allows for parallel execution. Every link that gets triggered starts
a new *workflow scheduler thread*. These are conceptual threads not related to system threads.

The *trigger* method of each pypushflow actor is wrapped with a *thread context*. This means at the start
of a *trigger* call, a scheduler thread starts and at the end (failure or not) this scheduler thread ends.

## Pypushflow logs

Pypushflow has lots of logs for debugging. As a result finding to correct logs for your problem can be hard.

There are three types of log messages

- logs on the creation of the pypushflow actor graph at the start of workflow execution
- actors logs: ``trigger with iData = ...``, ``started`` and ``finished``
- scheduler thread logs: `Thread started` and `Thread ended`

If you do not need to see the data passed between tasks, you can filter the logs on the Ewoks graph ``id``.

For example when

```python
{"graph": {"id": "workflow"}, ...}
```

the pypushflow logs can be filtered like this

```bash
pytest src/ewoksppf/tests/test_ppf_workflow25.py::test_ppf_workflow25_metric2 -xvs \
  --log-cli-level=DEBUG \
  --log-cli-format="%(asctime)s.%(msecs)03d %(message)s" \
  --log-cli-date-format="%H:%M:%S" \
  | grep "\[workflow\]"
```
