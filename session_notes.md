# Session Notes

## Session 1 - 2026-01-28

### Task 0.1: Read input materials and explore examples

#### Input Materials Analysis

**idea.md - Ski School Display System:**
- External vertical display for showing lessons
- Web address that auto-updates at intervals
- Shows current courses and upcoming courses for the day
- Privacy requirements:
  - Sponsors: given name + first 2 letters of surname (e.g., "Iryna Sc")
  - Participants: full given name only (column already contains just given names)
- Source data: orders export (TSV file)

**orders-2026-01-27-171230.tsv - Data Structure:**
- 1113 lesson records (+ header)
- Key columns for display:
  - `date_lesson` - lesson date (DD.MM.YYYY format)
  - `timestamp_start_lesson` - ISO8601 start time
  - `timestamp_end_lesson` - ISO8601 end time
  - `level` - lesson type (e.g., "dětská školka", "lyže začátečník")
  - `name_sponsor` - person who booked (apply privacy filter)
  - `name_participant` - participant name (given name only, use as-is)
  - `language` - lesson language (de, cz, pl, en)
  - `location_meeting` - meeting point (e.g., "Stone bar")

**Data Observations:**
- Same booking (id_order) can have multiple participants
- Same participant can have multiple lesson days
- Timestamps include timezone (+01:00)
- Some records have invalid dates (1970-01-01) - need filtering
- Multiple lessons can occur at the same time slot

#### Playbook Comparison

| Aspect | aws-serverless-multirepo | mcp-mono-repo |
|--------|--------------------------|---------------|
| Structure | Multi-repo (5 repos) | Mono-repo |
| Focus | Full serverless apps | Data exploration → MCP |
| Infra | CDK, Lambda, API GW, DynamoDB | Minimal |
| Complexity | High | Low |
| Best for | Complex apps with APIs | Data documentation |

**This project needs:**
- S3 static website for display
- Data processing (TSV → JSON)
- Periodic or triggered refresh
- Simple, focused architecture

**Does NOT need:**
- API Gateway (no real-time API)
- DynamoDB (TSV is source of truth)
- Complex multi-repo structure
- Frontend framework (simple HTML/CSS)

#### Recommendation

**Use aws-serverless-multirepo as base but SIMPLIFY:**
1. Single repo (or orchestration + infrastructure only)
2. S3 static site hosting
3. Lambda for TSV processing
4. CloudWatch Events or S3 trigger for updates
5. Simple HTML/CSS with auto-refresh

**Key architecture:**
```
TSV Upload → S3 → Lambda (process) → JSON → S3 (static site) → Display
                    ↓
              CloudFront (optional)
```

### Next Steps
- Task 0.2: Select playbook template and document rationale
- Document the simplified architecture choice

---

### Task 0.2: Select playbook template and document rationale

#### Selection: aws-serverless-multirepo (SIMPLIFIED)

**Template chosen:** `playbook-aws-serverless-multirepo`

**Why this template:**
1. Uses AWS services we need (S3, Lambda, CDK)
2. Established patterns for static site hosting
3. Infrastructure-as-code with CDK
4. Clear separation of concerns

**Simplifications needed:**
| Original Template | Our Adaptation |
|-------------------|----------------|
| 5 repos (orchestration, infrastructure, backend, frontend, testing) | 2 repos: orchestration + infrastructure |
| API Gateway + Lambda API | Lambda triggered by S3/schedule only |
| DynamoDB | Not needed - TSV is source |
| Full React frontend | Simple HTML/CSS/JS static page |
| Cognito auth | Not needed - public display |

**Rationale for simplification:**
- This is a **read-only display** - no user interaction
- Data source is **file upload** (TSV), not database
- Display is **internal use** - no auth needed
- Complexity should match requirements

#### Architecture Decision

```
┌─────────────────────────────────────────────────────────────────┐
│                     SIMPLIFIED ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐   │
│  │  TSV File   │────▶│  S3 Input   │────▶│  Lambda         │   │
│  │  (upload)   │     │  Bucket     │     │  (process TSV)  │   │
│  └─────────────┘     └─────────────┘     └────────┬────────┘   │
│                                                    │            │
│                                                    ▼            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐   │
│  │  Display    │◀────│ CloudFront  │◀────│  S3 Website     │   │
│  │  (browser)  │     │  (optional) │     │  (HTML + JSON)  │   │
│  └─────────────┘     └─────────────┘     └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**
1. **S3 Input Bucket** - receives TSV uploads
2. **Lambda Processor** - triggered by S3 upload, parses TSV, generates JSON
3. **S3 Website Bucket** - hosts static HTML/CSS/JS + generated JSON
4. **CloudFront** (optional) - caching, HTTPS
5. **Static Page** - auto-refreshes, reads JSON, displays schedule

#### Repository Structure

```
aps-goldsport-scheduler/           # Orchestration (this repo)
├── CLAUDE.md
├── IMPLEMENTATION_PLAN.md
├── progress.json
├── session_notes.md
├── tasks/
└── infrastructure/                # CDK project (nested or separate)
    ├── lib/
    │   └── scheduler-stack.ts
    ├── lambda/
    │   └── process-tsv/
    └── static-site/
        ├── index.html
        ├── styles.css
        └── app.js
```

**Decision: Mono-repo with nested infrastructure**
- Simpler for small project
- Single git history
- Easier context for Claude

### Status
- Task 0.1: COMPLETE
- Task 0.2: COMPLETE
- Current: Ready for Task 0.3
