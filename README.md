# Classic Ski School Scheduler

Scheduling engine for Classic Ski School Harrachov - processes lesson bookings from external booking system and displays them on vertical screens.

## Live URL

- **Production**: https://d2uodie4uj65pq.cloudfront.net
- **With language**: https://d2uodie4uj65pq.cloudfront.net?lang=de (de/en/cz/pl)
- **Debug mode**: https://d2uodie4uj65pq.cloudfront.net?debug=true&date=29.01.2026

## Architecture

![Classic Ski School Scheduler Architecture](docs/architecture/goldsport_scheduler_architecture.png)

See [Architecture Documentation](docs/architecture/README.md) for details.

---

## Data Refresh Schedule

Data is fetched at **14 specific times** aligned with lesson start times (CET):

```
06:00  08:55  09:00  09:05  10:00  10:05  10:55
12:55  13:00  13:05  14:25  14:30  14:35  17:25
```

### Changing the Schedule

Edit `infrastructure/lib/scheduler-stack.ts`:

```typescript
const fetchTimes = [
  { name: '0600', cron: 'cron(0 5 * * ? *)', desc: '06:00 CET' },
  // ... add/remove/modify times
];
```

Then deploy:
```bash
cd infrastructure
AWS_PROFILE=JiHy__vsb__299 npx cdk deploy
```

**Important:** Cron times are in **UTC**. CET = UTC+1 (winter), CEST = UTC+2 (summer).

### DST Adjustment

After daylight saving changes, update UTC times in the cron expressions:
- **Last Sunday March** (CET → CEST): Subtract 1 hour from UTC times
- **Last Sunday October** (CEST → CET): Add 1 hour to UTC times

---

## Data Processing

### Source Data

- **URL**: `http://kurzy.classicskischool.cz/export/export-tsv-2026.php?action=download`
- **Format**: TSV with ~1100 records (~3 weeks of bookings)
- **Fetched by**: Fetcher Lambda → stored in S3

### Processing Pipeline

```
TSV → ParseOrders → Deduplicate → Validate → Privacy → Storage → schedule.json
```

### Known Data Quality Issues

The source booking system has data quality issues that require preprocessing:

1. **Duplicate Orders**: Same participant + sponsor + time appears with multiple `order_id` values
   - **Solution**: Keep only the record with the highest (latest) `order_id`
   - **Code**: `_deduplicate_orders()` in `parse_orders.py`

2. **Invalid Dates**: Some records have `1970-01-01` dates
   - **Solution**: Filter out records with year < 2000
   - **Code**: `_filter_valid_records()` in `parse_orders.py`

### Lesson Grouping Logic

| Lesson Type | Grouping Key | Behavior |
|-------------|--------------|----------|
| **Private** (`privát`) | `order_id + start_time` | Each booking separate, even from same sponsor |
| **Small Group** (`malá skupina`) | `date + start + level + type + location` | All matching people grouped together |
| **Large Group** (`velká skupina`) | `date + start + level + type + location` | All matching people grouped together |

### Privacy Filtering

| Field | Rule | Example |
|-------|------|---------|
| Sponsor name | First 2 letters of each name | "Iryna Schröder" → "Ir.Sc." |
| Participant name | As-is (already just first name) | "Anna" → "Anna" |

---

## Frontend

### Display Format

```
Thursday, 29.1.2026 14:15:30

Schedule for Thursday, 30.01.2026. 11 lessons scheduled.

09:00-10:50 | Private | Kids Ski | Stone Bar | Anna 🇩🇪 (Ir.Sc.) | GoldSport Team
```

### Auto-Refresh

- Frontend refreshes data every **60 seconds**
- "Schedule updated" shows when Lambda generated the data

---

## Page Rotation System

When multiple time slots have lessons, the display rotates between pages automatically.

### Time Slots

| Slot | Lessons Starting | Main Display Window |
|------|------------------|---------------------|
| 09:00 | 08:00-09:59 | 08:00-10:00 |
| 11:00 | 11:00-11:59 | 10:00-12:00 |
| 13:00 | 13:00-13:59 | 12:00-14:00 |
| 14:30 | 14:30+ | 14:00-17:00 |

### Display Timing

| Slot Position | Duration | Description |
|---------------|----------|-------------|
| **Current** | 15 seconds | Main slot (current time window) |
| **Previous** | 3 seconds | Slots before current |
| **Upcoming** | 10 seconds | Slots after current |

### Visual Indicators

- **Page indicator**: Dots at bottom showing current page
- **Active page**: White dot (larger)
- **Main slot**: Yellow border on dot
- **Main slot cards**: Dark background with yellow text

### Changing Rotation Parameters

Edit `static-site/app.js`:

**Time Slots** (lines ~17-52):
```javascript
const TIME_SLOTS = [
    {
        id: 1,
        label: '09:00',
        startRange: { min: 480, max: 599 },  // minutes from midnight
        mainWindow: { min: 480, max: 599 },
    },
    // ... add/modify slots
];
```

**Display Timing** (lines ~55-60):
```javascript
const ROTATION_CONFIG = {
    currentDuration: 15000,    // 15 seconds for current/main slot
    previousDuration: 3000,    // 3 seconds for previous slots
    upcomingDuration: 10000,   // 10 seconds for upcoming slots
    transitionDuration: 300,   // 300ms fade transition
};
```

