# Repository Agent Entry Point

**Mandatory for every Expert, Skill, Connector and coding/QA/manager agent in this repository.**

Before any repository inspection that leads to changes, implementation, test, cleanup, packaging, Git operation, or task handoff:

1. Read the root [`agent.md`](./agent.md) **in full**. It is the authoritative cross-product development and repository hygiene policy.
2. Read the product-specific frozen contracts and any stricter local instructions; preserve their approved scope.
3. Apply `agent.md` to all participating subagents and worktrees. Do not claim platform/runtime enforcement unless that integration has been installed and verified.
4. After each writable task, execute the applicable test, cleanup, `dist` preservation, selective staging, local-commit and verification gates. No automatic push, merge or publish by default; only the product-scoped private-test authorization in [`docs/wangbin-estimate-calculator-private-test-authorization.md`](docs/wangbin-estimate-calculator-private-test-authorization.md) permits its exact private import/testing and scoped ordinary branch push. All other prohibitions remain.

If `agent.md` cannot be read, **stop before destructive changes or Git writes** and report the missing prerequisite. Never silently ignore it.
