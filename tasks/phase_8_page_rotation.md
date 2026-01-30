# Phase 8: Page Rotation System

## Overview

Implement multi-page rotation for vertical display screens when lessons overflow a single page. Pages are grouped by lesson start time slots, with the current/relevant page staying on screen longer.

## Time Slot Configuration

| Slot | Start Time Range | Main Display Window | Notes |
|------|------------------|---------------------|-------|
| 1 | 08:00-09:59 | 08:00-10:00 | Morning lessons (range) |
| 2 | 11:00 | 10:00-12:00 | Mid-morning |
| 3 | 13:00 | 12:00-14:00 | Afternoon |
| 4 | 14:30 | 14:00-17:00 | Late afternoon |

## Timing Configuration

- **Main page duration**: 15 seconds (page matching current time window)
- **Other pages duration**: 5 seconds
- **Rotation**: Continuous cycle through all pages with lessons

## Technical Design

### Page Grouping Logic

```javascript
// Determine which slot a lesson belongs to based on start time
function getTimeSlot(startTime) {
  const hour = parseInt(startTime.split(':')[0]);
  const minute = parseInt(startTime.split(':')[1]);
  const totalMinutes = hour * 60 + minute;

  if (totalMinutes >= 480 && totalMinutes < 600) return 1;  // 08:00-09:59
  if (totalMinutes >= 660 && totalMinutes < 720) return 2;  // 11:00-11:59
  if (totalMinutes >= 780 && totalMinutes < 840) return 3;  // 13:00-13:59
  if (totalMinutes >= 870) return 4;                        // 14:30+

  return null; // Lesson doesn't fit any slot
}
```

### Main Page Detection

```javascript
// Determine which slot is "main" based on current time
function getMainSlot(currentTime) {
  const hour = currentTime.getHours();

  if (hour >= 8 && hour < 10) return 1;   // 08:00-10:00
  if (hour >= 10 && hour < 12) return 2;  // 10:00-12:00
  if (hour >= 12 && hour < 14) return 3;  // 12:00-14:00
  if (hour >= 14 && hour < 17) return 4;  // 14:00-17:00

  return null; // Outside operating hours
}
```

---

## Tasks

### Task 8.1: Define time slot configuration

**Size**: small

**Description**:
Create the TIME_SLOTS configuration object in app.js that defines:
- Slot number (1-4)
- Start time range (for grouping lessons)
- Main display window (for determining current relevance)
- Display timing (main vs other)

**Files to modify**:
- `static-site/app.js` - Add TIME_SLOTS constant

**Verification**:
- TIME_SLOTS config object exists with 4 slots defined
- Each slot has: id, startRange, mainWindow, label

---

### Task 8.2: Implement lesson grouping by slot

**Size**: medium

**Description**:
Modify the lesson rendering logic to group lessons into pages based on their start time. Each time slot becomes a separate page.

**Requirements**:
- Group lessons by matching start time to slot ranges
- Slot 1 (08:00-09:59): All lessons starting 08:00-09:59
- Slot 2 (11:00): Lessons starting 11:00-11:59
- Slot 3 (13:00): Lessons starting 13:00-13:59
- Slot 4 (14:30): Lessons starting 14:30+
- Handle lessons that don't fit any slot (show on nearest slot or separate page)

**Files to modify**:
- `static-site/app.js` - Add groupLessonsBySlot() function

**Verification**:
- Lessons correctly grouped into pages by start time
- Console log shows slot assignments

---

### Task 8.3: Implement page rotation engine

**Size**: medium

**Description**:
Create the rotation system that cycles through pages automatically.

**Requirements**:
- Track current page index
- Timer-based page switching
- Configurable duration per page
- Smooth transition between pages (fade or instant)
- Pause rotation on user interaction (debug mode)

**Files to modify**:
- `static-site/app.js` - Add PageRotator class/functions
- `static-site/styles.css` - Add transition styles if needed

**Verification**:
- Pages auto-cycle with visible transitions
- Rotation can be paused/resumed

---

### Task 8.4: Implement main page priority timing

**Size**: small

**Description**:
Make the "main" page (matching current time window) stay on screen longer than other pages.

**Requirements**:
- Detect which slot is "main" based on current time
- Main page: 15 seconds
- Other pages: 5 seconds
- Recalculate main slot when time changes (crossing hour boundaries)

**Files to modify**:
- `static-site/app.js` - Add getMainSlot(), update rotation timing

**Verification**:
- Main page shows for 15s
- Other pages show for 5s
- Timing adjusts as clock crosses boundaries

---

### Task 8.5: Add page indicator UI

**Size**: small

**Description**:
Add visual indicator showing current page position and total pages.

**Requirements**:
- Dots or progress bar at bottom of screen
- Current page highlighted
- Show slot label (e.g., "09:00", "11:00", "13:00", "14:30")
- Semi-transparent, non-intrusive design

**Files to modify**:
- `static-site/index.html` - Add indicator container
- `static-site/styles.css` - Style indicator
- `static-site/app.js` - Update indicator on page change

**Verification**:
- Visual indicator shows current page
- Indicator updates on page change
- Design matches existing theme

---

### Task 8.6: Handle edge cases

**Size**: small

**Description**:
Handle special cases gracefully.

**Edge cases**:
1. **Empty slot**: Skip slots with no lessons (don't show empty page)
2. **Single page**: If only one slot has lessons, no rotation needed
3. **Outside hours**: Before 08:00 or after 17:00, show all lessons or message
4. **No lessons**: Show "No lessons scheduled" message
5. **Debug mode**: Allow manual page selection, pause rotation

**Files to modify**:
- `static-site/app.js` - Add edge case handling

**Verification**:
- Empty slots are skipped
- Single page doesn't rotate
- Outside hours shows appropriate content
- Debug mode allows manual control

---

### Task 8.7: Test with real data

**Size**: small

**Description**:
Test the rotation system with various real data scenarios.

**Test scenarios**:
1. Day with lessons in all 4 slots
2. Day with lessons in only 2 slots
3. Day with many lessons in one slot (overflow)
4. Day with no lessons
5. Different times of day (main page changes)

**Verification**:
- Rotation works correctly with various lesson configurations
- No JavaScript errors in console
- Performance acceptable (no lag/flicker)

---

## Completion Criteria

- [ ] Pages grouped by time slot
- [ ] Automatic rotation with configurable timing
- [ ] Main page stays on screen 3x longer
- [ ] Page indicator visible
- [ ] Edge cases handled
- [ ] Works with real production data
