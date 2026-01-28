# GoldSport Scheduler - Implementation Plan

> **SPECIFICATION ONLY** - This document defines WHAT to build, not HOW to build it.
> Tasks are generated separately via `/generate-phases` and tracked in `progress.json`.

---

## 1. Project Overview

### Description
A scheduling engine for GoldSport ski school that processes lesson bookings, manages instructor assignments, detects conflicts, and provides multiple outputs including a public display. The system is designed to start simple (display) and grow into a full scheduling platform.

### Vision
**Phase 1 (MVP)**: Display current/upcoming lessons on vertical screen
**Future**: Full scheduling engine with instructor assignment, conflict detection, optimization, notifications, and integrations

### Goals

**Immediate (MVP)**:
- Process lesson data from TSV exports
- Display current and upcoming lessons
- Multi-language support (EN/DE/PL/CZ)
- Privacy-compliant name display

**Future (Extensible Architecture)**:
- Automatic instructor assignment suggestions
- Conflict detection (double-bookings, overlaps)
- Schedule optimization
- Notifications (instructors, staff)
- Integration with booking systems

### Success Criteria

**MVP**:
- Display updates within 5 minutes of data upload
- Page readable from 3+ meters distance
- Handles 1000+ lesson records
- Works on vertical display (portrait orientation)

**Architecture**:
- Modular processing pipeline (easy to add new processors)
- State storage for scheduling data
- API-ready for future interactive features

---

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     GOLDSPORT SCHEDULER ENGINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      DATA ACQUISITION                            │   │
│  │                                                                   │   │
│  │   EventBridge          Fetcher Lambda         External Sources   │   │
│  │   (schedule)  ────────▶  (fetch data)  ◀────── • Orders TSV URL  │   │
│  │   every 5 min              │                   • (future sources)│   │
│  │                            ▼                                      │   │
│  │                     ┌──────────────┐    Manual uploads also      │   │
│  │                     │  S3 Input    │◀───── supported (fallback)  │   │
│  │                     │   Bucket     │                              │   │
│  │                     └──────┬───────┘                              │   │
│  └────────────────────────────┼──────────────────────────────────────┘   │
│                               │ S3 trigger                              │
│                               ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    PROCESSING PIPELINE                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │   │
│  │  │  Parse   │─▶│  Merge   │─▶│ Validate │─▶│   Process    │    │   │
│  │  │  & Load  │  │  Data    │  │  & Clean │  │   (future)   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │   │
│  │                                               │                  │   │
│  │  Future processors: ┌─────────────────────────┘                  │   │
│  │  • ConflictDetector │ • InstructorAssigner │ • Optimizer        │   │
│  └─────────────────────┼────────────────────────────────────────────┘   │
│                        ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      STATE STORAGE                               │   │
│  │                      (DynamoDB)                                  │   │
│  │  • Processed schedules  • Conflicts  • Assignment history       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                        │                                                │
│                        ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     OUTPUT LAYER                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │   Display    │  │     API      │  │    Notifications     │  │   │
│  │  │  (S3 + CF)   │  │  (future)    │  │     (future)         │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Infrastructure | AWS CDK (TypeScript) | Define and deploy AWS resources |
| Data Fetcher | Python Lambda + EventBridge | Scheduled fetch from external URLs |
| Processing Engine | Python Lambda | Modular pipeline for data processing |
| State Storage | DynamoDB | Processed schedules, conflicts, history |
| Configuration | S3 (JSON) | Translations, dictionaries, settings |
| Display Output | S3 + CloudFront | Public schedule display |
| API (future) | API Gateway + Lambda | Interactive features |

### Processing Pipeline (Modular Design)

```python
# Conceptual structure - each processor is independent
pipeline = [
    ParseOrdersProcessor(),      # TSV → internal format
    ParseInstructorsProcessor(), # JSON → internal format
    MergeDataProcessor(),        # Combine all sources
    ValidateProcessor(),         # Clean invalid records
    PrivacyProcessor(),          # Apply name filtering
    # Future processors:
    # ConflictDetectorProcessor(),
    # InstructorAssignerProcessor(),
    # OptimizerProcessor(),
]

for processor in pipeline:
    data = processor.process(data)
```

