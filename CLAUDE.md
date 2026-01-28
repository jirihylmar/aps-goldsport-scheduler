# GoldSport Scheduler

Scheduling engine for GoldSport ski school - processes lesson bookings, manages schedules, and provides display output for vertical screens.

---

## Quick Reference

| Item | Value |
|------|-------|
| AWS Account | `299025166536` |
| AWS Region | `eu-central-1` |
| MCP Tool | `mcp__aws-vsb-299__call_aws` |
| Naming | `goldsport-scheduler-{type}-{env}` |

## Commands
```
/start-session      # Init + verify last task + context check
/update-progress    # Conservative progress update
/generate-phases    # Decompose spec into phases/tasks (Phase 0)
/add-work           # Add phases/tasks mid-project
/check-aws          # Verify AWS resources
```

## Key Files
| File | Purpose | Updates |
|------|---------|---------|
| `IMPLEMENTATION_PLAN.md` | Specification (architecture, design) | Rarely |
| `progress.json` | Task state - **SINGLE SOURCE OF TRUTH** | Every session |
| `tasks/phase_*.md` | Task implementation details | When tasks added |
| `session_notes.md` | Session history log | Every session |

---

## Session Scope

### Context Budget
Check with `/context`:
- **<40%**: Start any task
- **40-60%**: Small/medium tasks only
- **60-80%**: Finish current, then wrap up
- **>80%**: Update progress.json and end session

### Per Session
- Complete **AT LEAST ONE** task perfectly
- Leave codebase in **deployable state**
- Don't start tasks you can't finish

---

## Progress Update Rules

**progress.json is append-only for tasks.**

### ALLOWED:
- Change task `status`
- Add timestamps, artifacts, notes
- Add NEW tasks with new IDs (use sub-IDs: 2.3a, 2.3b)

### NEVER:
- Remove tasks (mark `superseded` instead)
- Reorder tasks
- Rename tasks (add note instead)
- Change task IDs

---

## Task Sizing

Before adding task to progress.json:
- [ ] Single deliverable (one sentence)?
- [ ] Verifiable (one command/action)?
- [ ] ≤3 files touched?
- [ ] <30 min Claude time?
- [ ] Deployable state after completion?

**If any NO → break it down further**

| Size | Files | Time |
|------|-------|------|
| small | 1-2 | <15min |
| medium | 2-3 | 15-30min |
| large | 3+ | **Break down** |

---

## Critical Rules

### 1. AWS Account Verification
**ALWAYS verify before any AWS operation.**

```
mcp__aws-vsb-299__call_aws aws sts get-caller-identity
```

Must match: `299025166536` / `eu-central-1`

### 2. Use MCP Tools
```bash
# CORRECT - Use MCP (pre-configured)
mcp__aws-vsb-299__call_aws aws s3 ls

# WRONG - Never export profiles
export AWS_PROFILE=...
```

### 3. Infrastructure Changes Through CDK Only
```bash
# WRONG - Direct AWS modifications cause drift
aws lambda update-function-code ...
aws s3api put-bucket-policy ...

# RIGHT - All changes through CDK
cd infrastructure && npx cdk deploy
```

Never modify AWS resources directly via CLI/console.

### 4. Pre-Work Verification
Before starting NEW work:
1. Find last `complete` task in progress.json
2. Run its `verify` step
3. If FAILS → fix before proceeding
4. If PASSES → continue

### 5. Context Management - CRITICAL
Before starting any significant task, check `/context`. If:
- **Free space < 20%** OR
- **Remaining space insufficient for task**

**Then IMMEDIATELY:**
1. Run `/update-progress` to save current state
2. Update `session_notes.md` with detailed context
3. Commit changes
4. Inform user: "Context limit approaching. Progress saved."

### 6. Verify Against Real Data
Before marking tasks complete:
- Run operations against **real data**, not just test fixtures
- When task involves multiple components, verify **each one**
- Don't mark phase complete until all components verified

---

## Project Structure (Mono-Repo)

```
aps-goldsport-scheduler/           # This repository
├── CLAUDE.md                      # This file
├── IMPLEMENTATION_PLAN.md         # Specification
├── progress.json                  # Task state
├── session_notes.md               # Session log
├── tasks/                         # Task details by phase
│   ├── phase_1_infrastructure.md
│   ├── phase_2_processing.md
│   └── ...
├── config/                        # Configuration files
│   ├── ui-translations.json
│   ├── dictionaries.json
│   └── enrichment.json
├── infrastructure/                # CDK project
│   ├── bin/app.ts
│   ├── lib/scheduler-stack.ts
│   ├── cdk.json
│   └── package.json
├── lambda/                        # Lambda source
│   └── processor/
│       ├── handler.py
│       └── requirements.txt
└── static-site/                   # Frontend
    ├── index.html
    ├── styles.css
    └── app.js
```

---

## AWS Resources

| Resource | Name (prod) |
|----------|-------------|
| Input Bucket | `goldsport-scheduler-input-prod` |
| Website Bucket | `goldsport-scheduler-web-prod` |
| DynamoDB | `goldsport-scheduler-data-prod` |
| Lambda | `goldsport-scheduler-engine-prod` |
| CloudFront | `goldsport-scheduler-cdn-prod` |

---

## Session Protocol

1. Run `/start-session`
2. Read `progress.json` to identify current task
3. Read relevant `tasks/phase_*.md` file
4. **Check `/context` before starting significant work**
5. Complete tasks with verification
6. Commit changes
7. Run `/update-progress`
8. **Before next task: re-check `/context`** - if low, save and end session

---

## Tool Usage

| Task | Tool | Not |
|------|------|-----|
| Read files | `Read` | `cat` |
| Edit files | `Edit` | `sed` |
| Search files | `Glob`/`Grep` | `find`/`grep` |
| AWS operations | `mcp__aws-vsb-299__call_aws` | bash aws |
