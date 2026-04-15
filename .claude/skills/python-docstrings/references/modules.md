# Module docstrings

Covers: regular modules, package `__init__.py` files, test modules, scripts.

---

## When Is a Module Docstring Required?

**Every non-test `.py` file should have a module docstring.** The docstring
appears as the very first statement in the file — before imports, before
constants, before anything else (after the optional shebang line).

Test modules are an exception — see [Test Modules](#test-modules) below.

---

## Placement

```python
# Optional: shebang line (scripts only)
#!/usr/bin/env python3

# Optional: license boilerplate comment (see below)

"""Module docstring goes here — before imports."""

import os
import sys
```

The module docstring must come **before imports**. A license comment block
(not a docstring) may appear above the module docstring.

---

## Standard Format

```python
"""A one-line summary of the module or program, terminated by a period.

Leave one blank line. The rest of this docstring should contain an
overall description of the module or program. Optionally, it may also
contain a brief description of exported classes and functions and/or
usage examples.

Typical usage example:

  foo = ClassFoo()
  bar = foo.function_bar()
"""
```

### Summary line rules
- One physical line
- ≤ 80 characters
- Ends with `.`, `?`, or `!`
- Describes what the module *provides*, not what it *is* (not "This module…")

### Extended description
- Separate from summary by one blank line
- Describes purpose, scope, and any important usage notes
- May include a brief inventory of exported public names

### Usage examples
- Show the most common usage pattern
- Use 2-space indent inside the docstring
- Keep examples short and realistic — they will appear in `pydoc` output

---

## Real-World Examples

### Utility module
```python
"""Utilities for reading and writing user configuration files.

Provides functions for loading config from disk, merging with defaults,
and persisting changes atomically. Supports JSON and TOML formats.

Typical usage example:

  config = load_config('/etc/myapp/config.json')
  config['theme'] = 'dark'
  save_config(config, '/etc/myapp/config.json')
"""
```

### Class-heavy module
```python
"""Data models for the user management subsystem.

Defines the core User, UserProfile, and UserSession classes used
throughout the application. All models support JSON serialization
via their to_dict() and from_dict() class methods.
"""
```

### Script / entry-point file
```python
"""Batch processor for nightly data pipeline runs.

Reads pending jobs from the queue, processes each in parallel, and
writes results to the configured output bucket.

Typical usage:

  python batch_runner.py --env=prod --workers=8
"""
```

### Package `__init__.py`
```python
"""Public API for the mypackage library.

This package provides tools for X, Y, and Z. Import from this
module to access the stable public interface:

  from mypackage import FeatureExtractor, run_pipeline
"""
```

---

## License Boilerplate

Every file should contain a license header. This is a **comment block**, not
a docstring — it appears before the module docstring and uses `#`:

```python
# Copyright 2024 MyCompany Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Module docstring follows the license comment."""
```

The specific boilerplate depends on the project's license (Apache 2.0, MIT,
BSD, GPL, etc.). When adding docstrings to existing files, preserve any
existing license header — never move or remove it.

---

## Test Modules

Test module docstrings are **not required by default**. Include one only when
there is genuinely useful additional information that aids running or understanding the tests.

### Include a test module docstring when...

- The test requires special setup or teardown instructions
- The test uses golden files and explains how to update them
- The test has unusual environment dependencies
- The test explains a complex or non-obvious testing pattern

```python
"""Integration tests for the Bigtable reader.

These tests require a running Bigtable emulator. Start it with:

  gcloud beta emulators bigtable start

Set BIGTABLE_EMULATOR_HOST before running:

  export BIGTABLE_EMULATOR_HOST=localhost:8086
  pytest tests/test_bigtable_reader.py
"""
```

```python
"""Tests for the report generator using golden files.

Update golden files after intentional output changes:

  pytest tests/test_report.py --update-golden
"""
```

### Do NOT include a test module docstring that adds no information

```python
# ❌ Useless — omit this entirely
"""Tests for foo.bar."""

# ❌ Useless
"""Unit tests for the UserProfile class."""
```

If a test docstring would only restate what the filename already says, leave it out.

---

## Checklist Before Finishing a Module Docstring

- [ ] Appears before all imports
- [ ] Summary line is ≤ 80 chars and ends with punctuation
- [ ] Describes what the module *provides* (not "This module…")
- [ ] Usage example present (for modules intended to be imported and used)
- [ ] License boilerplate present (as a `#` comment above the docstring)
- [ ] If test module: only included when there's genuinely useful information
