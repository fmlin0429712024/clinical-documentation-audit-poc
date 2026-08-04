# Cheat Sheet: Claude Code Skills vs. Claude SDK

One line per point. Built from Phase 1 (Claude Code + Skills), Phase 2 (Claude SDK), and Phase 3 (GitHub CI/CD) of this project — see `docs/prd-agentic-audit-tracks.md`, `docs/prd-claude-sdk-migration.md`, and `docs/prd-github-headless-ci.md` for the full reasoning behind each line.

## Three products — don't conflate them

- `anthropic` (plain Python/TS SDK) = thin REST client, `client.messages.create()`, **zero built-in orchestration** — you hand-roll any multi-step loop yourself.
- `claude-agent-sdk` (Claude Agent SDK) = Claude Code's full harness as a library — built-in agent loop, built-in tools, native Skills, hooks, subagents, MCP, sessions.
- Claude Code CLI and the Agent SDK share the same engine — the SDK is the harness packaged as a library, not "built on" the CLI.
- Tool Runner (`client.beta.messages.tool_runner()`) = middle ground — handles the loop for tools *you* define, no built-in tools/Skills/sessions.

## Skills (`SKILL.md`)

- Frontmatter fields: `name`, `description` (drives auto-triggering by matching user intent), `allowed-tools`, `disallowed-tools`.
- `allowed-tools` **pre-approves** tools for the turn (skips the permission prompt) — it does **not** block other tools; it's not a sandbox.
- `disallowed-tools` removes a tool from the pool while the skill is active — docs don't confirm hard-block vs. soft restriction; verify before relying on it.
- Bare `Read` (no parens) approves reading any file; path-scoped `Read(pattern)` is confirmed for `settings.json` permission rules but only architecturally implied — not explicitly documented — inside a `SKILL.md`'s `allowed-tools`.
- Only `Read(path)` and `Edit(path)` are real permission-rule namespaces; `Write`/`NotebookEdit` have none of their own and fall under `Edit`.
- Claude Agent SDK supports Skills natively (reads `.claude/skills/`), but `allowed-tools` frontmatter is **CLI-only** — the SDK uses its own `allowedTools` session config instead.

## Deterministic vs. non-deterministic design

- Deterministic = zero LLM involvement in the verdict. Strongest form: the code never calls the API for that path at all — provable by inspection (e.g. an AST check asserting no `anthropic` import).
- Claude Code (agent-mediated) can only guarantee "the verdict wasn't computed by the LLM" — the orchestration loop that decides to call the tool is still LLM-driven. A hand-written script is a strictly stronger guarantee.
- Practicing agent tool-use: put iteration in the skill's *Workflow* (agent loops via repeated tool calls), not inside the tool itself — keeps looping as visible agent behavior, not hidden in code.
- In a hand-rolled SDK script this flips: there's no agent, so the loop is just your own code, by design — that's the whole point of Phase 2.

## Schema-enforced output (tool use)

- A tool definition = `name` + `description` + `input_schema` (standard JSON Schema).
- `tools=[...]` makes tool(s) *available*; `tool_choice` decides how much freedom the model has.
- `tool_choice` modes, increasing constraint: `auto` (model decides whether/which — default) → `any` (must call something, picks which) → `{"type":"tool","name":X}` (forced to call exactly `X`).
- Forcing one named tool via `tool_choice` is the **only** way to guarantee schema-conformant structured output from an LLM call.
- Response parsing: find the `content` block with `type == "tool_use"`; `block.input` is already a parsed dict matching the schema — no manual JSON parsing.
- Schema enforcement only matters when an LLM generates the output; deterministic code producing JSON (`json.dumps(dict)`) never needed it — that's *validation*, not *enforcement*, if you add a check at all.

## Preventing hallucinated routing/actions

- If the routing signal is already unambiguous (button click, status flag), decide in plain code before calling the LLM at all — never ask a question you already know the answer to.
- If routing needs free-text understanding, you can't eliminate the LLM from that decision — `tool_choice: any` forces *action*, not *correctness*.
- Real safety net for high-stakes actions: treat the LLM's tool call as a **proposal**, gate actual execution behind a separate deterministic check or human review — never auto-execute.

## Testing philosophy

- Deterministic code: real unit tests, cheap, fast, exact pass/fail.
- Non-deterministic output: schema-validity is 100% testable/enforceable; judgment *content* correctness is a "matches the worked example" check, not a mathematical guarantee — label it as such, don't conflate the two.

## GitHub CI/CD (Phase 3)

- GitHub Actions' unit of VM allocation is the **job**, not the workflow — each job in a workflow file gets its own fresh, throwaway runner; steps within one job share that one machine, but two jobs never share a machine.
- Branch protection has two independent axes: "require status checks to pass" (any number of automated checks — tests, linters, an AI review, etc.) and "require pull request reviews" (real human approvals only — a bot/Action posting a comment or a passing check never counts toward this). Both can gate the same merge button; neither replaces the other.
- Solo maintainer + "required review" is a real puzzle: GitHub won't let you approve your own PR. Fix is `enforce_admins: false` in branch protection, which lets the repo admin merge via an explicit "bypass rules" action — GitHub visibly flags this as merging without the required approval, which *is* the human-decision moment, just implemented as an admin override instead of a second person clicking Approve.
- A new job can run unconditionally on every PR (dumb, doesn't look at the diff) or depend on another job via `needs:` (e.g. skip an expensive/slow check if a cheap one already failed) — GitHub Actions itself has no built-in "only run if files X changed" judgment; that's what the separate `paths:`/`paths-ignore:` trigger filter is for, if you want it.
- A new status check isn't automatically a merge gate — it only blocks merging once explicitly added to branch protection's required-checks list. Adding a job and requiring it to pass are two separate decisions.
- Trap at the intersection of the two points above: a job skipped entirely by a `paths:` filter reports no status at all (not even a passing one) — if that same job is also a required check, a PR touching none of those paths stays blocked forever, waiting on a status that will never arrive.
- `anthropics/claude-code-action@v1` needs both an API credential (`ANTHROPIC_API_KEY` secret) *and* the separate Claude GitHub App installed on the repo (github.com/apps/claude) — the credential alone isn't sufficient.
- That App refuses to act (safely no-ops, doesn't hard-fail) when the triggering workflow file's content doesn't match the target branch's version — the exact situation on any PR that's itself introducing or editing that workflow file. Expected, self-resolving once such a PR merges; a real security control against a malicious PR editing the workflow to exploit the App's trusted credentials, not a bug.

## Git/security hygiene (learned the hard way, this project)

- `git status --short` collapses an entire untracked directory into one line — a per-file scan looping over that output silently skips every file inside it. Scan actual file lists (`git ls-files`, `git diff --cached`) instead.
- Read any `.env*` file by hand before committing near it — don't assume `.gitignore` covering `.env` makes its `.example` sibling safe by association.
- Any secret displayed anywhere (chat, logs, terminal output) = treat it as compromised and rotate it, regardless of whether it reached a remote.
- To remove a leaked secret from *unpushed* local commits: confirm nothing reached the remote yet, then `git reset --soft` to the last clean commit is safe (no data loss) — avoid interactive rebase (`-i`) for this.
