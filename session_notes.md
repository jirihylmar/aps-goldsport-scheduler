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

---

## Session 3 - 2026-01-28

### Phase 2: Processing Engine Implementation

**Task 2.1: Create pipeline architecture** - COMPLETE
- Created `processors/__init__.py` with Processor base class and ProcessorError
- Created `pipeline.py` with Pipeline orchestrator and PipelineBuilder
- Updated `handler.py` to use pipeline structure

**Task 2.2: Implement ParseOrdersProcessor** - COMPLETE
- Parses TSV orders from S3
- Filters invalid records (1970 dates, missing fields)
- Groups records by booking_id and time slot
- 5 unit tests

**Task 2.3: Implement ParseInstructorsProcessor** - COMPLETE
- Parses roster and profiles JSON
- Helper function for instructor lookup
- 4 unit tests

**Task 2.4: Implement MergeDataProcessor** - COMPLETE
- Merges orders with instructor assignments
- Default instructor fallback
- 5 unit tests

**Task 2.5: Implement ValidateProcessor** - COMPLETE
- Validates required fields and time formats
- 8 unit tests

**Task 2.6: Implement PrivacyProcessor** - COMPLETE
- Sponsor: given name + first 2 letters surname
- Participants: unchanged (already given names)
- 8 unit tests

**Task 2.7: Implement DynamoDB storage** - COMPLETE
- Stores lessons grouped by date
- Batch writes for efficiency
- 8 unit tests (including fix for duplicate key issue)

**Task 2.8: Implement JSON output generation** - COMPLETE
- Generates schedule.json with current/upcoming separation
- Wired up all processors in handler.py
- 7 unit tests

**Task 2.9: Integration test with real data** - COMPLETE
- Deployed Lambda with `cdk deploy`
- Uploaded real TSV (1113 records)
- Verified: 579 lessons parsed, 616 DynamoDB items stored
- schedule.json generated in website bucket
- Privacy applied correctly: "Iryna Schröder" → "Iryna Sc"

---

## Phase 2 COMPLETE

### Summary
- 7 processors implemented and tested
- 45 unit tests passing
- End-to-end integration test successful
- Lambda deployed and operational

### Pipeline Flow
```
S3 Upload → ParseOrders → ParseInstructors → MergeData → Validate → Privacy → Storage → Output
```

### Next Session
- Phase 3: Configuration & Dictionaries
- Start with Task 3.1: Create UI translations file

### Status
- Phase 0: COMPLETE
- Phase 1: COMPLETE
- Phase 2: COMPLETE
- Phase 3: COMPLETE
- Phase 4: COMPLETE
- Phase 5: IN PROGRESS (5/9 tasks)
- Debug URL: https://d2uodie4uj65pq.cloudfront.net?debug=true&date=28.01.2026&time=09:30
- Current Task: 5.5

---

## Session 4 - 2026-01-28 (continued)

### Phase 3: Configuration & Dictionaries

**Task 3.1: Create UI translations file** - COMPLETE
- Created `config/ui-translations.json`
- 16 UI keys in 4 languages (en, de, cz, pl)

**Task 3.2: Create semantic dictionaries file** - COMPLETE
- Created `config/dictionaries.json`
- Levels: 6 (kids ski school, ski/snowboard beginner/advanced, cross-country)
- Languages: 4 (en, de, cz, pl)
- Locations: 2 (Rýžoviště, Stone bar)

**Task 3.3: Create enrichment config file** - COMPLETE
- Created `config/enrichment.json`
- Default instructor, display settings, sample instructors

**Task 3.4: Implement config loader in Lambda** - COMPLETE
- Created `lambda/processor/config_loader.py`
- ConfigLoader class loads configs from S3
- translate() and get_ui_text() helper functions
- 15 unit tests

**Task 3.5: Upload config files to S3** - COMPLETE
- Uploaded to s3://goldsport-scheduler-web-dev/config/
  - ui-translations.json (2.4 KiB)
  - dictionaries.json (1.8 KiB)
  - enrichment.json (720 B)

