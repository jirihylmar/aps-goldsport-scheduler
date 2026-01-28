# GoldSport Scheduler - Implementation Plan

> **SPECIFICATION ONLY** - This document defines WHAT to build, not HOW to build it.
> Tasks are generated separately via `/generate-phases` and tracked in `progress.json`.

---

## 1. Project Overview

### Description
A web-based display system for GoldSport ski school that shows current and upcoming lessons on an external vertical display. The system processes lesson data from TSV exports and presents it in a readable format optimized for vertical orientation.

### Goals
- Display current lessons in progress
- Show upcoming lessons for the current day
- Auto-refresh at configurable intervals
- Protect participant privacy (given name only)
- Protect sponsor privacy (given name + 2-letter surname)
- Simple deployment via file upload

### Success Criteria
- Display updates within 5 minutes of TSV upload
- Page readable from 3+ meters distance
- Handles 1000+ lesson records without performance issues
- Works on vertical display (portrait orientation)

---

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DATA FLOW                                  │
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
│  │  (browser)  │     │  (CDN)      │     │  (HTML + JSON)  │   │
│  └─────────────┘     └─────────────┘     └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Infrastructure | AWS CDK (TypeScript) | Define and deploy AWS resources |
| Data Processing | Python Lambda | Parse TSV, apply enrichment, generate JSON |
| Configuration | JSON files | Translations, dictionaries, enrichment data |
| Static Site | HTML/CSS/JS | Multi-language display on vertical screen |
| Storage | S3 | Input bucket + website hosting + config |
| CDN | CloudFront | HTTPS, caching, fast delivery |

### Data Flow

1. Staff uploads TSV export to S3 input bucket
2. S3 event triggers Lambda function
3. Lambda parses TSV, filters to current date
4. Lambda applies dictionaries (translations, enrichment)
5. Lambda writes schedule.json to S3 website bucket
6. Display page loads with language parameter (?lang=de)
7. Page renders using UI translations for selected language

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
  "current_lessons": [
    {
      "start": "10:00",
      "end": "11:50",
      "level_key": "dětská školka",
      "language_key": "de",
      "location_key": "Stone bar",
      "sponsor": "Iryna Sc",
      "participants": ["Vera", "Eugen", "Gerda"],
      "instructor": "Jan Novák",
      "booking_id": "2405020a-b5a4-469e-81ab-18713fc5198a"
    }
  ],
  "upcoming_lessons": [ ... ]
}
```

**Note**: The `*_key` fields contain raw values from TSV. The frontend looks up translations from dictionaries based on selected language.

### Privacy Rules

| Field | Original | Display Format |
|-------|----------|----------------|
| Sponsor name | "Iryna Schröder" | "Iryna Sc" (given + 2 letters) |
| Participant name | "Vera" | "Vera" (as-is, already given name only) |

### Display Requirements

| Aspect | Specification |
|--------|---------------|
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

#### 3. Enrichment Data (`config/enrichment.json`)
Additional data not in TSV (managed separately):
```json
{
  "instructors": {
    "booking_id_or_pattern": {
      "name": "Jan Novák",
      "photo": "instructors/jan.jpg"
    }
  },
  "default_instructor": {
    "name": "GoldSport Team"
  }
}
```

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
**Objective**: Set up AWS resources and CDK project

**Deliverables**:
- CDK project initialized
- S3 buckets (input + website)
- Lambda function skeleton
- S3 trigger configured

**Dependencies**: None

---

### Phase 2: Data Processing & Configuration
**Objective**: Implement TSV parsing, dictionaries, and JSON generation

**Deliverables**:
- Lambda function parses TSV
- Privacy filtering applied
- Dictionary system (ui-translations, semantic dictionaries)
- Enrichment data structure (instructors, etc.)
- schedule.json generated with keys for translation
- Handles edge cases (invalid dates, missing fields)

**Dependencies**: Phase 1

---

### Phase 3: Display Frontend
**Objective**: Build the multi-language display page

**Deliverables**:
- HTML/CSS for vertical display
- JavaScript for auto-refresh
- Large, readable typography
- Current vs upcoming lesson distinction
- Multi-language support (EN/DE/PL/CZ via ?lang= param)
- Dictionary-based rendering (levels, languages, locations)

**Dependencies**: Phase 2

---

### Phase 4: CDN & Polish
**Objective**: Production readiness

**Deliverables**:
- CloudFront distribution
- HTTPS enabled
- Cache configuration
- End-to-end testing

**Dependencies**: Phase 3

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
| Lambda Function | `{project}-{component}-proc-{env}` | `goldsport-scheduler-proc-prod` |
| IAM Role | `{project}-{component}-lambda-role-{env}` | `goldsport-scheduler-lambda-role-prod` |
| CloudFront | `{project}-{component}-cdn-{env}` | `goldsport-scheduler-cdn-prod` |
| CloudWatch Logs | `/aws/lambda/{lambda-name}` | `/aws/lambda/goldsport-scheduler-proc-prod` |

---

### S3 Bucket Structure

#### Input Bucket: `goldsport-scheduler-input-{env}`

```
goldsport-scheduler-input-prod/
└── uploads/
    └── orders-YYYY-MM-DD-HHMMSS.tsv    # Uploaded TSV files
