# Architecture Documentation

## Diagram

![Classic Ski School Scheduler Architecture](goldsport_scheduler_architecture.png)

## Overview

The Classic Ski School Scheduler is a serverless AWS application that:
1. **Fetches** lesson data from external booking system at scheduled times
2. **Processes** ALL lessons (~3 weeks) through pipeline (parse, deduplicate, validate, privacy filter)
3. **Generates** schedule.json with all dates (frontend reads this directly)
4. **Displays** lessons on vertical screens via CloudFront

## Components

| Component | AWS Resource | Purpose |
|-----------|--------------|---------|
| EventBridge | 14 scheduled rules | Triggers data fetch at specific times |
| Fetcher Lambda | `goldsport-scheduler-fetcher-dev` | Fetches TSV from external API (~3 weeks of bookings) |
| Input Bucket | `goldsport-scheduler-input-dev` | Stores raw TSV files |
| Processor Lambda | `goldsport-scheduler-engine-dev` | Processes ALL lessons, regenerates schedule.json |
| DynamoDB | `goldsport-scheduler-data-dev` | Versioned backup storage (unused by frontend) |
| Web Bucket | `goldsport-scheduler-web-dev` | Hosts static site + schedule.json |
| CloudFront | Distribution E1UECZ9R3RFNX | HTTPS delivery, caching |

## Data Flow

```
External API ──(~3 weeks TSV)──> Fetcher Lambda ──> S3 Input
                                                      │
                                                      ▼ (S3 trigger)
                                              Processor Lambda
                                              (regenerates ALL)
                                                      │
                              ┌────────────────┬──────┴──────┐
                              ▼                ▼              ▼
                          DynamoDB      schedule.json     S3 Web
                          (backup)      (all dates)    (static site)
                                              │
                                              ▼
                                         CloudFront
                                              │
                                              ▼
                                           Display
```

## Fetch Schedule

Data is fetched at **14 specific times** (CET) aligned with lesson start times:

| Time (CET) | UTC Cron | Purpose |
|------------|----------|---------|
| 06:00 | `cron(0 5 * * ? *)` | Morning start |
| 08:55 | `cron(55 7 * * ? *)` | Before 09:00 lessons |
| 09:00 | `cron(0 8 * * ? *)` | 09:00 lessons start |
| 09:05 | `cron(5 8 * * ? *)` | After 09:00 lessons |
| 10:00 | `cron(0 9 * * ? *)` | Mid-morning |
| 10:05 | `cron(5 9 * * ? *)` | Mid-morning |
| 10:55 | `cron(55 9 * * ? *)` | Before 11:00 lessons |
| 12:55 | `cron(55 11 * * ? *)` | Before 13:00 lessons |
| 13:00 | `cron(0 12 * * ? *)` | 13:00 lessons start |
| 13:05 | `cron(5 12 * * ? *)` | After 13:00 lessons |
| 14:25 | `cron(25 13 * * ? *)` | Before 14:30 lessons |
| 14:30 | `cron(30 13 * * ? *)` | 14:30 lessons start |
| 14:35 | `cron(35 13 * * ? *)` | After 14:30 lessons |
| 17:25 | `cron(25 16 * * ? *)` | End of day |

**DST Note:** Times are in UTC. Adjust cron expressions after daylight saving changes:
- Last Sunday March: CET → CEST (UTC+1 → UTC+2)
- Last Sunday October: CEST → CET (UTC+2 → UTC+1)

## Processing Pipeline

```
ParseOrders → Deduplicate → ParseInstructors → MergeData → Validate → Privacy → Storage → Output
```

| Processor | Purpose |
|-----------|---------|
| ParseOrders | Parse TSV, filter invalid dates (1970), group into lessons |
| Deduplicate | Remove duplicate orders (same person, same time, different order_id) |
| ParseInstructors | Parse instructor assignments (if available) |
| MergeData | Merge orders with instructor data |
| Validate | Validate required fields, time formats |
| Privacy | Filter names: sponsor → "Ir.Sc.", participant → as-is |
| Storage | Write to DynamoDB with versioned keys |
| Output | Generate schedule.json for frontend |

## Key Points

- **Processor regenerates ALL schedules** each run (not just today)
- **schedule.json** contains `all_lessons_by_date` with every date from TSV
- **DynamoDB** is versioned backup storage for future API use (frontend doesn't query it)
- **Frontend** reads schedule.json directly via CloudFront, refreshes every 60 seconds

## Regenerating Diagram

```bash
python3 docs/architecture/generate.py
```

Requirements:
- `pip3 install diagrams`
- `apt-get install graphviz`
