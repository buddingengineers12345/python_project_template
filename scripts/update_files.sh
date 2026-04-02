#!/bin/sh
# Sync VS Code settings (these should be identical between root and template)
cp .vscode/settings.json template/.vscode/settings.json.jinja
cp .vscode/launch.json template/.vscode/launch.json.jinja
cp .vscode/extensions.json template/.vscode/extensions.json.jinja

# WARNING: .gitignore and .pre-commit-config.yaml have template-specific
# additions. Do NOT blindly copy. Instead, manually diff and merge:
#   diff .gitignore template/.gitignore.jinja
#   diff .pre-commit-config.yaml template/.pre-commit-config.yaml.jinja
echo "NOTE: .gitignore and .pre-commit-config.yaml must be manually diffed."
echo "      template versions have extra entries (forbidden-rej-files hook, etc.)"
