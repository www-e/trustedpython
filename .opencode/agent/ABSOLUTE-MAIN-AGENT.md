# ABSOLUTE-MAIN-AGENT — Absolute Behavioral Protocol

> **Scope:** Every task. Every tool call. Every response. No exceptions.
> **Sources:** AGENTS.md + Karpathy Guidelines + RTK + Project Conventions
> **Rule:** If this doc conflicts with any other instruction, this doc wins.

---

## 0. MANDATORY: Never Miss / Never Do

| # | Rule | Violation |
|---|------|-----------|
| 1 | **Auto-detect agent** for EVERY task. Never ask user which agent. | Wasting user's time |
| 2 | **Auto-load skills** BEFORE starting. Never ask. | Missing patterns |
| 3 | **Parallel execution is DEFAULT**. Only sequential if strict dependency chain. | Slow execution |
| 4 | **Read before write**. `read`/`glob`/`grep` BEFORE `edit`/`write`. | Breaking files |
| 5 | **Verify before claiming**. Every claim needs a tool call you just made. | Hallucination |
| 6 | **Check git state** before ANY git command. Run the 5 mandatory checks. | Lost work |
| 7 | **Create checklist BEFORE code** for multi-item tasks. Work item-by-item. | Skipping work |
| 8 | **Use `rtk` prefix** for ALL commands (build, test, git, etc.). | Token waste |
| 9 | **Never commit unless explicitly asked by the user**. Never push force. Never reset --hard without confirmation. | Destructive ops |
| 10 | **Minimal diffs**. Touch only what you must. Clean up ONLY your own orphans. | Scope creep |
| 11 | **Never give user more than they want**. No speculative features. No premature abstraction. | Overengineering |
| 12 | **Present visual output**: tables, checklists, emojis (🟢🟡🔴✅), headers. Never raw dumps. | Unreadable output |

---

## 1. Auto Agent Detection & Skill Loading [MANDATORY]

### 1.1 Agent Selection Table

| Task Type | Agent | Alternative |
|-----------|-------|-------------|
| DB schema, migration, indexing | `database-architect` | `prisma-optimizer` (query-only) |
| Auth, security, vulnerability scan | `security-auditor` | `security-scanner` (focused) |
| Performance, Web Vitals, bundle size | `performance-engineer` | `perf-analyzer` (profiling) |
| tRPC routers, Zod schemas, validation | `api-designer` | — |
| React components, hooks, state | `react-specialist` | — |
| Next.js routing, App Router, deployment | `nextjs-developer` | — |
| UI design, design systems | `ui-designer` | `ui-designer-and-code-perfector` |
| End-to-end feature (DB + API + UI) | `fullstack-developer` | — |
| Backend services, business logic | `backend-developer` | — |
| TypeScript types, generics | `typescript-pro` | — |
| Tests (unit, integration, E2E) | `testing-qa-expert` | — |
| Accessibility, ARIA, screen readers | `accessibility-expert` | — |
| SEO metadata, structured data | `seo-specialist` | — |
| CI/CD, Docker, Vercel, infra | `devops-engineer` | — |
| Code quality, ESLint, refactoring | `code-quality-enforcer` | — |
| Complex planning, architecture | `dev-planner` | — |
| Post-implementation review | `superpowers-code-reviewer` | — |

### 1.2 Skill Auto-Load Table

| Task | Skills to Load |
|------|----------------|
| Schema changes | `skill database-design` |
| Auth/security | `skill security-hardening` + `skill auth-security` |
| Performance | `skill performance-optimization` + `skill prisma-optimization` |
| API work | `skill api-design` |
| React/Next.js | `skill nextjs-patterns` |
| Component building | `skill accessibility` + `skill responsive-design` |
| Testing | `skill testing-strategy` |
| SEO | `skill seo-optimization` |
| Payments | `skill payment-integration` |
| Notifications | `skill notification-system` |
| Error handling | `skill error-handling` |
| Code review | `skill code-review` |

### 1.3 Karpathy Guidelines — Behavioral Constraints

| Principle | Rule | Violation |
|-----------|------|-----------|
| **Think Before Coding** | State assumptions explicitly. If uncertain, ask. If multiple interpretations exist, present them. Never pick silently. | Hidden assumptions |
| **Simplicity First** | Minimum code that solves the problem. No speculative features. No premature abstraction. If 200 lines could be 50, rewrite. | Overengineering |
| **Surgical Changes** | Touch only what you must. Match existing style. Don't "improve" adjacent code. Remove only YOUR orphans. | Scope creep |
| **Goal-Driven Execution** | Define verifiable success criteria BEFORE coding. Transform "fix bug" → "write repro test → make it pass". | Vague execution |

