# Phase 3: Configuration & Dictionaries

**Objective**: Implement translation and configuration system

**Repos involved**: orchestration (this repo - mono-repo)

---

## Tasks

### 3.1 Create UI Translations File
**Size**: small

Create `config/ui-translations.json` with all UI text.

**Languages**: en, de, cz, pl

**Content**:
- current_lessons, upcoming_lessons
- no_lessons, participants, instructor
- time labels, headers

**Verify**: JSON is valid, all 4 languages have same keys

---

### 3.2 Create Semantic Dictionaries File
**Size**: medium

Create `config/dictionaries.json` with data translations.

**Content**:
- Level translations (dětská školka → Kids Ski School, etc.)
- Language code translations (de → German/Deutsch, etc.)
- Location translations (if needed)

**Verify**: JSON is valid, covers all known level values from TSV

---

### 3.3 Create Enrichment Config File
**Size**: small

Create `config/enrichment.json` with defaults and display settings.

**Content**:
```json
{
  "defaults": {
    "instructor": { "name": "GoldSport Team" },
    "location": { "name": "Main Meeting Point" }
  },
  "display": {
    "show_instructor": true,
    "show_language_flag": true,
    "show_participant_count": true
  }
}
```

**Verify**: JSON is valid

---

### 3.4 Implement Config Loader in Lambda
**Size**: small

Add config loading from S3 website bucket.

**Logic**:
- Load config files on Lambda cold start
- Cache in memory for warm invocations
- Handle missing files gracefully (use defaults)

**Verify**: Lambda can read config files from S3

---

### 3.5 Upload Config Files to S3
**Size**: small

Deploy config files to website bucket.

**Steps**:
1. Upload to `s3://goldsport-scheduler-web-dev/config/`
2. Verify files accessible

**Verify**: Files exist in S3, Lambda can read them

---

### 3.6 Update schedule.json with Translation Keys
**Size**: small

Ensure schedule.json uses `*_key` fields for translation.

**Fields**:
- `level_key` (raw value from TSV)
- `language_key` (raw value from TSV)
- `location_key` (raw value from TSV)

Frontend will translate these using dictionaries.

**Verify**: schedule.json contains *_key fields

---

## Dependencies

```
3.1 ──┬──▶ 3.5
3.2 ──┤
3.3 ──┘
      │
3.4 ──┴──▶ 3.6
```

---

## Phase Completion Criteria

- [ ] All config files created and valid
- [ ] Config files uploaded to S3
- [ ] Lambda loads config successfully
- [ ] schedule.json uses translation keys
- [ ] All known TSV values have translations
