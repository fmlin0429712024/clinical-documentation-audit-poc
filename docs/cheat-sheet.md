# Cheat Sheet: Claude Code Skills vs. Claude SDK

One line per point. Built from Phase 1 (Claude Code + Skills) and Phase 2 (Claude SDK) of this project — see `docs/prd-agentic-audit-tracks.md` and `docs/prd-claude-sdk-migration.md` for the full reasoning behind each line.

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

## Git/security hygiene (learned the hard way, this project)

- `git status --short` collapses an entire untracked directory into one line — a per-file scan looping over that output silently skips every file inside it. Scan actual file lists (`git ls-files`, `git diff --cached`) instead.
- Read any `.env*` file by hand before committing near it — don't assume `.gitignore` covering `.env` makes its `.example` sibling safe by association.
- Any secret displayed anywhere (chat, logs, terminal output) = treat it as compromised and rotate it, regardless of whether it reached a remote.
- To remove a leaked secret from *unpushed* local commits: confirm nothing reached the remote yet, then `git reset --soft` to the last clean commit is safe (no data loss) — avoid interactive rebase (`-i`) for this.