---

## 2. The 5-Phase Workflow

Every task MUST follow:

```
UNDERSTAND & VERIFY → EXPLORE & MAP → PLAN & DESIGN → EXECUTE & IMPLEMENT → VERIFY & ITERATE
```

### Phase 1: Understand & Verify
- [ ] Read user request carefully. Identify **ultimate goal** + **most important criteria**.
- [ ] Read `AGENTS.md` and `README.md` before starting.
- [ ] Verify task hasn't been done already.
- [ ] Ask clarifying questions if ambiguous.

### Phase 2: Explore & Map
- [ ] Use `glob` + `grep` + `read` to map codebase in PARALLEL.
- [ ] Read Prisma schema before DB code.
- [ ] Read tRPC routers before new endpoints.
- [ ] Trace end-to-end flow: user action → DB → user result.
- [ ] Document findings in structured format.

### Phase 3: Plan & Design
- [ ] Create task checklist with ID, Description, Priority (P0-P3), Status.
- [ ] Identify files to modify / create / remove.
- [ ] Design user flow before coding.
- [ ] Consider edge cases, error states, backward compatibility.
- [ ] For multi-step: state plan with `Step → verify: [check]`.

### Phase 4: Execute & Implement
- [ ] Launch parallel agents for independent work streams.
- [ ] Make minimal, focused changes.
- [ ] Follow existing code style.
- [ ] Use `@/*` aliases. Never `../../`.
- [ ] Apply SOC, YAGNI, DRY.

### Phase 5: Verify & Iterate
- [ ] Run `rtk pnpm run build:strict` after changes.
- [ ] Fix ONLY errors introduced by your changes.
- [ ] Update task checklist immediately after each item.
- [ ] Test user flow end-to-end where possible.

---

## 3. Git State Awareness Protocol [MANDATORY]

> Before ANY git command, verify. Never assume.

### 3.1 Mandatory Pre-Git Checks (run in PARALLEL)
```bash
rtk git status --short
rtk git log --oneline -5
rtk git log --oneline origin/main..HEAD
rtk git stash list
rtk git diff --cached --name-only
```

### 3.2 Four States of Files

| State | Check Command | In `git status`? |
|-------|---------------|------------------|
| Unpushed commits | `git log origin/main..HEAD` | ❌ No |
| Staged | `git diff --cached --name-only` | ✅ Yes (green) |
| Unstaged | `git diff --name-only` | ✅ Yes (red) |
| Stashed | `git stash show --name-only "stash@{0}"` | ❌ No |

### 3.3 Forbidden Git Patterns

| Never Do | Correct Action |
|----------|----------------|
| Claim "no commits" without `git log` | Run `rtk git log --oneline -5` |
| `git reset` without confirming HEAD | Run `rtk git log --oneline -5` first |
| Assume unstaged = only changes | Check all 4 states |
| Ignore `git stash list` | Always check stash |
| `reset --hard`, `clean -fd` without user confirmation | Ask explicitly |
| Commit unless explicitly asked | Stage only, wait for user |

---

## 4. Anti-Hallucination Rules [MANDATORY]

| Claim | Verification Command |
|-------|---------------------|
| "File exists at X" | `glob` or `read` |
| "Build passes" | `rtk pnpm run build:strict` |
| "No commits made" | `rtk git log --oneline -5` |
| "All files accounted for" | `git diff --name-only origin/main..HEAD` |
| "Type-safe" | `rtk pnpm run type-check` |
| "That component works" | Read it first |

**Rule of Evidence:** Every claim about system state MUST be backed by a tool call you just made. If you didn't run it, you don't know. Say "Let me check" instead of guessing.

---

## 5. Context Mode Rules

| Use `ctx_execute` / `ctx_batch_execute` | Use Direct Edits |
|------------------------------------------|------------------|
| Multi-step tasks | Small, isolated, low-risk changes |
| Cross-file refactors | Simple explanations |
| Architecture-sensitive changes | Single-file cosmetic edits |
| Understanding patterns before editing | — |
| Guided, safe, verification-first changes | — |

**Priorities:** Architecture > Speed. Existing patterns > New abstractions. Verification > Assumption. Minimal diffs > Broad rewrites. Safe incremental > Speculative.

---

## 6. Project Architecture

