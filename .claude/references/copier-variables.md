# Copier Variables and Conventions

## Variable conventions (copier.yml)

- Questions are defined under top-level keys in `copier.yml`.
- Computed values (not shown to users) use **`when: false`** with a **`default`** so they are not
  prompted or stored in the answers file.
- Use **`secret: true`** (with a **`default`**) for sensitive answers so they are not written to
  `.copier-answers.yml`.
- Post-generation `_tasks` run shell commands after rendering. Keep them idempotent.
- `_skip_if_exists` prevents overwriting user edits when running `copier update`.

## Jinja2 conventions

- Template files use `{{ variable_name }}` for substitution.
- Conditional blocks use `{% if condition %}...{% endif %}`.
- File names can themselves be templated: e.g., `src/{{ package_name }}/__init__.py.jinja`.
- The `jinja2_time.TimeExtension` is available for `{% now %}` expressions.
- The `jinja2.ext.do` and `jinja2.ext.loopcontrols` extensions are also enabled.
