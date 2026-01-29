/**
 * GoldSport Scheduler - Display Application
 *
 * Multi-language ski lesson display with auto-refresh.
 */

// Configuration
const CONFIG = {
    refreshInterval: 60000,  // 60 seconds
    dataUrl: 'data/schedule.json',
    configUrl: {
        translations: 'config/ui-translations.json',
        dictionaries: 'config/dictionaries.json',
    },
    defaultLanguage: 'en',
};

// Application state
const state = {
    language: CONFIG.defaultLanguage,
    translations: {},
    dictionaries: {},
    schedule: null,
    lastUpdate: null,
    refreshTimer: null,
    debugMode: false,      // ?debug=true shows all lessons
    dateOverride: null,    // ?date=28.01.2026 shows specific date
    timeOverride: null,    // ?time=09:30 simulates specific time
};

/**
 * Initialize the application
 */
async function init() {
    // Get parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    state.language = urlParams.get('lang') || CONFIG.defaultLanguage;
    state.debugMode = urlParams.get('debug') === 'true';
    state.dateOverride = urlParams.get('date') || null;
    state.timeOverride = urlParams.get('time') || null;  // e.g., "09:30"

    // Show debug indicator
    if (state.debugMode || state.dateOverride || state.timeOverride) {
        showDebugBanner();
    }

    // Set up date/time display
    updateDateTimeDisplay();
    setInterval(updateDateTimeDisplay, 1000); // Update every second

    // Load configurations and data
    try {
        await loadConfigs();
        await loadSchedule();
        startAutoRefresh();
    } catch (error) {
        console.error('Initialization failed:', error);
        showError('error_loading');
    }
}

/**
 * Load translation and dictionary configs
 */
async function loadConfigs() {
    try {
        const [transResponse, dictResponse] = await Promise.all([
            fetch(CONFIG.configUrl.translations),
            fetch(CONFIG.configUrl.dictionaries),
        ]);

        if (transResponse.ok) {
            state.translations = await transResponse.json();
        }
        if (dictResponse.ok) {
            state.dictionaries = await dictResponse.json();
        }

        // Apply translations to UI
        applyTranslations();
    } catch (error) {
        console.warn('Failed to load configs, using defaults:', error);
    }
}

/**
 * Load schedule data from API
 */
async function loadSchedule() {
    try {
        const response = await fetch(CONFIG.dataUrl);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        state.schedule = await response.json();
        state.lastUpdate = new Date();

        renderSchedule();
        updateLastUpdateTime();
    } catch (error) {
        console.error('Failed to load schedule:', error);
        showError('error_loading');
    }
}

/**
 * Day names for date display
 */
const DAY_NAMES = {
    'cz': ['Neděle', 'Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota'],
    'cs': ['Neděle', 'Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota'],
    'de': ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'],
    'en': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    'pl': ['Niedziela', 'Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota'],
};

/**
 * Update the date/time display in the header
 * Format: "Thursday, 29.1.2026 14:06:30"
 */
function updateDateTimeDisplay() {
    const el = document.getElementById('datetime-display');
    if (!el) return;

    const now = new Date();
    const dayNames = DAY_NAMES[state.language] || DAY_NAMES['en'];
    const dayName = dayNames[now.getDay()];
    const day = now.getDate();
    const month = now.getMonth() + 1;
    const year = now.getFullYear();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');

    el.textContent = `${dayName}, ${day}.${month}.${year} ${hours}:${minutes}:${seconds}`;
}

/**
 * Apply translations to all elements with data-i18n attribute
 */
function applyTranslations() {
    const elements = document.querySelectorAll('[data-i18n]');
    const langTranslations = state.translations[state.language] || state.translations.en || {};

    elements.forEach(el => {
        const key = el.dataset.i18n;
        if (langTranslations[key]) {
            el.textContent = langTranslations[key];
        }
    });
}

/**
 * Get translated UI text
 */
function getUIText(key) {
    const langTranslations = state.translations[state.language] || state.translations.en || {};
    return langTranslations[key] || key;
}

/**
 * Translate data value using dictionaries
 */
function translateValue(value, category) {
    const categoryDict = state.dictionaries[category] || {};
    const valueTranslations = categoryDict[value] || {};
    return valueTranslations[state.language] || value;
}

/**
 * Render the schedule - always shows entire day
 */
