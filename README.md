# Classic Ski School Scheduler

Scheduling engine for Classic Ski School Harrachov - processes lesson bookings, manages schedules, and provides display output for vertical screens.

## Architecture

![Classic Ski School Scheduler Architecture](docs/architecture/goldsport_scheduler_architecture.png)

See [Architecture Documentation](docs/architecture/README.md) for details.

## Live URL

- **Production**: https://d2uodie4uj65pq.cloudfront.net
- **With language**: https://d2uodie4uj65pq.cloudfront.net?lang=de
- **Debug mode**: https://d2uodie4uj65pq.cloudfront.net?debug=true

## Features

- Auto-fetch lesson data every 5 minutes
- Multi-language support (CZ, DE, EN, PL)
- Privacy-compliant name display
- Time-slot color coding
- Optimized for vertical display screens

## Project Structure

```
aps-goldsport-scheduler/
├── infrastructure/     # AWS CDK (TypeScript)
├── lambda/
│   ├── fetcher/       # Data acquisition Lambda
│   └── processor/     # Processing pipeline Lambda
├── static-site/       # Frontend (HTML/CSS/JS)
├── config/            # Translations & dictionaries
└── docs/              # Documentation
```

## Development

### Deploy Infrastructure
```bash
cd infrastructure
npm install
npx cdk deploy
```

### Upload Static Site
```bash
aws s3 sync static-site/ s3://goldsport-scheduler-web-dev/
```

### Regenerate Architecture Diagram
```bash
python3 docs/architecture/generate.py
```
