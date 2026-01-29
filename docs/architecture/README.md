# Architecture Documentation

## Diagram

![Classic Ski School Scheduler Architecture](goldsport_scheduler_architecture.png)

## Overview

The Classic Ski School Scheduler is a serverless AWS application that:
1. **Fetches** lesson data from external booking system (every 5 minutes)
2. **Processes** data through a modular pipeline (parse, validate, privacy filter)
3. **Stores** processed schedules in DynamoDB
4. **Displays** lessons on vertical screens via CloudFront

## Components

| Component | AWS Resource | Purpose |
|-----------|--------------|---------|
| EventBridge | Scheduled rule (5 min) | Triggers data fetch |
| Fetcher Lambda | `goldsport-scheduler-fetcher-dev` | Fetches TSV from external API |
| Input Bucket | `goldsport-scheduler-input-dev` | Stores raw data files |
| Processor Lambda | `goldsport-scheduler-engine-dev` | Processes data through pipeline |
| DynamoDB | `goldsport-scheduler-data-dev` | Stores processed schedules |
| Web Bucket | `goldsport-scheduler-web-dev` | Hosts static site + JSON |
| CloudFront | Distribution | HTTPS delivery, caching |

## Data Flow

```
External API → Fetcher Lambda → S3 Input → Processor Lambda → DynamoDB
                                                           ↓
                                              S3 Web → CloudFront → Display
```

## Regenerating

To regenerate the diagram:
```bash
python3 docs/architecture/generate.py
```

Requirements:
- `pip3 install diagrams`
- `apt-get install graphviz`
