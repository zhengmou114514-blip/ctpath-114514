# Autoresearch Method

This local skill adapts the public `karpathy/autoresearch` workflow to CTpath.

## What is preserved

- Human-written program file as the source of truth
- Bounded edit surface
- Fixed verification loop
- Multiple small attempts instead of one large rewrite
- Keep-only-winning ratchet

## What changes in CTpath

- Replace training scripts with product subsystems
- Replace model score with acceptance checks, contract tests, or measured UX/runtime outcomes
- Replace experiment table with short run notes under `docs/autoresearch/runs/`

## Recommended structure for a run

1. Read `docs/autoresearch/program.md`
2. Summarize the single target and allowed files
3. Choose one hypothesis
4. Implement the smallest viable attempt
5. Run the exact verification commands from the brief
6. Record:
   - hypothesis
   - files touched
   - command results
   - keep/discard decision
7. Repeat until the stop condition is met

## Example CTpath targets

- Improve logout handoff latency without touching unrelated pages
- Make one contract test pass in `model-api`
- Reduce first-render waiting in one workspace page
- Tighten one middleware chain and verify headers

## Non-goals

- Freeform refactoring with no metric
- Unbounded cross-module rewrites
- Mixing clinic and model concerns in a single run
- Keeping speculative changes without verification evidence