### Data Flow

**MVP Flow**:
1. **EventBridge triggers Fetcher Lambda** on schedule (every 5 minutes)
2. **Fetcher Lambda fetches data from external URLs**:
   - Orders: `http://kurzy.classicskischool.cz/export/export-tsv-2026.php?action=download`
   - (Future: instructors, locations, etc.)
3. **Fetcher Lambda saves data to S3 input bucket** (`orders/orders-{timestamp}.tsv`)
4. **S3 event triggers Processor Lambda**
5. Processor Lambda runs pipeline: Parse → Merge → Validate → Privacy
6. Processor Lambda stores processed schedule in DynamoDB
7. Processor Lambda generates schedule.json → S3 website bucket
8. Display auto-refreshes from S3/CloudFront

**Manual Upload Fallback**:
- Staff can still manually upload files to S3 input bucket
- S3 trigger works the same way regardless of upload source

**Future Flow** (additions):
- Step 5 adds: Conflict Detection → Assignment → Optimization
- Step 7 adds: API endpoints, Notifications

---

## 3. Technical Specifications

### Data Schema

#### Input: TSV Export (Confirmed Columns)
| Column | Type | Example | Used |
|--------|------|---------|------|
| `date_lesson` | DD.MM.YYYY | "28.12.2025" | Yes |
| `timestamp_start_lesson` | ISO8601 | "2025-12-28T09:00:00+01:00" | Yes |
| `timestamp_end_lesson` | ISO8601 | "2025-12-28T10:50:00+01:00" | Yes |
| `level` | string | "dětská školka" | Yes |
| `name_sponsor` | string | "Iryna Schröder" | Yes (privacy filtered) |
| `name_participant` | string | "Vera" | Yes |
| `language` | string | "de", "cz", "en", "pl" | Yes |
| `location_meeting` | string | "Stone bar" | Yes |
| `group_size` | number | 2 | Optional |

#### Output: schedule.json
```json
{
  "generated_at": "2026-01-28T10:30:00+01:00",
  "date": "2026-01-28",
  "data_sources": {
    "orders": "orders-2026-01-28-093000.tsv",
    "roster": "roster-2026-01-28.json",
    "overrides": null
  },
  "current_lessons": [
    {
      "start": "10:00",
      "end": "11:50",
      "level_key": "dětská školka",
      "language_key": "de",
      "location_key": "Stone bar",
      "sponsor": "Iryna Sc",
      "participants": ["Vera", "Eugen", "Gerda"],
      "participant_count": 3,
      "instructor": {
        "id": "jan-novak",
        "name": "Jan Novák",
        "photo": "assets/instructors/jan-novak.jpg"
      },
      "booking_id": "2405020a-b5a4-469e-81ab-18713fc5198a",
      "notes": null
    }
  ],
  "upcoming_lessons": [ ... ]
}
```

**Field sources**:
| Field | Source |
|-------|--------|
| `start`, `end`, `level_key`, `language_key`, `location_key` | orders TSV |
| `sponsor`, `participants` | orders TSV (privacy filtered) |
| `instructor` | instructors/roster + profiles |
| `notes` | schedule-overrides (if any) |

**Note**: The `*_key` fields contain raw values. The frontend looks up translations from dictionaries based on selected language.

### Privacy Rules

| Field | Original | Display Format |
|-------|----------|----------------|
| Sponsor name | "Iryna Schröder" | "Iryna Sc" (given + 2 letters) |
| Participant name | "Vera" | "Vera" (as-is, already given name only) |

### Display Requirements