```

- TSV files uploaded here trigger Lambda processing
- Old files can be retained or lifecycle-deleted (configurable)

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
| S3 Bucket | `goldsport-scheduler-input-{env}` | Receives TSV uploads |
| S3 Bucket | `goldsport-scheduler-web-{env}` | Static site + config + data |
| Lambda | `goldsport-scheduler-proc-{env}` | Processes TSV → JSON |
| IAM Role | `goldsport-scheduler-lambda-role-{env}` | Lambda execution permissions |

#### Phase 4 Resources
| Type | Name | Purpose |
|------|------|---------|
| CloudFront | `goldsport-scheduler-cdn-{env}` | CDN for website bucket |
| ACM Certificate | (auto-generated) | HTTPS for CloudFront |

---

### IAM Permissions (Lambda Role)

```yaml
Permissions:
  - s3:GetObject on goldsport-scheduler-input-{env}/*
  - s3:PutObject on goldsport-scheduler-web-{env}/data/*
  - s3:GetObject on goldsport-scheduler-web-{env}/config/*
  - logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
```

---

### Estimated Costs (Monthly)
| Resource | Estimate |
|----------|----------|
| S3 (storage + requests) | < $1 |
| Lambda | < $1 (minimal invocations) |
| CloudFront | < $1 (low traffic) |
| **Total** | **< $5/month** |

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
│   └── processor/
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
| Location | Pattern | Example |
|----------|---------|---------|
| Input uploads | `uploads/{filename}.tsv` | `uploads/orders-2026-01-28-120000.tsv` |
| Generated data | `data/{filename}.json` | `data/schedule.json` |
| Config files | `config/{name}.json` | `config/dictionaries.json` |
| Static assets | `assets/{path}` | `assets/logo.png` |

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
| 2026-01-28 | S3 trigger (not scheduled) | Updates only when new data uploaded |
| 2026-01-28 | No database | TSV is source of truth, regenerate on each upload |
| 2026-01-28 | CloudFront for CDN | HTTPS, caching, professional delivery |
| 2026-01-28 | JSON config for translations | No code changes needed to add languages/terms |
| 2026-01-28 | Enrichment file for instructors | Decouples instructor assignment from TSV |
| 2026-01-28 | Keys in schedule.json | Frontend handles translation, allows runtime language switch |

---

## 9. Out of Scope

The following are explicitly NOT part of this implementation:
- User authentication (public display)
- Data entry/editing (read-only from TSV)
- Historical data storage (only current day shown)
- Mobile app (web only)
- Multi-location support (single display endpoint)