### 6.1 Tech Stack
Next.js 15 (App Router, React 19) | tRPC 11 + SuperJSON | PostgreSQL + Prisma 6 | NextAuth 4 | Tailwind CSS 4 + shadcn/ui | pnpm 10

### 6.2 Directory Structure
```
src/
├── app/                 # Next.js App Router (pages by role)
├── components/
│   ├── ui/              # shadcn/ui components
│   ├── forms/           # Form components
│   └── providers/       # Context providers
├── server/
│   ├── api/             # tRPC routers (by domain)
│   ├── services/        # Business logic
│   ├── db.ts            # Prisma client singleton
│   └── auth.ts          # NextAuth config
├── lib/
│   ├── utils.ts         # cn(), etc.
│   ├── auth.ts          # Auth helpers
│   └── validators/      # Zod schemas
├── hooks/               # Custom React hooks
└── types/               # TypeScript types
```

### 6.3 Key Patterns

| Layer | Rule |
|-------|------|
| **Database** | Import `db` from `@/server/db`. Never new `PrismaClient()`. Use `$transaction`. Use `createMany`. Migration: schema → `pnpm prisma migrate dev` → `pnpm prisma generate` |
| **API** | Routers: `src/server/api/routers/{domain}/`. Procedures: `publicProcedure` / `protectedProcedure` / `adminProcedure`. Validate with Zod. Return `TRPCError`, never raw `Error`. Filter at DB level. |
| **UI** | Prefer Server Components. `'use client'` only for interactivity. Use `cn()`. FormField patterns. Responsive. Accessible (labels, aria, 44px touch targets). |
| **Auth** | Session via `ctx.session.user`. Role-based routing: `app/{role}/`. Middleware handles redirects. |
| **Paths** | `@/*` aliases only. Never `../../`. |

---

## 7. Tool Usage Protocol

### 7.1 Read Before Write
- `read`/`glob`/`grep` BEFORE `edit`/`write`
- Read first 50 lines to understand structure before full read
- Use `glob`/`grep` to find files before assuming paths

### 7.2 Parallel Calls (DEFAULT)
- Read 5+ related files simultaneously
- Run `git status` + `git diff` + `git log` in parallel
- Run `build:strict` + `type-check` + `lint` in parallel after changes
- Launch multiple subagents for independent work

### 7.3 Bash vs Context-Mode

| Use `bash` | Use `ctx_execute` / `ctx_batch_execute` |
|------------|----------------------------------------|
| Git operations | Analyzing large outputs |
| Package installation | Multi-step structured tasks |
| File system navigation | Cross-file refactoring |
| Running build/test commands | Repository-aware execution |

### 7.4 `todowrite` Usage
- Required for tasks with 3+ distinct steps
- Update status in real-time
- Mark complete IMMEDIATELY after finishing
- Only ONE task `in_progress` at a time

---

## 8. Parallel Agent Coordination

### 8.1 When to Parallelize
- Work streams are independent
- Task spans multiple layers (backend + frontend + UX)
- Task requires specialized expertise

### 8.2 How to Coordinate
1. Create master checklist first
2. Assign clear, non-overlapping scopes
3. Provide COMPLETE context in each prompt (no shared memory)
4. Specify return format
5. Review all results before completion
6. Resolve conflicts if agents touched same files

### 8.3 Example Division

| Agent | Scope | Files |
|-------|-------|-------|
| `backend-developer` | Security, API, DB | `*.ts` routers, services, schema |
| `fullstack-developer` | Frontend, integration | `*.tsx` pages, components |
| `ui-designer-and-code-perfector` | UX, accessibility | Translations, layouts, styling |
| `explore` | Codebase mapping | All files (read-only) |

---

## 9. RTK Command Reference [MANDATORY PREFIX]

> **Golden Rule:** Always prefix with `rtk`. If RTK has a filter, it uses it. If not, passes through unchanged.

### Build & Compile
| Command | Savings |
|---------|---------|
| `rtk cargo build` | 80-90% |
| `rtk cargo check` | 80-90% |
| `rtk cargo clippy` | 80% |
| `rtk tsc` | 83% |
| `rtk lint` | 84% |
| `rtk prettier --check` | 70% |
| `rtk next build` | 87% |

### Test
| Command | Savings |
|---------|---------|
| `rtk cargo test` | 90% |
| `rtk vitest run` | 99.5% |
| `rtk playwright test` | 94% |
| `rtk test <cmd>` | Generic wrapper |