function renderSchedule() {
    if (!state.schedule) return;

    const allByDate = state.schedule.all_lessons_by_date || {};
    const dates = Object.keys(allByDate).sort();

    // Determine which date to show
    let targetDate = state.dateOverride;
    if (!targetDate) {
        // Use today's date in DD.MM.YYYY format
        const now = new Date();
        targetDate = `${now.getDate().toString().padStart(2, '0')}.${(now.getMonth() + 1).toString().padStart(2, '0')}.${now.getFullYear()}`;
    }

    // Only fall back to first available date if no date override specified
    // When user explicitly selects a date, show empty state if no data
    if (!state.dateOverride && !allByDate[targetDate] && dates.length > 0) {
        targetDate = dates[0];
    }

    const lessons = targetDate ? (allByDate[targetDate] || []) : [];

    // Update title with translated text
    // Format: "Schedule for Friday, 30.01.2026. This day we give 11 lessons."
    const titleEl = document.getElementById('day-title');
    if (titleEl && targetDate) {
        // Parse date from DD.MM.YYYY format
        const [day, month, year] = targetDate.split('.');
        const dateObj = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
        const dayNames = DAY_NAMES[state.language] || DAY_NAMES['en'];
        const dayName = dayNames[dateObj.getDay()];

        const scheduleFor = getUIText('schedule_for');
        const lessonsText = getUIText('lessons_on_day').replace('{n}', lessons.length);

        titleEl.textContent = `${scheduleFor} ${dayName}, ${targetDate}. ${lessonsText}`;
    } else if (titleEl) {
        titleEl.textContent = getUIText('no_lessons');
    }

    // Render all lessons
    renderLessons('all-lessons', lessons, 'no_lessons');

}

/**
 * Language labels (flags don't work in Chrome/Windows)
 */
const LANGUAGE_FLAGS = {
    'cz': '🇨🇿',
    'de': '🇩🇪',
    'en': '🇬🇧',
    'pl': '🇵🇱',
};

/**
 * Group type symbols
 */
const GROUP_TYPE_SYMBOLS = {
    'privát': '👤',
    'malá skupina': '👤👤',
    'velká skupina': '👤👤👤',
};

/**
 * Format participant with language flag and sponsor
 * @param {Object|string} participant - Participant object or name string
 * @returns {string} Formatted "Name 🇩🇪 (Sponsor)" e.g. "Anna 🇩🇪 (Iryna Sc)"
 */
function formatParticipant(participant) {
    if (typeof participant === 'string') {
        // Legacy format - just name
        return participant;
    }

    const name = participant.name || '';
    const lang = participant.language || '';
    const sponsor = participant.sponsor || '';
    const flag = LANGUAGE_FLAGS[lang] || (lang ? lang.toUpperCase() : '');

    // Format: "Name 🇩🇪 (Sponsor)"
    let result = name;
    if (flag) result += ` ${flag}`;
    if (sponsor) result += ` (${sponsor})`;

    return result.trim();
}

/**
 * Get time slot number for color coding (1-5 based on hour)
 */
function getTimeSlot(startTime) {
    if (!startTime) return 1;
    const hour = parseInt(startTime.split(':')[0], 10);
    if (hour < 10) return 1;      // 08:00-09:59 - blue
    if (hour < 12) return 2;      // 10:00-11:59 - green
    if (hour < 14) return 3;      // 12:00-13:59 - yellow
    if (hour < 16) return 4;      // 14:00-15:59 - pink
    return 5;                     // 16:00+ - purple
}

/**
 * Render lessons to a container
 */
