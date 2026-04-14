# Stage banner format

Display at the top of every response during the SDLC workflow.

## Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SDLC  ○DESIGN  ○RED  ○GREEN  ○REFACTOR  ○QUALITY  ○SECURE  ○DOCS  ○COMMIT  ○PR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Symbols

| Symbol | Meaning |
|---|---|
| `✓` | Stage completed successfully |
| `●` | Stage currently active |
| `○` | Stage not yet started |
| `✗` | Stage failed |

## Examples

Mid-cycle (GREEN active):
```
SDLC  ✓DESIGN  ✓RED  ●GREEN  ○REFACTOR  ○QUALITY  ○SECURE  ○DOCS  ○COMMIT  ○PR
```

Parallel stages active:
```
SDLC  ✓DESIGN  ✓RED  ✓GREEN  ✓REFACTOR  ●QUALITY  ●SECURE  ●DOCS  ○COMMIT  ○PR
```

Pipeline complete:
```
SDLC  ✓DESIGN  ✓RED  ✓GREEN  ✓REFACTOR  ✓QUALITY  ✓SECURE  ✓DOCS  ✓COMMIT  ✓PR
```