| Aspect | Specification |
|--------|---------------|
| **Display client** | Windows screensaver-based engine |
| **Protocol** | HTTPS required (CloudFront) |
| Orientation | Portrait (vertical) |
| Font size | Large, readable from 3m |
| Refresh interval | Configurable (default: 60 seconds) |
| Time zones | Europe/Prague (CET/CEST) |
| Current lesson | Highlighted/prominent |
| Language | Czech UI, multilingual lesson data |

### Invalid Data Handling

Records with these characteristics are filtered out:
- `date_lesson` = "01.01.1970" (placeholder dates)
- `timestamp_start_lesson` contains "1970-01-01"
- Missing required fields

---

### Dictionary & Translation System

The system uses configuration files for translations and data enrichment:

#### 1. UI Translations (`config/ui-translations.json`)
Static text for the display interface:
```json
{
  "en": {
    "current_lessons": "Current Lessons",
    "upcoming_lessons": "Upcoming Lessons",
    "no_lessons": "No lessons scheduled",
    "participants": "Participants",
    "instructor": "Instructor"
  },
  "de": {
    "current_lessons": "Aktuelle Kurse",
    "upcoming_lessons": "Kommende Kurse",
    ...
  },
  "cz": { ... },
  "pl": { ... }
}
```

#### 2. Semantic Dictionaries (`config/dictionaries.json`)
Translate data values from TSV:
```json
{
  "levels": {
    "dětská školka": {
      "en": "Kids Ski School",
      "de": "Kinderskischule",
      "cz": "Dětská školka",
      "pl": "Przedszkole narciarskie"
    },
    "lyže začátečník": {
      "en": "Ski Beginner",
      "de": "Ski Anfänger",
      ...
    }
  },
  "languages": {
    "de": { "en": "German", "de": "Deutsch", "cz": "Němčina", "pl": "Niemiecki" },
    "cz": { "en": "Czech", "de": "Tschechisch", ... },
    "en": { "en": "English", ... },
    "pl": { "en": "Polish", ... }
  },
  "locations": {
    "Stone bar": {
      "display_name": { "en": "Stone Bar", "de": "Stone Bar", ... },
      "description": { "en": "Meeting point at Stone Bar terrace", ... }
    }
  }
}
```

#### 3. Static Enrichment (`config/enrichment.json`)
Default values and fallbacks (operational data comes from input bucket):
```json
{
  "defaults": {
    "instructor": {
      "name": "GoldSport Team",
      "photo": "assets/logo.png"
    },
    "location": {
      "name": "Main Meeting Point"
    }
  },
  "display": {
    "show_instructor": true,
    "show_language_flag": true,
    "show_participant_count": true
  }
}
```

**Note**: Instructor assignments and profiles are uploaded to the input bucket (`instructors/` folder), not stored in config. Config only holds defaults and display settings.

### Extensibility Model

The system is designed for future additions:

| Current | Future Possible |
|---------|-----------------|
| Sponsor, participants | + Instructor assignment |
| Level, language | + Difficulty rating |
| Location name | + Location details, map |
| Time slot | + Equipment notes |

**Extension approach**:
1. Add new fields to enrichment.json (no code change)
2. Add translations to dictionaries.json (no code change)
3. Update display template (minor code change)

### Multi-Language Display

| URL | Display Language |
|-----|------------------|
| `/index.html` | Czech (default) |
| `/index.html?lang=de` | German |
| `/index.html?lang=en` | English |
| `/index.html?lang=pl` | Polish |

The frontend loads translations based on `lang` parameter and renders all text accordingly

---

## 4. Implementation Phases

> **NOTE**: These are high-level phases. Detailed tasks are generated via `/generate-phases`
> and tracked in `progress.json`. Do NOT add task lists here.

### Phase 1: Infrastructure Foundation
**Objective**: Set up AWS resources, CDK project, and base architecture

**Deliverables**:
- CDK project initialized with modular stack structure
- S3 buckets (input + website)
- DynamoDB table for schedule state
- Processor Lambda function skeleton with pipeline structure
- Fetcher Lambda for scheduled data acquisition
- EventBridge rule for scheduled triggering (every 5 minutes)
- S3 trigger configured for processor

