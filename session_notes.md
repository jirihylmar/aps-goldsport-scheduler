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

---

### Task 0.5: Spec Approval - APPROVED

**Revisions made before approval:**
1. Added multi-language support (EN/DE/PL/CZ) with dictionary system
2. Redesigned as scheduling engine (not just display)
3. Added modular processing pipeline
4. Added DynamoDB for state storage
5. Multiple input sources (orders, instructors, overrides)
6. CloudFront required (display engine expects HTTPS)
7. Detailed cost analysis (~$0.10-0.50/month)

**Final architecture:**
- Input: S3 (orders/, instructors/, locations/, schedule-overrides/)
- Processing: Lambda with modular pipeline
- State: DynamoDB (schedules, conflicts, assignments)
- Output: S3 + CloudFront (HTTPS)
- Display: Windows screensaver-based engine

**User approved**: 2026-01-28

---

### Task 0.6: Create project CLAUDE.md - COMPLETE
- AWS Account: 299025166536 (eu-central-1)
- MCP Tool: mcp__aws-vsb-299__call_aws

### Task 0.7: Generate Phase 1 tasks - COMPLETE
- 7 tasks for Infrastructure Foundation

### Task 0.8: Generate remaining phase tasks - COMPLETE
- Phase 2: Processing Engine (9 tasks)
- Phase 3: Configuration (6 tasks)
- Phase 4: Frontend (9 tasks)
- Phase 5: Production (8 tasks)
- Total: 39 implementation tasks

### Task 0.9: Remove examples repo - COMPLETE
- syndicate-playbooks-examples/ removed
- .gitignore updated for project use

---

## Phase 0 COMPLETE

### Summary
- Implementation spec approved
- 5 phases defined with 39 tasks
- Project ready for implementation

### Next Session
- Start with Task 1.1: Initialize CDK project
- Phase 1: Infrastructure Foundation

### Status
- Phase 0: COMPLETE
- Phase 1: PENDING (next)
- Current Task: 1.1

---

## Session 2 - 2026-01-28

### Discussion: Architecture Change - Timer-Based Data Fetching

**Issue raised**: Original plan assumed manual S3 uploads for orders data. However, orders data is available via HTTP export:
```
http://kurzy.classicskischool.cz/export/export-tsv-2026.php?action=download
```

**Tested**: URL returns fresh TSV data directly (verified with curl).

**Architectural Decision**: Two-Lambda architecture (Option A)
1. **Fetcher Lambda** - scheduled via EventBridge, fetches from external URLs, saves to S3
2. **Processor Lambda** - triggered by S3, processes data through pipeline

**Benefits**:
- Automated data refresh (no manual uploads needed)
- Extensible for additional data sources
- Consistent refresh schedule (every 5 minutes)
- S3 trigger still works for manual uploads (fallback)

### Changes Made

**IMPLEMENTATION_PLAN.md**:
- Updated architecture diagram with Data Acquisition layer
- Added Fetcher Lambda and EventBridge to Components table
- Updated Data Flow to show automated fetch process
- Updated Phase 1 deliverables
- Added Fetcher Lambda, EventBridge rule to resource tables
- Added External Data Sources section documenting URLs
- Updated IAM Permissions for both Lambda roles
- Added decision to Decision Log

**progress.json**:
- Renamed task 1.5 to "Create Processor Lambda skeleton"
- Added task 1.5a: Create Fetcher Lambda skeleton
- Added task 1.5b: Create EventBridge schedule rule
- Updated task 1.7 dependencies to include 1.5b

**tasks/phase_1_infrastructure.md**:
- Added task 1.5a with Fetcher Lambda details and sample code
- Added task 1.5b with EventBridge CDK code
- Updated dependency diagram
- Updated completion criteria

### Phase 1 Tasks (Updated)

| ID | Task | Status |
|----|------|--------|
| 1.1 | Initialize CDK project | pending |
| 1.2 | Create S3 input bucket | pending |
| 1.3 | Create S3 website bucket | pending |
| 1.4 | Create DynamoDB table | pending |
| 1.5 | Create Processor Lambda skeleton | pending |
| 1.5a | Create Fetcher Lambda skeleton | pending |
| 1.5b | Create EventBridge schedule rule | pending |
| 1.6 | Configure S3 trigger | pending |
| 1.7 | Deploy and verify infrastructure | pending |

### Status
- Phase 0: COMPLETE
- Phase 1: PENDING (updated with new tasks)
- Current Task: 1.1

---

### Phase 1 Implementation

**Task 1.1: Initialize CDK project** - COMPLETE
- Created `infrastructure/` with CDK TypeScript project
- Created `scheduler-stack.ts` with environment configuration
- Configured for eu-central-1, account 299025166536

**Tasks 1.2, 1.3, 1.4** - COMPLETE (parallel)
- S3 input bucket: `goldsport-scheduler-input-dev`
- S3 website bucket: `goldsport-scheduler-web-dev`
- DynamoDB table: `goldsport-scheduler-data-dev`

**Task 1.5: Processor Lambda skeleton** - COMPLETE
- `lambda/processor/handler.py` with basic S3 event handling
- Environment: DATA_TABLE, WEBSITE_BUCKET, INPUT_BUCKET

**Task 1.5a: Fetcher Lambda skeleton** - COMPLETE
- `lambda/fetcher/handler.py` with HTTP fetch and S3 save logic
- Environment: INPUT_BUCKET, ORDERS_URL (configured with export URL)

**Task 1.5b: EventBridge schedule rule** - COMPLETE
- `goldsport-scheduler-fetch-schedule-dev`
- Rate: every 5 minutes
- Target: Fetcher Lambda

**Task 1.6: S3 trigger** - COMPLETE
- S3 notifications on input bucket for prefixes: orders/, instructors/, schedule-overrides/
- Target: Processor Lambda

**Task 1.7: Deploy and verify** - COMPLETE
- `cdk deploy` successful
- All resources verified via MCP tools

---

## Phase 1 COMPLETE

### Deployed Resources
| Resource | Name |
|----------|------|
| S3 Input | goldsport-scheduler-input-dev |
| S3 Website | goldsport-scheduler-web-dev |
| DynamoDB | goldsport-scheduler-data-dev |
| Fetcher Lambda | goldsport-scheduler-fetcher-dev |
| Processor Lambda | goldsport-scheduler-engine-dev |
| EventBridge Rule | goldsport-scheduler-fetch-schedule-dev (rate 5 min) |

### Next Session
- Phase 2: Processing Engine
- Start with Task 2.1: Create pipeline architecture

### Status
- Phase 0: COMPLETE
- Phase 1: COMPLETE
- Phase 2: PENDING (next)
- Current Task: 2.1
