# Phase 4: Display Frontend

**Objective**: Build the multi-language display page for vertical screens

**Repos involved**: orchestration (this repo - mono-repo)

---

## Tasks

### 4.1 Create HTML Structure
**Size**: small

Create `static-site/index.html` with semantic structure.

**Structure**:
```html
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GoldSport Schedule</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header>
    <img src="assets/logo.png" alt="GoldSport" class="logo">
    <h1 id="title">Rozvrh lekcí</h1>
  </header>
  <main>
    <section id="current-lessons">
      <h2 id="current-title">Právě probíhá</h2>
      <div class="lessons-container"></div>
    </section>
    <section id="upcoming-lessons">
      <h2 id="upcoming-title">Následující lekce</h2>
      <div class="lessons-container"></div>
    </section>
  </main>
  <footer>
    <span id="last-update"></span>
  </footer>
  <script src="app.js"></script>
</body>
</html>
```

**Verify**: HTML is valid, displays in browser

---

### 4.2 Create CSS for Vertical Display
**Size**: medium

Create `static-site/styles.css` optimized for portrait orientation.

**Requirements**:
- Large fonts (readable from 3m)
- High contrast colors
- Portrait/vertical layout
- Current lessons highlighted
- Clean, minimal design

**Key styles**:
- Body: dark background, light text
- Lessons: card-based layout
- Current: highlighted border/background
- Time: prominent display

**Verify**: Page looks good on vertical display (test with browser dev tools)

---

### 4.3 Implement JavaScript - Data Fetching
**Size**: small

Create `static-site/app.js` with data loading.

**Functions**:
- `fetchSchedule()` - GET schedule.json
- `fetchTranslations()` - GET ui-translations.json
- `fetchDictionaries()` - GET dictionaries.json

**Verify**: Console shows data loaded successfully

---

### 4.4 Implement JavaScript - Language Support
**Size**: medium

Add multi-language rendering.

**Logic**:
- Read `?lang=` parameter (default: cz)
- Load appropriate translations
- Translate all UI text
- Translate data values using dictionaries

**Functions**:
- `getLanguage()` - parse URL param
- `translateUI(lang)` - update all UI text
- `translateValue(key, dict, lang)` - lookup translation

**Verify**: `?lang=de` shows German UI

---

### 4.5 Implement JavaScript - Lesson Rendering
**Size**: medium

Render lessons from schedule.json.

**Functions**:
- `renderLessons(lessons, container)` - create lesson cards
- `formatTime(isoString)` - display time
- `formatParticipants(list)` - join names

**Lesson card content**:
- Time (start - end)
- Level (translated)
- Language flag/name
- Instructor name
- Participants

**Verify**: Lessons display correctly

---

### 4.6 Implement JavaScript - Auto-Refresh
**Size**: small

Add automatic data refresh.

**Logic**:
- Refresh every 60 seconds (configurable)
- Show last update time
- Handle errors gracefully (keep displaying old data)

**Verify**: Data refreshes without page reload

---

### 4.7 Implement Current vs Upcoming Logic
**Size**: small

Separate current from upcoming lessons.

**Logic**:
- Current: start <= now <= end
- Upcoming: start > now (same day)
- Sort by start time

**Verify**: Lessons appear in correct section based on current time

---

### 4.8 Upload Static Site to S3
**Size**: small

Deploy frontend files to website bucket.

**Files**:
- index.html
- styles.css
- app.js
- assets/logo.png (placeholder)

**Verify**: Site accessible via S3 website URL

---

### 4.9 End-to-End Frontend Test
**Size**: small

Test complete frontend with real data.

**Steps**:
1. Access S3 website URL
2. Verify lessons display
3. Test language switching
4. Verify auto-refresh
5. Test on vertical aspect ratio

**Verify**: All features work correctly

---

## Dependencies

```
4.1 ──▶ 4.2 ──▶ 4.8
         │
4.3 ──▶ 4.4 ──▶ 4.5 ──▶ 4.6 ──▶ 4.7 ──▶ 4.8 ──▶ 4.9
```

---

## Phase Completion Criteria

- [ ] HTML/CSS renders correctly on vertical display
- [ ] All 4 languages work (?lang=en/de/cz/pl)
- [ ] Lessons display with all required information
- [ ] Auto-refresh works without page reload
- [ ] Current vs upcoming separation works
- [ ] Site deployed to S3
