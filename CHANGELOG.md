# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2025-07-25

### Added

- Add `ewoks.engines` entry point and implement the `WorkflowEngine` interface.

## [1.3.0] - 2025-05-21

### Changed

- Raise error when the workflow does not have a start or end node.

## [1.2.0] - 2025-02-14

### Changed

- Set `db_options["request_id"]` to the Ewoks job id when missing.

## [1.1.0] - 2025-02-13

### Added

- Set deprecated environment variable `PYPUSHFLOW_OBJECTID` to the Ewoks job id when needed.

### Changed

- Drop support for Python 3.6 and 3.7.

## [1.0.0] - 2024-12-25

## [0.4.0] - 2024-11-16

### Added

- Add `db_options` to `execute_graph` so we can avoid environment variables for pypushflow.

## [0.3.0] - 2024-11-08

### Added

- Add `task_options` to `execute_graph`.

## [0.2.2] - 2024-09-17

### Fixed

- Support ewokscore 0.8.1.

## [0.2.1] - 2024-06-22

### Fixed

- Support pip 24.1.

## [0.2.0] - 2023-09-30

### Changed

- Stop merging task inputs and outputs to trigger the next task.

## [0.1.7] - 2023-09-27

### Changed

- Use workflow and node labels with id fallback for pypushflow logging.

## [0.1.6] - 2023-09-09

### Fixed

- Remove info key from workflow outputs.

## [0.1.5] - 2023-09-07

### Changed

- Re-raise pypushflow exceptions by default.

## [0.1.4] - 2023-05-15

### Changed

- Remove deprecated ewokscore Task properties.

## [0.1.3] - 2023-03-29

### Fixed

- Fix "outputs" argument default of execute_graph.

## [0.1.2] - 2023-03-28

### Fixed

- Output of execute_graph was not consistent with other bindings.

## [0.1.1] - 2023-03-09

### Changed

- Use new "engine" argument instead of the deprecated "binding".

## [0.1.0] - 2022-12-02

### Added

- Convert Ewoks `Graph` to graph of actors for exection.

[unreleased]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v2.0.0...HEAD
[2.0.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v1.3.0...v2.0.0
[1.3.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v1.2.0...v1.3.0
[1.2.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v1.1.0...v1.2.0
[1.1.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v1.0.0...v1.1.0
[1.0.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.4.0...v1.0.0
[0.4.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.3.0...v0.4.0
[0.3.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.2.2...v0.3.0
[0.2.2]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.2.1...v0.2.2
[0.2.1]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.2.0...v0.2.1
[0.2.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.1.7...v0.2.0
[0.1.7]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.1.6...v0.1.7
[0.1.6]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.1.5...v0.1.6
[0.1.5]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.1.4...v0.1.5
[0.1.4]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.1.3...v0.1.4
[0.1.3]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.1.2...v0.1.3
[0.1.2]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.1.1...v0.1.2
[0.1.1]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/compare/v0.1.0...v0.1.1
[0.1.0]: https://gitlab.esrf.fr/workflow/ewoks/ewoksppf/-/tags/v0.1.0
