# Phase 6: UI/UX Improvements

## Overview
Tune the display for passive screen usage (screensaver mode). The display must work without user interaction - no scrolling, no clicking, no manual manipulation.

## Key Constraints
- **Passive display**: Screensaver mode - no user interaction possible
- **All content must fit**: Either on one page, or rotate automatically
- **Multi-language**: Each language may need its own dedicated page/rotation
- **Readability**: Large fonts, high contrast, visible from 3+ meters

---

## Task 6.1: Analyze Display Requirements

**Objective**: Determine how many lessons fit on vertical display at current font sizes

**Steps**:
1. Count current lesson cards that fit on 1080x1920 vertical screen
2. Measure with real data - how many concurrent lessons typical?
3. Document constraints for rotation logic

**Verify**: Analysis document with max lessons per page, typical lesson counts

---

## Task 6.2: Implement Page Rotation System

**Objective**: Auto-rotate pages when content exceeds single page

**Implementation**:
- Split lessons into pages of N items each
- Auto-advance every X seconds (configurable, default 10s)
- Page indicator showing "Page 1/3"
- Smooth transition between pages

**Verify**: Demo with 20+ lessons shows rotation working

---

## Task 6.3: Language-Specific Views

**Objective**: Create dedicated view for each display language

**Options to evaluate**:
1. Separate URLs per language (?lang=cz, ?lang=de)
2. Auto-rotate through languages on single display
3. Filter lessons by language for language-specific displays

**Verify**: Each language has optimized view

---

## Task 6.4: Fix Data Grouping Issues

**Objective**: Ensure related lessons (e.g., kids school) are grouped correctly

**Known issues**:
- Kids school lessons not always grouped together
- Need to analyze TSV data to understand grouping logic
- May need to enhance ParseOrdersProcessor

**Steps**:
1. Analyze real data patterns
2. Identify grouping criteria
3. Implement grouping logic if needed

**Verify**: Related lessons appear together in display

---

## Task 6.5: Sponsor Display Decision

**Objective**: Decide and implement sponsor handling

**Options**:
1. Show sponsors prominently (name highlighted)
2. Show sponsors same as other participants
3. Hide sponsors entirely
4. Show sponsor company/group name only

**Verify**: Sponsor display matches agreed approach

---

## Task 6.6: Participant Language Indicator

**Objective**: Distinguish between lesson language and participant's native language

**Current state**: Shows lesson_language_key (language of instruction)

**Requirement**: May need to show:
- Language spoken by instructor
- Language(s) spoken by participants
- Both with clear visual distinction

**Verify**: Language indicators are clear and unambiguous

---

## Task 6.7: Format and Layout Tuning

**Objective**: Fine-tune all display elements for optimal readability

**Areas to tune**:
- Font sizes for different elements
- Color schemes for current vs upcoming
- Card spacing and padding
- Time format display
- Level/location badges
- Instructor info presentation

**Verify**: User approves final layout

---

## Task 6.8: Implement No-Scroll Safeguards

**Objective**: Ensure display never requires scrolling

**Implementation**:
- CSS overflow hidden on body
- Content truncation with ellipsis where needed
- Dynamic font scaling if content doesn't fit
- Page rotation for overflow content

**Verify**: No scrollbars appear, all content accessible via rotation

---

## Dependencies

```
6.1 (Analysis)
  └─> 6.2 (Rotation) ─> 6.8 (No-scroll)
  └─> 6.3 (Languages)

6.4 (Grouping) - Independent
6.5 (Sponsors) - Independent
6.6 (Language indicator) - Independent
6.7 (Format tuning) - After 6.2, 6.3 complete
```

## Notes

- All changes must maintain debug mode functionality
- Test with simulated time to verify appearance at different times of day
- Consider screen burn-in prevention (subtle animation/movement?)