**Dependencies**: None

---

### Phase 2: Processing Engine (MVP)
**Objective**: Implement core processing pipeline

**Deliverables**:
- Pipeline architecture (processor chain)
- ParseOrdersProcessor (TSV → internal format)
- ParseInstructorsProcessor (JSON → internal format)
- MergeDataProcessor (combine sources)
- ValidateProcessor (filter invalid records)
- PrivacyProcessor (name filtering)
- DynamoDB storage of processed schedule
- schedule.json output generation

**Dependencies**: Phase 1

---

### Phase 3: Configuration & Dictionaries
**Objective**: Implement translation and configuration system

**Deliverables**:
- Dictionary system (ui-translations, semantic dictionaries)
- Configuration loading from S3
- Multi-language key resolution
- Default/fallback handling

**Dependencies**: Phase 2

---

### Phase 4: Display Frontend
**Objective**: Build the multi-language display page

**Deliverables**:
- HTML/CSS for vertical display
- JavaScript for auto-refresh
- Large, readable typography
- Current vs upcoming lesson distinction
- Multi-language support (EN/DE/PL/CZ via ?lang= param)
- Dictionary-based rendering

**Dependencies**: Phase 3

---

### Phase 5: CloudFront & Production
**Objective**: HTTPS delivery (required for display engine)

**Deliverables**:
- CloudFront distribution with HTTPS
- SSL certificate (ACM)
- Cache configuration for schedule.json (short TTL)
- Cache configuration for static assets (long TTL)
- End-to-end testing with display engine
- Monitoring/alerting setup

**Note**: CloudFront is required, not optional. Display engine (Windows screensaver) expects HTTPS URL.

**Dependencies**: Phase 4

---

### Future Phases (Post-MVP)

**Phase 6: Conflict Detection**
- ConflictDetectorProcessor
- Conflict storage in DynamoDB
- Conflict display/alerts

**Phase 7: Instructor Assignment**
- InstructorAssignerProcessor
- Skills/availability matching
- Assignment suggestions

**Phase 8: API Layer**
- API Gateway setup
- CRUD endpoints
- Authentication

**Phase 9: Notifications**
- SNS/SES integration
- Instructor notifications
- Schedule change alerts

---

## 5. AWS Resources

### Resource Naming Convention

**Pattern**: `{project}-{component}-{type}-{env}`

| Element | Values | Example |
|---------|--------|---------|
| `{project}` | `goldsport` | Fixed prefix |
| `{component}` | `scheduler` | Application name |
| `{type}` | `input`, `web`, `proc`, `cdn` | Resource purpose |
| `{env}` | `dev`, `prod` | Environment |

**Full resource names**:

| Resource Type | Name | Example (prod) |
|---------------|------|----------------|
| S3 Input Bucket | `{project}-{component}-input-{env}` | `goldsport-scheduler-input-prod` |
| S3 Website Bucket | `{project}-{component}-web-{env}` | `goldsport-scheduler-web-prod` |
| DynamoDB Table | `{project}-{component}-data-{env}` | `goldsport-scheduler-data-prod` |
| Lambda (Fetcher) | `{project}-{component}-fetcher-{env}` | `goldsport-scheduler-fetcher-prod` |
| Lambda (Processor) | `{project}-{component}-engine-{env}` | `goldsport-scheduler-engine-prod` |
| EventBridge Rule | `{project}-{component}-fetch-schedule-{env}` | `goldsport-scheduler-fetch-schedule-prod` |
| IAM Role (Fetcher) | `{project}-{component}-fetcher-role-{env}` | `goldsport-scheduler-fetcher-role-prod` |
| IAM Role (Processor) | `{project}-{component}-engine-role-{env}` | `goldsport-scheduler-engine-role-prod` |
| CloudFront | `{project}-{component}-cdn-{env}` | `goldsport-scheduler-cdn-prod` |
| CloudWatch Logs | `/aws/lambda/{lambda-name}` | `/aws/lambda/goldsport-scheduler-engine-prod` |

