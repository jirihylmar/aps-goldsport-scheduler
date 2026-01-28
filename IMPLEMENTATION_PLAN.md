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
| Data Processing | Python Lambda | Parse TSV, generate schedule JSON |
| Static Site | HTML/CSS/JS | Display schedule on vertical screen |
| Storage | S3 | Input bucket + website hosting |
| CDN | CloudFront | HTTPS, caching, fast delivery |

### Data Flow

1. Staff uploads TSV export to S3 input bucket
2. S3 event triggers Lambda function
3. Lambda parses TSV, filters to current date, generates JSON
4. Lambda writes schedule.json to S3 website bucket
5. Display page auto-refreshes, fetches schedule.json
6. Page renders current and upcoming lessons

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
      "level": "dětská školka",
      "language": "de",
      "location": "Stone bar",
      "sponsor": "Iryna Sc",
      "participants": ["Vera", "Eugen", "Gerda"]
    }
  ],
  "upcoming_lessons": [
    {
      "start": "13:00",
      "end": "14:20",
      "level": "lyže začátečník",
      "language": "cz",
      "location": "Stone bar",
      "sponsor": "Jana Sc",
      "participants": ["George"]
    }
  ]
}
```

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

### Phase 2: Data Processing
**Objective**: Implement TSV parsing and JSON generation

**Deliverables**:
- Lambda function parses TSV
- Privacy filtering applied
- schedule.json generated
- Handles edge cases (invalid dates, missing fields)

**Dependencies**: Phase 1

---

### Phase 3: Display Frontend
**Objective**: Build the display page

**Deliverables**:
- HTML/CSS for vertical display
- JavaScript for auto-refresh
- Large, readable typography
- Current vs upcoming lesson distinction

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
```
goldsport-{component}-{env}
```

Where:
- `{component}`: input, website, processor, cdn
- `{env}`: dev, prod

### Resources by Phase

#### Phase 1 Resources
| Type | Name | Purpose |
|------|------|---------|
| S3 Bucket | goldsport-input-{env} | Receives TSV uploads |
| S3 Bucket | goldsport-website-{env} | Hosts static site + JSON |
| Lambda | goldsport-processor-{env} | Processes TSV files |
| IAM Role | goldsport-lambda-role-{env} | Lambda execution permissions |

#### Phase 4 Resources
| Type | Name | Purpose |
|------|------|---------|
| CloudFront | goldsport-cdn-{env} | CDN for website |
| ACM Certificate | (auto-generated) | HTTPS |

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

### Code
| Type | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `process-tsv.py` |
| Functions | snake_case (Python) | `parse_lesson_row` |
| Classes | PascalCase | `ScheduleProcessor` |
| Constants | SCREAMING_SNAKE | `DEFAULT_REFRESH_INTERVAL` |

### AWS Resources
| Type | Pattern | Example |
|------|---------|---------|
| S3 Buckets | goldsport-{purpose}-{env} | goldsport-website-prod |
| Lambda | goldsport-{function}-{env} | goldsport-processor-prod |
| CloudFront | goldsport-cdn-{env} | goldsport-cdn-prod |

### Commits
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

---

## 9. Out of Scope

The following are explicitly NOT part of this implementation:
- User authentication (public display)
- Data entry/editing (read-only from TSV)
- Historical data storage (only current day shown)
- Mobile app (web only)
- Multi-location support (single display endpoint)