**Task 3.6: Verify *_key fields in schedule.json** - COMPLETE
- OutputProcessor already includes level_key, language_key, location_key

---

## Phase 3 COMPLETE

### Summary
- 3 config files created and uploaded to S3
- Config loader implemented with translation helpers
- 60 total unit tests passing (15 new for config loader)

---

## Phase 4 COMPLETE - 2026-01-28

### Tasks Completed
- 4.1: HTML structure (index.html)
- 4.2: CSS for vertical display (styles.css)
- 4.3-4.7: JavaScript application (app.js)
- 4.8: Uploaded to S3
- 4.9: Frontend ready, needs CloudFront

### Summary
- Display frontend built with HTML/CSS/JS
- Multi-language support (?lang=de/en/pl/cz)
- Auto-refresh every 60 seconds
- Uploaded to S3, awaiting CloudFront for public access

### Next Session
- Phase 5: CloudFront & Production
- Start with Task 5.1: Add CloudFront distribution to CDK

---

## Session 5 - 2026-01-28

### Phase 6 Added: UI/UX Improvements

User requested extensive UI tuning work via `/add-work` command.

**Key requirements identified:**
1. Passive display (screensaver mode) - no scrolling, no interaction
2. All content must fit on one page OR auto-rotate
3. Language-specific views
4. Data grouping issues (kids school not grouped correctly)
5. Sponsor display decisions needed
6. Distinguish participant language vs lesson language
7. Format and layout tuning throughout

**Tasks created:**
| ID | Task | Size |
|----|------|------|
| 6.1 | Analyze display requirements | small |
| 6.2 | Implement page rotation system | medium |
| 6.3 | Language-specific views | medium |
| 6.4 | Fix data grouping issues | medium |
| 6.5 | Sponsor display decision | small |
| 6.6 | Participant language indicator | small |
| 6.7 | Format and layout tuning | medium |
| 6.8 | Implement no-scroll safeguards | small |

**Files created:**
- `tasks/phase_6_ui_tuning.md` - detailed task descriptions
- Updated `progress.json` with Phase 6

### Status
- Phase 0-4: COMPLETE
- Phase 5: IN PROGRESS (5/9 tasks, current: 5.5)
- Phase 6: PENDING (8 tasks added)
- Debug URL: https://d2uodie4uj65pq.cloudfront.net?debug=true&date=28.01.2026&time=09:30

---

## Session 6 - 2026-01-28

### Phase 6: UI/UX Improvements - Compact Card Layout

**Task 6.1: Analyze display requirements** - COMPLETE
- Created `docs/display-analysis.md` with screen capacity analysis
- Screen: 1080x1920 portrait, current cards ~280px = only 4 visible
- Max lessons at same time: 17 concurrent lessons possible
- Recommendation: compact cards + page rotation

**Task 6.4: Fix data grouping issues** - COMPLETE
- Changed grouping from `booking_id` to `date + start + level + location`
- All same-type lessons now grouped together (e.g., kids school 09:00-10:50 at Stone Bar)
- Updated: parse_orders.py, merge_data.py, storage.py

**Task 6.5: Sponsor display decision** - COMPLETE
- Format: "Ir.Sc." (first 2 letters of given name + first 2 letters of surname)
- Shown per-person in parentheses: "Anna 🇩🇪 (Ir.Sc.)"
- Updated: privacy.py `_filter_sponsor_name()`

**Task 6.6: Participant language indicator** - COMPLETE
- Per-person language flags instead of per-lesson
- Data model changed: `people: [{name, language, sponsor}, ...]`
- Format: "Anna 🇩🇪 (Ir.Sc.), Max 🇬🇧 (Ma.Mü.)"
- Updated: parse_orders.py, privacy.py, merge_data.py, validate.py, storage.py, output.py, app.js

**Implemented compact 3-line card layout:**
```
11:00-12:50 | Ski Beginner | 2 | Stone Bar
Lily 🇨🇿 (An.Hr.), Amy 🇨🇿 (An.Hr.)
Instructor: GoldSport Team
```