After editing, deploy to both buckets:
```bash
# Dev/CloudFront bucket
AWS_PROFILE=JiHy__vsb__299 aws s3 cp static-site/app.js s3://goldsport-scheduler-web-dev/app.js

# Hot/embedded bucket
AWS_PROFILE=JiHy__vsb__299 aws s3 cp static-site/app.js s3://medite-ss1-infgsp-299025166536/classicskischoolharrachov/schedule/app.js

# Invalidate CloudFront
AWS_PROFILE=JiHy__vsb__299 aws cloudfront create-invalidation --distribution-id E1UECZ9R3RFNX --paths /app.js
```

---

### Languages

URL parameter `?lang=xx`:
- `cz` - Czech (default)
- `de` - German
- `en` - English
- `pl` - Polish

### Debug Mode

Add `?debug=true` to enable:
- Time slider to simulate different times
- Date selector (+7/-14 days)
- Useful for testing without waiting for real data

---

## Project Structure

```
aps-goldsport-scheduler/
├── infrastructure/          # AWS CDK (TypeScript)
│   └── lib/scheduler-stack.ts  # All AWS resources defined here
├── lambda/
│   ├── fetcher/            # Data acquisition Lambda
│   │   └── handler.py      # Fetches TSV from external URL
│   └── processor/          # Processing pipeline Lambda
│       ├── handler.py      # Entry point
│       ├── pipeline.py     # Pipeline orchestration
│       └── processors/     # Individual processors
│           ├── parse_orders.py    # TSV parsing, deduplication, grouping
│           ├── validate.py        # Field validation
│           ├── privacy.py         # Name filtering
│           ├── storage.py         # DynamoDB write
│           └── output.py          # schedule.json generation
├── static-site/            # Frontend (HTML/CSS/JS)
│   ├── index.html
│   ├── styles.css
│   └── app.js              # All frontend logic
├── config/                 # Translations & dictionaries
│   ├── ui-translations.json    # UI text (4 languages)
│   └── dictionaries.json       # Level/location translations
└── docs/                   # Documentation
```

---

## Development

### Prerequisites

- AWS CLI configured with `JiHy__vsb__299` profile
- Node.js 18+ for CDK
- Python 3.11 for Lambda

### Deploy Infrastructure

```bash
cd infrastructure
npm install
AWS_PROFILE=JiHy__vsb__299 npx cdk deploy
```

### Upload Static Site

```bash
AWS_PROFILE=JiHy__vsb__299 aws s3 sync static-site/ s3://goldsport-scheduler-web-dev/ \
  --exclude "*.md"
```

### Upload Config Files

```bash
AWS_PROFILE=JiHy__vsb__299 aws s3 sync config/ s3://goldsport-scheduler-web-dev/config/
```

### Invalidate CloudFront Cache

```bash
AWS_PROFILE=JiHy__vsb__299 aws cloudfront create-invalidation \
  --distribution-id E1UECZ9R3RFNX \
  --paths "/*"
```

### Manual Data Fetch

```bash
AWS_PROFILE=JiHy__vsb__299 aws lambda invoke \
  --function-name goldsport-scheduler-fetcher-dev \
  --payload '{}' /tmp/response.json
```

---

## AWS Resources

| Resource | Name | Region |
|----------|------|--------|
| Account | 299025166536 | eu-central-1 |
| Input Bucket | `goldsport-scheduler-input-dev` | |
| Web Bucket | `goldsport-scheduler-web-dev` | |
| DynamoDB | `goldsport-scheduler-data-dev` | |
| Fetcher Lambda | `goldsport-scheduler-fetcher-dev` | |
| Processor Lambda | `goldsport-scheduler-engine-dev` | |
| CloudFront | E1UECZ9R3RFNX | Global |

---

## Troubleshooting

### Data not updating

1. Check if EventBridge rules are enabled:
   ```bash
   AWS_PROFILE=JiHy__vsb__299 aws events list-rules --name-prefix goldsport-scheduler-fetch
   ```

2. Check Fetcher Lambda logs:
   ```bash
   AWS_PROFILE=JiHy__vsb__299 aws logs tail /aws/lambda/goldsport-scheduler-fetcher-dev --follow
   ```

3. Manually trigger fetch:
   ```bash
   AWS_PROFILE=JiHy__vsb__299 aws lambda invoke --function-name goldsport-scheduler-fetcher-dev --payload '{}' /tmp/out.json
   ```

### Wrong lesson count

Check deduplication logs in Processor Lambda:
```bash
AWS_PROFILE=JiHy__vsb__299 aws logs tail /aws/lambda/goldsport-scheduler-engine-dev --since 1h
```

Look for: "Removed X records from older duplicate orders"

### Frontend not showing latest data

1. Check schedule.json timestamp:
   ```bash
   AWS_PROFILE=JiHy__vsb__299 aws s3api head-object --bucket goldsport-scheduler-web-dev --key data/schedule.json
   ```

2. Invalidate CloudFront cache (see above)

3. Hard refresh browser (Ctrl+Shift+R)
