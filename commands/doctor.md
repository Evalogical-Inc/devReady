---
description: Run DevReady and explain any environment problems
---

Run `devready check --format json` in the current project. If the command is missing, follow the fallback order in the devready skill (`python -m devready`, then `uvx`, then `pipx run`) and, if none work, tell the user how to install it instead of installing anything yourself. Summarize failures first, then warnings, each with the suggested next step. Do not change anything without asking.