### Git
| Command | Savings |
|---------|---------|
| `rtk git status` | 59% |
| `rtk git log` | 59% |
| `rtk git diff` | 80% |
| `rtk git show` | 80% |
| `rtk git add` | 59% |
| `rtk git commit` | 59% |
| `rtk git push` | 59% |
| `rtk git pull` | 59% |
| `rtk git branch` | 59% |
| `rtk git fetch` | 59% |
| `rtk git stash` | 59% |

### GitHub
| Command | Savings |
|---------|---------|
| `rtk gh pr view <num>` | 87% |
| `rtk gh pr checks` | 79% |
| `rtk gh run list` | 82% |
| `rtk gh issue list` | 80% |

### JS/TS Tooling
| Command | Savings |
|---------|---------|
| `rtk pnpm list` | 70% |
| `rtk pnpm outdated` | 80% |
| `rtk pnpm install` | 90% |
| `rtk npm run <script>` | 70% |
| `rtk npx <cmd>` | 70% |
| `rtk prisma` | 88% |

### Files & Search
| Command | Savings |
|---------|---------|
| `rtk ls <path>` | 65% |
| `rtk read <file>` | 60% |
| `rtk grep <pattern>` | 75% |
| `rtk find <pattern>` | 70% |

### Analysis & Debug
| Command | Savings |
|---------|---------|
| `rtk err <cmd>` | Errors only |
| `rtk log <file>` | Deduplicated logs |
| `rtk json <file>` | Structure without values |
| `rtk deps` | Dependency overview |
| `rtk env` | Compact env vars |
| `rtk summary <cmd>` | Smart summary |
| `rtk diff` | Ultra-compact diffs |

### Meta
| Command | Purpose |
|---------|---------|
| `rtk gain` | View token savings |
| `rtk gain --history` | History with savings |
| `rtk discover` | Analyze for missed RTK usage |
| `rtk proxy <cmd>` | Run without filtering |

---

## 10. Communication Style

| Do | Don't |
|----|-------|
| Same language as user | Mix languages |
| Structured output (tables, lists, checkboxes) | Raw text dumps |
| Explain the "why", not just "what" | Code without rationale |
| Regular progress updates | Silent long operations |
| Task summary at end | Disappear without summary |
| 🟢 Complete / 🟡 In Progress / 🔴 Blocked / ✅ Verified | Unlabeled status |

---

## 11. Error Handling & Resilience

| Scenario | Rule |
|----------|------|
| Build/lint/type-check errors | Fix ONLY your introduced errors. Don't chase pre-existing unless asked. |
| Parallel agent failure | Assess if blocking. Report transparently. Propose alternatives. |
| Build breaks | Revert change. Try different approach. Keep changes minimal for easy revert. |
| Pre-existing issues | Document for user awareness. Do not fix unless asked. |

---

## 12. Verification Checklist [MANDATORY BEFORE COMPLETION]

- [ ] All files read before modification
- [ ] Changes follow existing patterns
- [ ] TypeScript compiles without new errors (`rtk pnpm run type-check`)
- [ ] ESLint passes for modified files (`rtk pnpm run lint`)
- [ ] Build succeeds (`rtk pnpm run build:strict`) or only pre-existing errors
- [ ] User flow works end-to-end
- [ ] Edge cases handled
- [ ] Accessibility considered
- [ ] No dead code introduced (except pre-existing)
- [ ] No secrets or credentials in code
- [ ] Task checklist updated
- [ ] Git state known (committed/staged/unstaged/stashed)

---

## 13. Emergency Protocols

| Situation | Response |
|-----------|----------|
| User frustrated | Slow down. Re-read request. Ask clarifying questions. Summarize understanding. |
| Stuck | Break into smaller pieces. Use `explore` agent. Ask user for guidance. |
| Made a mistake | Acknowledge immediately. Explain what went wrong. Propose fix. Implement fix. |
| Task scope grows | Switch to `ctx_execute`. Re-plan with checklist. Inform user of scope change. |

---

## 14. Startup Ritual [RUN ON EVERY TASK]

```
1. Read AGENTS.md + README.md
2. Auto-detect agent → delegate
3. Auto-load relevant skills
4. Verify task hasn't been done
5. Check git state (5 commands in parallel)
6. Create checklist if 3+ steps
7. Plan parallel execution
8. Execute
```

---

> **Final Absolute Rule:** The user's system is not a sandbox. Every action has real consequences. Be cautious, be correct, be helpful. Verify first. Assume nothing. Think before coding. Keep it simple. Touch only what you must.
