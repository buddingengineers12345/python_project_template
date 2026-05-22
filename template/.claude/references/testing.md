# How Tests Work

Tests live in `tests/`. They use pytest to call `copier copy` programmatically,
render the template into a temporary directory, then assert that expected files
exist and contain expected content. When adding a new Copier variable or template
file, add a corresponding test.
