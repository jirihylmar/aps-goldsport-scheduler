# Phase 2: Processing Engine (MVP)

**Objective**: Implement core processing pipeline with modular architecture

**Repos involved**: orchestration (this repo - mono-repo)

---

## Tasks

### 2.1 Create Pipeline Architecture
**Size**: small

Set up the modular pipeline structure in Lambda code.

**Files**:
- `lambda/processor/handler.py` - Main entry point
- `lambda/processor/pipeline.py` - Pipeline orchestration
- `lambda/processor/processors/__init__.py` - Processor base class

**Structure**:
```python
class Processor:
    def process(self, data: dict) -> dict:
        raise NotImplementedError

class Pipeline:
    def __init__(self, processors: list[Processor]):
        self.processors = processors

    def run(self, data: dict) -> dict:
        for processor in self.processors:
            data = processor.process(data)
        return data
```

**Verify**: `handler.py` imports pipeline, basic structure works

---

### 2.2 Implement ParseOrdersProcessor
**Size**: medium

Parse TSV orders file into internal format.

**Input**: TSV file from S3
**Output**: List of lesson records

**Key logic**:
- Read TSV with proper encoding (UTF-8)
- Parse date/time fields
- Filter invalid records (1970 dates)
- Group by booking_id for participant lists

**Verify**: Unit test with sample TSV data passes

---

### 2.3 Implement ParseInstructorsProcessor
**Size**: small

Parse instructor roster and profiles JSON.

**Input**: JSON files from S3
**Output**: Instructor assignments and profiles dict

**Verify**: Unit test with sample JSON passes

---

### 2.4 Implement MergeDataProcessor
**Size**: medium

Combine orders with instructor assignments.

**Logic**:
- Match lessons to instructors by booking_id
- Apply default instructor if no match
- Combine into unified lesson records

**Verify**: Unit test with combined data passes

---

### 2.5 Implement ValidateProcessor
**Size**: small

Clean and validate merged data.

**Logic**:
- Remove records with missing required fields
- Validate date/time formats
- Log warnings for invalid records

**Verify**: Unit test filters invalid records correctly

---

### 2.6 Implement PrivacyProcessor
**Size**: small

Apply privacy rules to names.

**Logic**:
- Sponsor: given name + first 2 letters of surname
- Participant: use as-is (already given name only)

**Verify**: Unit test transforms names correctly

---

### 2.7 Implement DynamoDB Storage
**Size**: medium

Store processed schedule in DynamoDB.

**Logic**:
- Write schedule metadata (SCHEDULE#date / META)
- Write individual lessons (SCHEDULE#date / LESSON#id)
- Use batch writes for efficiency

**Verify**: Data appears in DynamoDB after Lambda run

---

### 2.8 Implement JSON Output Generation
**Size**: small

Generate schedule.json for website bucket.

**Logic**:
- Filter to current date
- Separate current vs upcoming lessons
- Include metadata (generated_at, data_sources)
- Write to S3 website bucket

**Verify**: schedule.json appears in website bucket after upload

---

### 2.9 Integration Test with Real Data
**Size**: medium

Test full pipeline with actual TSV data.

**Steps**:
1. Upload sample orders TSV to input bucket
2. Verify Lambda triggered
3. Check DynamoDB has records
4. Check schedule.json in website bucket
5. Validate JSON structure

**Verify**: End-to-end flow works with real data

---

## Dependencies

```
2.1 ──▶ 2.2 ──┬──▶ 2.4 ──▶ 2.5 ──▶ 2.6 ──▶ 2.7 ──▶ 2.8 ──▶ 2.9
         │    │
         └────┤
2.1 ──▶ 2.3 ──┘
```

---

## Phase Completion Criteria

- [ ] All processors implemented and tested
- [ ] Pipeline runs without errors
- [ ] DynamoDB populated correctly
- [ ] schedule.json generated with correct structure
- [ ] Privacy rules applied correctly
- [ ] Invalid records filtered