---

### S3 Bucket Structure

#### Input Bucket: `goldsport-scheduler-input-{env}`

```
goldsport-scheduler-input-prod/
│
├── orders/                             # Lesson bookings from booking system
│   └── orders-YYYY-MM-DD-HHMMSS.tsv    # Latest export triggers processing
│
├── instructors/                        # Instructor data
│   ├── roster-YYYY-MM-DD.json          # Daily roster: who's working today
│   └── profiles.json                   # Instructor profiles (names, photos, etc.)
│
├── locations/                          # Location data (optional)
│   └── locations.json                  # Meeting points, descriptions
│
└── schedule-overrides/                 # Manual overrides (optional)
    └── overrides-YYYY-MM-DD.json       # Cancellations, time changes, notes
```

**Data source types**:

| Folder | Format | Trigger | Purpose |
|--------|--------|---------|---------|
| `orders/` | TSV | Yes - triggers Lambda | Main lesson data from booking system |
| `instructors/` | JSON | Yes - triggers Lambda | Instructor assignments and profiles |
| `locations/` | JSON | No - loaded on demand | Location details (optional enrichment) |
| `schedule-overrides/` | JSON | Yes - triggers Lambda | Manual adjustments |

**Processing logic**:
- Lambda triggers on any file upload in `orders/`, `instructors/`, or `schedule-overrides/`
- Lambda reads latest file from each folder
- Combines: orders + instructor assignments + overrides → schedule.json

**Example: instructors/roster-2026-01-28.json**
```json
{
  "date": "2026-01-28",
  "assignments": [
    {
      "instructor_id": "jan-novak",
      "booking_ids": ["2405020a-b5a4-469e-81ab-18713fc5198a"],
      "time_slots": [{"start": "09:00", "end": "12:00"}]
    },
    {
      "instructor_id": "petra-svoboda",
      "booking_ids": ["9ebabe94-626c-48d4-b585-531335c20e3f"],
      "time_slots": [{"start": "13:00", "end": "16:00"}]
    }
  ]
}
```

**Example: instructors/profiles.json**
```json
{
  "jan-novak": {
    "name": "Jan Novák",
    "photo": "assets/instructors/jan-novak.jpg",
    "languages": ["cz", "de", "en"]
  },
  "petra-svoboda": {
    "name": "Petra Svobodová",
    "photo": "assets/instructors/petra-svoboda.jpg",
    "languages": ["cz", "en"]
  }
}
```

---

#### Website Bucket: `goldsport-scheduler-web-{env}`

```
goldsport-scheduler-web-prod/
│
├── index.html                          # Main display page
├── styles.css                          # Styling (vertical display optimized)
├── app.js                              # Auto-refresh, translation logic
│
├── config/                             # Configuration files
│   ├── ui-translations.json            # UI text (EN/DE/PL/CZ)
│   ├── dictionaries.json               # Semantic translations
│   └── enrichment.json                 # Instructors, additional data
│
├── data/                               # Generated data (Lambda output)
│   └── schedule.json                   # Current day's schedule
│
└── assets/                             # Static assets (optional)
    ├── logo.png                        # School logo
    └── instructors/                    # Instructor photos (if used)
        └── {name}.jpg
```

**Access patterns**:
| Path | Updated By | Frequency |
|------|------------|-----------|
| `index.html`, `*.css`, `*.js` | Deployment | Rare |
| `config/*.json` | Manual/Deployment | Occasional |
| `data/schedule.json` | Lambda | On each TSV upload |
| `assets/*` | Manual | Rare |

---

### Resources by Phase