**Files modified:**
- `lambda/processor/processors/parse_orders.py` - grouping logic, people array
- `lambda/processor/processors/privacy.py` - Ir.Sc. sponsor format
- `lambda/processor/processors/merge_data.py` - people field passthrough
- `lambda/processor/processors/validate.py` - people validation
- `lambda/processor/processors/storage.py` - new ID generation
- `lambda/processor/processors/output.py` - people in output
- `static-site/index.html` - compact card template
- `static-site/styles.css` - compact styles
- `static-site/app.js` - formatParticipant function

**Bugs fixed:**
- DynamoDB BatchWriteItem duplicate key error - fixed lesson ID to use new grouping fields
- Lambda not deploying in time - waited for update status before triggering

### Status
- Phase 0-4: COMPLETE
- Phase 5: IN PROGRESS (5/9 tasks)
- Phase 6: IN PROGRESS (4/8 tasks: 6.1✓, 6.4✓, 6.5✓, 6.6✓)
- Current task: 6.2 (page rotation)
- Test URL: https://d2uodie4uj65pq.cloudfront.net?debug=true&date=02.01.2026&time=11:00

---

## Session 7 - 2026-01-28

### Major UI Overhaul

**Task 6.6a: Add group_type to data model** - COMPLETE
- Added `group_type` field (privát, malá skupina, velká skupina)
- Updated dictionaries.json with translations for all 4 languages
- Changed grouping key to: `date + start + level + group_type + location`
- Updated processors: parse_orders.py, merge_data.py, storage.py, output.py

**Task 6.7: Format and layout tuning** - IN PROGRESS
Implemented single-page layout with many iterations:

1. **Single-line cards with pipe separators**
   - Format: `11:00-12:50 | Private | Kids Ski | Stone Bar | Anna CZ (Ir.Sc.) | Instructor`
   - Cards flow left-to-right, wrap to next line

