Check for updates from the Copier template that generated this project (if `.copier-answers.yml` is present).

1. Run `copier check-update` from the project root and summarize whether a newer template version is available
2. If the user wants to apply updates: remind them to commit or stash a clean `git status`, then run `copier update --trust` (or `copier update --trust --defaults` to reuse answers)
3. Mention `copier recopy` only as a last resort when `copier update` fails, and that it does not use the smart merge algorithm

Do not run destructive git commands unless the user explicitly asks.