#### Phase 1 Resources
| Type | Name | Purpose |
|------|------|---------|
| S3 Bucket | `goldsport-scheduler-input-{env}` | Receives data uploads |
| S3 Bucket | `goldsport-scheduler-web-{env}` | Static site + config + data |
| DynamoDB | `goldsport-scheduler-data-{env}` | Processed schedules, state |
| Lambda | `goldsport-scheduler-fetcher-{env}` | Fetches data from external URLs |
| Lambda | `goldsport-scheduler-engine-{env}` | Processing pipeline |
| EventBridge | `goldsport-scheduler-fetch-schedule-{env}` | Triggers fetcher every 5 min |
| IAM Role | `goldsport-scheduler-fetcher-role-{env}` | Fetcher Lambda permissions |
| IAM Role | `goldsport-scheduler-engine-role-{env}` | Processor Lambda permissions |

#### Phase 4 Resources
| Type | Name | Purpose |
|------|------|---------|
| CloudFront | `goldsport-scheduler-cdn-{env}` | CDN for website bucket |
| ACM Certificate | (auto-generated) | HTTPS for CloudFront |

#### Future Resources (not in MVP)
| Type | Name | Purpose |
|------|------|---------|
| API Gateway | `goldsport-scheduler-api-{env}` | REST API for interactive features |
| Lambda | `goldsport-scheduler-api-handler-{env}` | API request handlers |
| SNS/SES | `goldsport-scheduler-notify-{env}` | Notifications |

---

### DynamoDB Schema

**Table**: `goldsport-scheduler-data-{env}`

```
Primary Key: PK (partition key), SK (sort key)

Item Types:
┌─────────────────┬──────────────────┬────────────────────────────────┐
│ PK              │ SK               │ Purpose                        │
├─────────────────┼──────────────────┼────────────────────────────────┤
│ SCHEDULE#date   │ META             │ Schedule metadata for date     │
│ SCHEDULE#date   │ LESSON#id        │ Individual lesson record       │
│ CONFLICT#date   │ CONFLICT#id      │ Detected conflict (future)     │
│ INSTRUCTOR#id   │ PROFILE          │ Instructor profile             │
│ INSTRUCTOR#id   │ ASSIGN#date      │ Assignment for date            │
└─────────────────┴──────────────────┴────────────────────────────────┘
```

**Example: Schedule item**
```json
{
  "PK": "SCHEDULE#2026-01-28",
  "SK": "LESSON#abc123",
  "start": "10:00",
  "end": "11:50",
  "level_key": "dětská školka",
  "instructor_id": "jan-novak",
  "participants": ["Vera", "Eugen"],
  "booking_id": "2405020a-..."
}
```

---

### IAM Permissions (Lambda Roles)

**Fetcher Lambda Role** (`goldsport-scheduler-fetcher-role-{env}`):
```yaml
Permissions:
  # Write fetched data to input bucket
  - s3:PutObject on goldsport-scheduler-input-{env}/*

  # Logging
  - logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
```

**Processor Lambda Role** (`goldsport-scheduler-engine-role-{env}`):
```yaml
Permissions:
  # Read all input sources
  - s3:GetObject on goldsport-scheduler-input-{env}/*
  - s3:ListBucket on goldsport-scheduler-input-{env}

  # Read config, write data output
  - s3:GetObject on goldsport-scheduler-web-{env}/config/*
  - s3:PutObject on goldsport-scheduler-web-{env}/data/*

  # DynamoDB full access to scheduler table
  - dynamodb:GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan
    on goldsport-scheduler-data-{env}

  # Logging
  - logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
```

---

### External Data Sources

The Fetcher Lambda retrieves data from external URLs on a schedule.

| Source | URL | Format | Schedule |
|--------|-----|--------|----------|
| Orders | `http://kurzy.classicskischool.cz/export/export-tsv-2026.php?action=download` | TSV | Every 5 min |

**Configuration**: Data source URLs are stored in environment variables on the Fetcher Lambda, allowing updates without code changes.

**Future Sources** (can be added via env vars):
- Instructor roster URL (if available)
- Location data URL (if available)
- Override/cancellation feeds

**Fetcher Lambda behavior**:
1. Read source URLs from environment variables
2. HTTP GET each configured URL
3. Save response to S3 input bucket with timestamped filename
4. S3 trigger then invokes Processor Lambda

