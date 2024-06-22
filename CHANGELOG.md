# CHANGELOG.md

## (unreleased)

## 0.2.1

Bug fixes:

- support pip 24.1

## 0.2.0

Changes:

- stop merging task inputs and outputs to trigger the next task

## 0.1.7

Changes:

- use workflow and node labels with id fallback for pypushflow logging

## 0.1.6

Bug fixes:

- remove info key from workflow outputs

## 0.1.5

Changes:

- re-raise pypushflow exceptions by default

## 0.1.4

Changes:

- remove deprecated ewokscore Task properties

## 0.1.3

Bug fixes:

- fix "outputs" argument default of execute_graph

## 0.1.2

Bug fixes:

- output of execute_graph was not consistent with other bindings

## 0.1.1

Changes:

- use new "engine" argument instead of the deprecated "binding"

## 0.1.0

New features:

- Convert Ewoks `Graph` to graph of actors for exection
