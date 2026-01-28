# Task 6.1: Display Requirements Analysis

## Screen Specifications
- **Target resolution**: 1080x1920 (portrait/vertical)
- **Display mode**: Passive screensaver (no user interaction)
- **Viewing distance**: 3+ meters

## Current Layout Capacity

### Fixed Element Heights
| Element | Height (px) |
|---------|-------------|
| Container padding | 48 |
| Header | 132 |
| Footer | 76 |
| Current section overhead | 122 |
| Upcoming section overhead | 122 |
| **Total fixed** | **500** |
| **Available for cards** | **1420** |

### Card Dimensions (Portrait Mode)
| Component | Height (px) |
|-----------|-------------|
| Card padding | 48 |
| Time row | 48 |
| Level row | 48 |
| Info row | 36 |
| Instructor | 64 |
| Participants | 36 |
| **Total per card** | **280** |
| Gap between cards | 24 |

### Current Capacity
- **Space per section**: 710px
- **Cards per section**: 2
- **Total visible**: 4 lesson cards

## Real Data Analysis

### Lesson Distribution (35 dates analyzed)
| Metric | Value |
|--------|-------|
| Total lessons | 593 |
| Min concurrent | 1 |
| Max concurrent | 17 |
| Average concurrent | 4.4 |

### Peak Days
| Date | Total Lessons | Max Concurrent |
|------|---------------|----------------|
| 17.01.2026 | 40 | 14 |
| 04.01.2026 | 32 | 17 |
| 19.01.2026 | 32 | 15 |
| 20.01.2026 | 24 | 13 |
| 11.01.2026 | 20 | 12 |

### Time Slot Patterns
Standard time slots:
- 09:00-10:50 (morning)
- 11:00-12:50 (late morning) - **busiest**
- 13:00-14:20 (early afternoon)
- 14:30-16:00 (late afternoon)

## Gap Analysis

| Scenario | Current | Upcoming | Total | Pages Needed |
|----------|---------|----------|-------|--------------|
| Quiet day | 1-2 | 4-6 | 5-8 | 2-4 |
| Average day | 4-5 | 8-12 | 12-17 | 4-8 |
| Busy day | 10-17 | 15-25 | 25-42 | 10-20 |

**Problem**: Current layout cannot show more than 4 lessons without scrolling/rotation.

## Recommendations

### Option A: Compact Cards (Recommended First Step)
Reduce card height from 280px to ~100px:
- Remove instructor photo
- Single-line time display: "09:00-10:50"
- Single-line info: "Level | Location | Lang"
- Participant count only (not names)

**Estimated capacity**: 6-8 cards per section = 12-16 total

### Option B: Two-Column Layout
Use CSS grid with 2 columns for cards:
- Each card ~200px wide on 1080px screen
- Maintain readability with larger fonts

**Estimated capacity**: 4-6 cards per section × 2 columns = 16-24 total

### Option C: Page Rotation (Required for Busy Days)
Auto-rotate pages every 8-10 seconds:
- Page indicator: "Page 1/3"
- Smooth fade transition
- Configurable interval

**Combined with compact cards**: Can handle any volume

### Option D: Priority-Based Display
Show only most relevant lessons:
- Current: Always show all
- Upcoming: Show next 2-3 time slots only
- Filter by relevance (language matching?)

## Recommended Implementation Order

1. **Task 6.8**: Add no-scroll safeguards first (CSS overflow:hidden)
2. **Task 6.7**: Compact card redesign (reduce to ~100px height)
3. **Task 6.2**: Page rotation system (for overflow)
4. **Task 6.3**: Language-specific views (reduce content per page)

## Minimum Viable Display

For passive screensaver use, essential information per lesson:
- ✅ Time slot (start-end)
- ✅ Level/type (translated)
- ✅ Location
- ⚠️ Instructor (name only, no photo)
- ⚠️ Language
- ❓ Participants (count or names?)
- ❌ Sponsor info (privacy concern, low value for display)

## Next Steps
1. Create compact card CSS variant
2. Test with real data at different times
3. Implement page rotation for overflow
4. User review of compact layout
