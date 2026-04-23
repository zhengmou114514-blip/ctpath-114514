---
name: autoresearch
description: Run a Karpathy-style autoresearch loop inside this repository. Use when Codex should iteratively improve one bounded subsystem by following a program.md brief, changing only the allowed files, running a fixed verification loop, keeping winning changes, and discarding losing or broken experiments.
---

# Autoresearch

Use this skill to apply the `karpathy/autoresearch` method to a normal product/codebase task.

The upstream repo is not a Codex skill package. Its useful part is the workflow: a human-written `program.md`, a narrow edit surface, a fixed evaluation loop, and a keep-or-discard ratchet. Reuse that method here instead of copying its ML repository layout literally.

## Core Idea

Treat `program.md` as the control plane.

- Read one scoped brief first.
- Modify only the files the brief explicitly allows.
- Run the same verification loop every iteration.
- Keep only changes that improve the measured outcome.
- Discard broken, regressive, or inconclusive attempts.

The objective is not to "change a lot of files". The objective is to make many small, measurable, reversible attempts against one stable target.

## Required Inputs

Before editing, load a project-local program file:

- Primary path: [docs/autoresearch/program.md](E:/CTpath-master/docs/autoresearch/program.md)
- If it does not exist, create it from [assets/program-template.md](E:/CTpath-master/.agents/skills/autoresearch/assets/program-template.md)

The brief must define:

- Target subsystem
- In-scope files
- Out-of-scope files
- Verification command(s)
- Success signal
- Revert rule
- Stop condition

If the brief is vague, tighten it before running the loop.

## Experiment Loop

Repeat this cycle while the brief still has headroom:

1. Check git/worktree state and current target files.
2. Form one concrete hypothesis.
3. Edit only allowed files.
4. Run the fixed verification command(s).
5. Record the result.
6. Keep the change only if the evidence improved.
7. Revert failed, regressive, or inconclusive attempts.

Prefer one hypothesis per iteration.

## Keep or Discard

Keep a change only if one of these is true:

- A failing command now passes
- A new acceptance check is now satisfied
- A measured response improved without breaking existing checks
- A user-facing defect is removed and the verification loop still passes

Discard the change if:

- Verification fails
- The outcome is ambiguous
- The change spills outside the scoped files
- The fix depends on unverified assumptions

## CTpath Translation

This repository is not a pure training repo. Translate `autoresearch` into product iteration:

- Replace `train.py` with the current bounded implementation surface
- Replace model loss or validation score with a project-specific acceptance metric
- Replace a short training run with a fixed build/test/manual-contract loop
- Replace `results.tsv` with a short run note under `docs/autoresearch/runs/`

Good targets in this repo:

- one page + one composable + one test
- one API service + one contract test
- one middleware chain + one verification script

Bad targets:

- the whole frontend
- all model features
- all backend cleanup

## Verification

Always use explicit commands from `program.md`. Prefer repo-native commands such as:

```powershell
cd E:\CTpath-master\frontend
npm run build
npm test -- src/pages/__tests__/AppBootstrap.spec.ts src/pages/__tests__/PatientDetailPage.spec.ts src/pages/__tests__/AppWorkspacePage.spec.ts
```

```powershell
cmd /c "set CONDA_NO_PLUGINS=true && conda run --no-capture-output -n ctpath python E:\CTpath-master\test_backend_contracts.py"
```

Do not claim progress without fresh evidence from the commands you actually ran.

## Outputs

For each run, leave behind:

- the updated code if the attempt won
- a short run note under `docs/autoresearch/runs/`
- the verification result summarized in plain language

When you need more detail about the method, load:

- [references/autoresearch-method.md](E:/CTpath-master/.agents/skills/autoresearch/references/autoresearch-method.md)