function renderLessons(containerId, lessons, emptyMessageKey) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';

    if (!lessons || lessons.length === 0) {
        const emptyTemplate = document.getElementById('empty-template');
        const emptyEl = emptyTemplate.content.cloneNode(true);
        const messageEl = emptyEl.querySelector('[data-i18n]');
        if (messageEl) {
            messageEl.textContent = getUIText(emptyMessageKey);
        }
        container.appendChild(emptyEl);
        return;
    }

    const template = document.getElementById('lesson-template');
    let lastStartTime = null;

    lessons.forEach(lesson => {
        // Add line break when start time changes
        if (lastStartTime !== null && lesson.start !== lastStartTime) {
            const lineBreak = document.createElement('div');
            lineBreak.className = 'time-break';
            container.appendChild(lineBreak);
        }
        lastStartTime = lesson.start;

        const card = template.content.cloneNode(true);
        const cardEl = card.querySelector('.lesson-card');

        // Set time slot for color coding
        const slot = getTimeSlot(lesson.start);
        if (cardEl) cardEl.setAttribute('data-slot', slot);

        // Line 1: Time | Group Type | Level | Location
        const timeRange = `${lesson.start || '--:--'}-${lesson.end || '--:--'}`;
        card.querySelector('.lesson-time').textContent = timeRange;

        // Group type (privát, malá skupina, velká skupina)
        card.querySelector('.lesson-group-type').textContent =
            translateValue(lesson.group_type_key, 'group_types');

        card.querySelector('.lesson-level').textContent =
            translateValue(lesson.level_key, 'levels');

        // Location (translated)
        card.querySelector('.lesson-location').textContent =
            translateValue(lesson.location_key, 'locations');

        // Participants - sorted by sponsor, then name
        const participantList = card.querySelector('.participant-list');
        if (lesson.people && lesson.people.length > 0) {
            const sortedPeople = [...lesson.people].sort((a, b) => {
                const sponsorCompare = (a.sponsor || '').localeCompare(b.sponsor || '');
                if (sponsorCompare !== 0) return sponsorCompare;
                return (a.name || '').localeCompare(b.name || '');
            });
            participantList.textContent = sortedPeople.map(formatParticipant).join(', ');
        }

        // Instructor - only show if assigned (not default)
        const instructorEl = card.querySelector('.instructor-name');
        const instructorName = lesson.instructor?.name;
        if (instructorName && instructorName !== 'GoldSport Team') {
            instructorEl.textContent = instructorName;
        } else {
            // Remove instructor and its preceding pipe
            instructorEl.remove();
            const pipes = card.querySelectorAll('.pipe');
            if (pipes.length > 0) {
                pipes[pipes.length - 1].remove();
            }
        }

        container.appendChild(card);
    });

    // Convert emoji flags to images for cross-browser support
    if (typeof twemoji !== 'undefined') {
        twemoji.parse(container, { folder: 'svg', ext: '.svg' });
    }
}

/**
 * Show error message
 */
function showError(messageKey) {
    const container = document.getElementById('all-lessons');
    if (container) {
        container.innerHTML = `<div class="error">${getUIText(messageKey)}</div>`;
    }
}

/**
 * Update last update time display
 */
function updateLastUpdateTime() {
    const el = document.getElementById('last-update');
    if (el && state.lastUpdate) {
        el.textContent = state.lastUpdate.toLocaleTimeString(state.language === 'cz' ? 'cs' : state.language);
    }
}

/**
 * Start auto-refresh timer
 */
function startAutoRefresh() {
    // Clear existing timer
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
    }

    // Set up new timer
    state.refreshTimer = setInterval(async () => {
        console.log('Auto-refreshing data...');
        await loadSchedule();
    }, CONFIG.refreshInterval);
}

/**
 * Stop auto-refresh timer
 */
function stopAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
        state.refreshTimer = null;
    }
}

/**
 * Show debug mode banner
 */
