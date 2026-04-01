Generate a test project from this Copier template into a temporary directory and inspect it.

Steps:
1. Run: `copier copy . /tmp/test-output --trust --defaults`
2. List the files and directories created under `/tmp/test-output`
3. Show the contents of the generated `pyproject.toml`
4. Show the contents of the generated `justfile` (if present)
5. Check whether the generated project has a valid Python package structure under `src/`
6. Clean up: `rm -rf /tmp/test-output`

Report any errors that occurred during generation and what they mean in the context of the template source files.