---

### CloudFront: Required for HTTPS

**Why CloudFront is required**:
- Display engine is Windows screensaver-based
- Screensaver expects HTTPS URL
- S3 website hosting only supports HTTP
- CloudFront provides SSL/TLS termination

**CloudFront provides**:
| Feature | Benefit |
|---------|---------|
| **HTTPS** | Required - display engine expects secure URL |
| Caching | Reduces S3 requests, faster page loads |
| Custom domain | Use your own domain (e.g., schedule.goldsport.cz) |

---

### Estimated Operational Costs (Monthly)

**Assumptions**:
- ~1000 lessons/day in peak season
- 5-10 data uploads per day
- 1 display refreshing every 60 seconds (1440 requests/day)
- ~100KB schedule.json, ~50KB static files

#### Detailed Breakdown

| Resource | Usage | Unit Cost | Monthly Cost |
|----------|-------|-----------|--------------|
| **S3 Storage** | ~10 MB total | $0.023/GB | ~$0.01 |
| **S3 Requests** | ~50K GET/month | $0.0004/1K | ~$0.02 |
| **S3 PUT** | ~300/month | $0.005/1K | ~$0.01 |
| **DynamoDB Write** | ~10K/month | $1.25/1M | ~$0.01 |
| **DynamoDB Read** | ~50K/month | $0.25/1M | ~$0.01 |
| **Lambda Invocations** | ~300/month | Free tier (1M) | $0.00 |
| **Lambda Compute** | ~30 sec total | Free tier (400K GB-sec) | $0.00 |
| **CloudFront** (if used) | ~5 GB/month | Free tier (1TB) | $0.00 |
| **CloudWatch Logs** | ~100 MB | $0.50/GB | ~$0.05 |

#### Summary

| Scenario | Monthly Cost |
|----------|--------------|
| **Without CloudFront** | **~$0.10 - $0.50** |
| **With CloudFront** | **~$0.10 - $0.50** (free tier) |
| **After free tier expires** | **~$1 - $2** |

**Note**: AWS Free Tier (12 months) covers most of this usage. Even after free tier, costs are minimal for this scale.

#### Off-Season vs Peak Season

| Period | Uploads/day | Display refreshes | Est. Cost |
|--------|-------------|-------------------|-----------|
| Off-season | 0-1 | 0 (display off) | ~$0.05 |
| Peak season | 5-10 | 1440 | ~$0.50 |

---

## 6. Repository Structure

### Strategy: Mono-Repository

```
aps-goldsport-scheduler/           # Single repository
├── CLAUDE.md                      # Project instructions
├── IMPLEMENTATION_PLAN.md         # This spec
├── progress.json                  # Task tracking
├── session_notes.md               # Session history
├── tasks/                         # Task details by phase
│   ├── phase_1_infrastructure.md
│   ├── phase_2_processing.md
│   ├── phase_3_frontend.md
│   └── phase_4_cdn.md
├── input/                         # Input materials (gitignored after setup)
│   └── orders-*.tsv
├── config/                        # Configuration & translations
│   ├── ui-translations.json       # UI text in all languages
│   ├── dictionaries.json          # Semantic translations (levels, etc.)
│   └── enrichment.json            # Additional data (instructors, etc.)
├── infrastructure/                # CDK project
│   ├── bin/
│   │   └── app.ts
│   ├── lib/
│   │   └── scheduler-stack.ts
│   ├── cdk.json
│   ├── package.json
│   └── tsconfig.json
├── lambda/                        # Lambda source
│   ├── fetcher/                   # Data acquisition Lambda
│   │   ├── handler.py
│   │   └── requirements.txt
│   └── processor/                 # Processing pipeline Lambda
│       ├── handler.py
│       └── requirements.txt
└── static-site/                   # Frontend
    ├── index.html
    ├── styles.css
    └── app.js
```

### Git Workflow
| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code |
| `feature/*` | New features (if needed) |