function showDebugBanner() {
    const banner = document.createElement('div');
    banner.className = 'debug-banner';

    // Generate date buttons: 7 days ahead + today + 14 days back
    const dateButtons = [];
    const today = new Date();

    // Future dates (7 days ahead, sorted furthest first)
    for (let i = 7; i >= 1; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        const dateStr = formatDateForUrl(date);
        const displayStr = formatDateShort(date);
        const isActive = state.dateOverride === dateStr;
        dateButtons.push(`<a href="?debug=true&date=${dateStr}" class="date-btn future${isActive ? ' active' : ''}">${displayStr}</a>`);
    }

    // Past dates (today + 14 days back)
    for (let i = 0; i < 14; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        const dateStr = formatDateForUrl(date);
        const displayStr = formatDateShort(date);
        const isActive = state.dateOverride === dateStr;
        dateButtons.push(`<a href="?debug=true&date=${dateStr}" class="date-btn${isActive ? ' active' : ''}">${displayStr}</a>`);
    }

    banner.innerHTML = `
        <div class="debug-header">
            <strong>DEBUG MODE</strong>
            ${state.timeOverride ? `| Time: ${state.timeOverride}` : ''}
            | <a href="?" class="exit-link">Exit debug</a>
        </div>
        <div class="date-selector">
            ${dateButtons.join('')}
        </div>
    `;
    banner.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #ff5722;
        color: white;
        padding: 4px 16px 8px;
        text-align: center;
        font-size: 14px;
        z-index: 9999;
    `;

    // Style the date selector
    const style = document.createElement('style');
    style.textContent = `
        .debug-banner .debug-header { margin-bottom: 6px; }
        .debug-banner a { color: white; }
        .debug-banner .date-selector {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            justify-content: center;
        }
        .debug-banner .date-btn {
            padding: 2px 8px;
            background: rgba(255,255,255,0.2);
            border-radius: 4px;
            text-decoration: none;
            font-size: 12px;
        }
        .debug-banner .date-btn:hover {
            background: rgba(255,255,255,0.4);
        }
        .debug-banner .date-btn.active {
            background: white;
            color: #ff5722;
            font-weight: bold;
        }
        .debug-banner .date-btn.future {
            background: rgba(76,175,80,0.3);
        }
        .debug-banner .date-btn.future:hover {
            background: rgba(76,175,80,0.5);
        }
        .debug-banner .date-btn.future.active {
            background: #4caf50;
            color: white;
        }
    `;
    document.head.appendChild(style);

    document.body.prepend(banner);
    document.body.style.paddingTop = '70px';
}

/**
 * Format date for URL parameter (DD.MM.YYYY)
 */
function formatDateForUrl(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
}

/**
 * Format date for display (DD.MM or "Today")
 */
function formatDateShort(date) {
    const today = new Date();
    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    }
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `${day}.${month}`;
}

/**
 * Render time slider for debugging
 */
function renderTimeSlider(currentDate, dates) {
    // Add time slider to footer
    const footer = document.querySelector('.footer');
    if (!footer) return;

    // Remove existing slider
    const existing = footer.querySelector('.time-slider');
    if (existing) existing.remove();

    const sliderDiv = document.createElement('div');
    sliderDiv.className = 'time-slider';
    sliderDiv.style.cssText = 'margin-top: 16px; padding: 16px; background: #f0f0f0; border-radius: 8px;';

    sliderDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
            <label><strong>Simulate time:</strong></label>
            <input type="range" id="time-range" min="0" max="1440" value="${timeToMinutes(state.timeOverride)}" style="flex: 1; min-width: 200px;">
            <span id="time-display" style="font-weight: bold; min-width: 60px;">${state.timeOverride}</span>
            <select id="date-select" style="padding: 8px;">
                ${dates.map(d => `<option value="${d}" ${d === currentDate ? 'selected' : ''}>${d}</option>`).join('')}
            </select>
            <button onclick="applyTimeSimulation()" style="padding: 8px 16px; cursor: pointer;">Apply</button>
        </div>
        <div style="margin-top: 8px; font-size: 12px; color: #666;">
            Quick:
            <a href="#" onclick="setQuickTime('08:00')">08:00</a> |
            <a href="#" onclick="setQuickTime('09:30')">09:30</a> |
            <a href="#" onclick="setQuickTime('11:00')">11:00</a> |
            <a href="#" onclick="setQuickTime('13:00')">13:00</a> |
            <a href="#" onclick="setQuickTime('14:30')">14:30</a> |
            <a href="#" onclick="setQuickTime('16:00')">16:00</a>
        </div>
    `;

    footer.appendChild(sliderDiv);

    // Add event listener for range input
    document.getElementById('time-range').addEventListener('input', (e) => {
        const minutes = parseInt(e.target.value);
        document.getElementById('time-display').textContent = minutesToTime(minutes);
    });
}

function timeToMinutes(time) {
    if (!time) return 540; // default 9:00
    const [h, m] = time.split(':').map(Number);
    return h * 60 + m;
}

function minutesToTime(minutes) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
}

function setQuickTime(time) {
    document.getElementById('time-range').value = timeToMinutes(time);
    document.getElementById('time-display').textContent = time;
    applyTimeSimulation();
    return false;
}

function applyTimeSimulation() {
    const time = document.getElementById('time-display').textContent;
    const date = document.getElementById('date-select').value;
    const url = new URL(window.location);
    url.searchParams.set('debug', 'true');
    url.searchParams.set('date', date);
    url.searchParams.set('time', time);
    window.location.href = url.toString();
}
// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        state,
        init,
        loadSchedule,
        changeLanguage,
        translateValue,
        renderSchedule,
    };
}
