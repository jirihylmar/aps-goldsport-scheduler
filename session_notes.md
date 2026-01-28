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

---

### Task 0.3: Draft IMPLEMENTATION_PLAN.md sections 1-3

Created IMPLEMENTATION_PLAN.md with:

**Section 1 - Project Overview:**
- Description: Web display for ski school lessons
- Goals: Current/upcoming lessons, auto-refresh, privacy
- Success criteria: 5-min update, readable from 3m, handles 1000+ records

**Section 2 - Architecture:**
- Data flow: TSV → S3 → Lambda → JSON → S3 Website → Display
- Components: CDK, Python Lambda, HTML/CSS/JS, S3, CloudFront

**Section 3 - Technical Specifications:**
- Input schema: TSV columns mapped
- Output schema: schedule.json format
- Privacy rules: sponsor = given + 2 letters, participant = as-is
- Display requirements: portrait, large font, 60s refresh

---

### Task 0.4: Draft IMPLEMENTATION_PLAN.md sections 4-7

Completed IMPLEMENTATION_PLAN.md with:

**Section 4 - Implementation Phases:**
- Phase 1: Infrastructure Foundation (CDK, S3, Lambda skeleton)
- Phase 2: Data Processing (TSV parsing, JSON generation)
- Phase 3: Display Frontend (HTML/CSS/JS)
- Phase 4: CDN & Polish (CloudFront, HTTPS)

**Section 5 - AWS Resources:**
- Naming: goldsport-{component}-{env}
- Input bucket, website bucket, Lambda, IAM role
- CloudFront for production
- Estimated cost: < $5/month

**Section 6 - Repository Structure:**
- Mono-repo with infrastructure/, lambda/, static-site/
- Task files in tasks/

**Section 7 - Naming Conventions:**
- Code: kebab-case files, snake_case functions
- AWS: goldsport-{purpose}-{env}

**Section 8 - Decision Log:**
- Documented key architecture decisions

**Section 9 - Out of Scope:**
- No auth, no data entry, no history, web only

---

### Task 0.5: Spec Review - Revision 1

**User feedback:**
- Need more robust architecture for future development
- Multi-language support (EN/DE/PL/CZ)
- Semantic dictionaries for data translation (levels, etc.)
- Extensibility for additional data (instructors, locations)

**Changes made:**
1. Added Dictionary & Translation System section
   - ui-translations.json for UI text
   - dictionaries.json for semantic translations (levels, languages, locations)
   - enrichment.json for additional data (instructors)

2. Updated output schema
   - Uses `*_key` fields for raw values
   - Frontend handles translation based on selected language

3. Added multi-language display
   - URL parameter ?lang=de/en/pl/cz
   - Default: Czech

4. Updated repository structure
   - Added config/ folder for all configuration files

5. Updated phases
   - Phase 2 includes dictionary system
   - Phase 3 includes multi-language rendering

6. Added extensibility model documentation

### Status
- Task 0.1: COMPLETE
- Task 0.2: COMPLETE
- Task 0.3: COMPLETE
- Task 0.4: COMPLETE
- Current: Task 0.5 - awaiting user approval (revision 1)