2. **Time-slot colors** (border-left + background)
   - 08:00-09:59: Blue (#e3f2fd)
   - 10:00-11:59: Green (#e8f5e9)
   - 12:00-13:59: Yellow (#fff8e1)
   - 14:00-15:59: Pink (#fce4ec)
   - 16:00+: Purple (#f3e5f5)

3. **Time breaks** - New line between different start times

4. **Font sizing** - Reduced 50%, then increased 30%
   - Base: 16px, Large: 21px, Small: 13px

5. **Tested and rejected:**
   - Emoji symbols for group types (👤👤👤) - looked bad
   - Colored label badges - too busy
   - Max-width cards - uneven layout

6. **Deferred:** Graphics tuning for later phase

**Task 5.4b: Add date selector to debug mode (+7/-14 days)** - COMPLETE
- Debug banner shows 21 clickable date buttons
- 7 days ahead (green background) + today + 14 days back
- "Today" label for current day
- Active state highlighting for selected date
- Easy inspection of historical and future schedules

**Cross-browser flag fix:**
- Chrome/Windows doesn't render flag emojis natively
- Implemented Twemoji (Twitter's emoji library)
- Flags now render as SVG images across all browsers
- Added `<script src="https://cdn.jsdelivr.net/npm/@twemoji/api@latest/dist/twemoji.min.js">`

### Files Modified
- `config/dictionaries.json` - added group_types translations
- `lambda/processor/processors/parse_orders.py` - group_type field, grouping key
- `lambda/processor/processors/merge_data.py` - group_type_key passthrough
- `lambda/processor/processors/storage.py` - updated ID generation
- `lambda/processor/processors/output.py` - group_type_key output
- `static-site/app.js` - flags via Twemoji, 14-day selector, time breaks, hide GoldSport Team instructor
- `static-site/index.html` - Twemoji script, pipe-separated template
- `static-site/styles.css` - time-slot colors, compact layout, emoji sizing

### Status
- Phase 0-4: COMPLETE
- Phase 5: IN PROGRESS (6/10 tasks: 5.1-5.4a✓, 5.4b✓)
- Phase 6: IN PROGRESS (5/9 tasks: 6.1✓, 6.4✓, 6.5✓, 6.6✓, 6.6a✓, 6.7 in progress)
- Test URL: https://d2uodie4uj65pq.cloudfront.net?debug=true&date=02.01.2026

**Bug fixes:**
- Fixed date fallback: When user selects future date with no data, show "No lessons" instead of wrong data
- Removed duplicate date selector from footer (now only in debug banner)

### Commits This Session
| Hash | Description |
|------|-------------|
| f947f31 | Session 7: UI overhaul + group_type + debug enhancements |
| d1208ad | fix: Show empty state for dates with no data |
| deb07f3 | Remove duplicate date selector from footer |

### Next Steps
- Deploy Lambda with updated processors (group_type changes)
- Continue 6.7 (format tuning) when graphics phase begins
- Consider 6.2 (rotation) if content doesn't fit single page

---

## Session 8 - 2026-01-29

### Phase 6 Complete - UI/UX Improvements

**Task 6.3: Language-specific views** - COMPLETE
- Removed language switcher buttons from header
- Added datetime display: "Čtvrtek, 29.1.2026 08:01"
- Day names translate based on `?lang=` parameter (cz/cs, de, en, pl)
- Language is now URL-only: `?lang=xx`

**Task 6.2, 6.7, 6.8** - Marked COMPLETE
- Page rotation deferred (single-page layout sufficient)
- Format tuning complete with current layout
- No-scroll safeguards already in place (CSS overflow:hidden)

**Branding changes:**
- Header: "GoldSport Ski School" → "Classic Ski School Harrachov"
- Page title: "Scheduler - Classic Ski School - production"

### Files Modified
- `static-site/index.html` - datetime display, title, branding
- `static-site/styles.css` - removed language button styles
- `static-site/app.js` - DAY_NAMES translations, updateDateTimeDisplay()

### Status
- Phase 0-4: COMPLETE
- Phase 5: IN PROGRESS (4/8 tasks remaining: 5.5, 5.6, 5.7, 5.8)
- Phase 6: IN PROGRESS (3 new branding tasks added)
- Live URL: https://d2uodie4uj65pq.cloudfront.net

### Work Added
- 6.9: Apply company theme CSS
- 6.10: Add company logo to header
- 6.11: Apply dark background layout
- Source: User request to align with aps-goldsport-booking branding
- Reference: /home/hylmarj/aps-goldsport-booking/src/styles/company-theme.css

### Branding Implementation
**Tasks 6.9-6.11 completed:**
- Company theme CSS: Inter font, yellow #ffed00, dark #1a1a1a
- Background image: vyuka-bg-4.jpg from booking app S3
- Header: datetime only (no logo), semi-transparent overlay
- Content section: 85% opacity with backdrop blur (frosted glass)
- Increased margins/padding throughout
- Default language changed to English

### Architecture Diagram
- Created docs/architecture/generate.py
- Generated goldsport_scheduler_architecture.png
- Added root README.md

### Commits This Session
| Hash | Description |
|------|-------------|
| 57701cf | Session 8: Phase 6 complete - UI/UX improvements done |
| 7e7d73d | Add architecture diagram and README |
| b154dbc | Apply company branding - yellow/dark theme with logo |
| f693298 | Header: centered logo (bigger) with time underneath |
| d660c3a | Use background image, remove logo |
| 81c90ea | Increase margins, translucent content section |
| ed5ee5c | Default language changed to English |
| 0842874 | Content section: 85% opacity + blur effect |

### Status
- Phase 0-5: See below
- Phase 6: COMPLETE (all 12 tasks)
- Phase 7: PENDING (4 tasks added)
- Live URL: https://d2uodie4uj65pq.cloudfront.net

### Phase 7 Added: Data & Storage Improvements
**Tasks:**
- 7.1: Change private lesson grouping to use order_id
- 7.2: Clean current DynamoDB entries
- 7.3: Add versioning to DynamoDB storage
- 7.4: Reprocess data with new logic

**Reason:** Private lessons need separate grouping - one sponsor can have multiple independent private lessons at same time. Also adding DynamoDB versioning to keep historical snapshots.