---

## 7. Naming Conventions

### AWS Resources
**Pattern**: `{project}-{component}-{type}-{env}`

| Type | Pattern | Example |
|------|---------|---------|
| S3 Buckets | `goldsport-scheduler-{type}-{env}` | `goldsport-scheduler-web-prod` |
| Lambda | `goldsport-scheduler-proc-{env}` | `goldsport-scheduler-proc-prod` |
| IAM Role | `goldsport-scheduler-lambda-role-{env}` | `goldsport-scheduler-lambda-role-prod` |
| CloudFront | `goldsport-scheduler-cdn-{env}` | `goldsport-scheduler-cdn-prod` |

### S3 Object Keys

**Input Bucket**:
| Folder | Pattern | Example |
|--------|---------|---------|
| Orders | `orders/orders-{timestamp}.tsv` | `orders/orders-2026-01-28-120000.tsv` |
| Roster | `instructors/roster-{date}.json` | `instructors/roster-2026-01-28.json` |
| Profiles | `instructors/profiles.json` | `instructors/profiles.json` |
| Locations | `locations/locations.json` | `locations/locations.json` |
| Overrides | `schedule-overrides/overrides-{date}.json` | `schedule-overrides/overrides-2026-01-28.json` |

**Website Bucket**:
| Folder | Pattern | Example |
|--------|---------|---------|
| Static files | `{file}` | `index.html`, `app.js` |
| Config | `config/{name}.json` | `config/dictionaries.json` |
| Generated data | `data/schedule.json` | `data/schedule.json` |
| Assets | `assets/{path}` | `assets/instructors/jan-novak.jpg` |

### Code
| Type | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `process-tsv.py` |
| Functions | snake_case (Python) | `parse_lesson_row` |
| Classes | PascalCase | `ScheduleProcessor` |
| Constants | SCREAMING_SNAKE | `DEFAULT_REFRESH_INTERVAL` |
| Config keys | snake_case | `ui_translations`, `current_lessons` |

### Git Commits
```
{type}: {description}

Types: feat, fix, docs, refactor, test, chore, infra
```

---

## 8. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-28 | Mono-repo structure | Simple project, single deployment unit |
| 2026-01-28 | Python for Lambda | Better TSV/data processing libraries |
| 2026-01-28 | ~~S3 trigger (not scheduled)~~ | ~~Updates only when new data uploaded~~ |
| 2026-01-28 | CloudFront for CDN | HTTPS, caching, professional delivery |
| 2026-01-28 | JSON config for translations | No code changes needed to add languages/terms |
| 2026-01-28 | Keys in schedule.json | Frontend handles translation, allows runtime language switch |
| 2026-01-28 | **Scheduling engine architecture** | Not just display - needs processing logic, extensibility |
| 2026-01-28 | **DynamoDB for state** | Store processed schedules, conflicts, assignments for future features |
| 2026-01-28 | **Modular pipeline** | Easy to add processors (conflict, assignment) without rewriting |
| 2026-01-28 | **Multiple input sources** | Orders, instructors, overrides as separate uploads |
| 2026-01-28 | **Timer-based Fetcher Lambda** | Orders data available via HTTP export URL - automated fetch every 5 min instead of manual upload. Two-Lambda architecture (Fetcher + Processor) keeps concerns separated. S3 trigger still works for manual uploads as fallback. |
| 2026-01-28 | **EventBridge for scheduling** | Standard AWS service for scheduled Lambda invocation |

---

## 9. Scope Boundaries

### MVP Scope (Phases 1-5)
- Display current/upcoming lessons
- Multi-language support
- Modular architecture ready for extensions

### Future Scope (Phases 6+)
- Instructor assignment (manual from input files, then automatic)
- Conflict detection
- API for interactive features
- Notifications

### Out of Scope (Not Planned)
- User authentication for display (public)
- Booking system integration (manual upload only)
- Mobile native app (web responsive only)
- Multi-tenant (single ski school)
