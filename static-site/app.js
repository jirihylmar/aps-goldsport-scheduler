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
    defaultLanguage: 'cz',
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

    // Set up language selector
    setupLanguageSelector();

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
 * Set up language selector buttons
 */
function setupLanguageSelector() {
    const buttons = document.querySelectorAll('.lang-btn');

    buttons.forEach(btn => {
        const lang = btn.dataset.lang;

        // Mark active language
        if (lang === state.language) {
            btn.classList.add('active');
        }

        // Handle click
        btn.addEventListener('click', () => {
            changeLanguage(lang);
        });
    });
}

/**
 * Change display language
 */
function changeLanguage(lang) {
    state.language = lang;

    // Update URL without reload
    const url = new URL(window.location);
    url.searchParams.set('lang', lang);
    window.history.replaceState({}, '', url);

    // Update active button
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });

    // Reapply translations
    applyTranslations();
    renderSchedule();
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
 * Render the schedule
 */
function renderSchedule() {
    if (!state.schedule) return;

    // Debug mode with time simulation: filter lessons client-side
    if (state.timeOverride && state.dateOverride) {
        const allByDate = state.schedule.all_lessons_by_date || {};
        const dates = Object.keys(allByDate).sort();
        const lessons = allByDate[state.dateOverride] || [];
        const simTime = state.timeOverride;

        // Filter into current/upcoming based on simulated time
        const current = lessons.filter(l => l.start <= simTime && simTime < l.end);
        const upcoming = lessons.filter(l => l.start > simTime);
        const past = lessons.filter(l => l.end <= simTime);

        // Update section titles
        const currentTitle = document.querySelector('.current-section .section-title');
        const upcomingTitle = document.querySelector('.upcoming-section .section-title');

        if (currentTitle) {
            currentTitle.textContent = `Current @ ${simTime} (${current.length})`;
        }
        if (upcomingTitle) {
            upcomingTitle.textContent = `Upcoming (${upcoming.length}) | Past: ${past.length}`;
        }

        renderLessons('current-lessons', current, 'no_current_lessons');
        renderLessons('upcoming-lessons', upcoming, 'no_upcoming_lessons');

        // Show time slider
        renderTimeSlider(state.dateOverride, dates);
        return;
    }

    // Debug mode without time: show all lessons for a specific date
    if (state.debugMode || state.dateOverride) {
        const allByDate = state.schedule.all_lessons_by_date || {};
        const dates = Object.keys(allByDate).sort();

        // Find which date to show
        let targetDate = state.dateOverride;
        if (!targetDate && dates.length > 0) {
            // Default to first date with data
            targetDate = dates[0];
        }

        const lessons = targetDate ? (allByDate[targetDate] || []) : [];

        // Update section titles for debug mode
        const currentTitle = document.querySelector('.current-section .section-title');
        const upcomingTitle = document.querySelector('.upcoming-section .section-title');

        if (currentTitle) {
            currentTitle.textContent = `All Lessons: ${targetDate || 'No data'} (${lessons.length})`;
        }
        if (upcomingTitle) {
            upcomingTitle.textContent = `Select date or add &time=09:30 to simulate`;
        }

        // Show all lessons in current section
        renderLessons('current-lessons', lessons, 'no_lessons');

        // Show date selector in upcoming section
        renderDateSelector('upcoming-lessons', dates, targetDate);
        return;
    }

    // Normal mode: current and upcoming lessons
    renderLessons('current-lessons', state.schedule.current_lessons, 'no_current_lessons');
    renderLessons('upcoming-lessons', state.schedule.upcoming_lessons, 'no_upcoming_lessons');
}

/**
 * Language flag mapping
 */
const LANGUAGE_FLAGS = {
    'cz': '🇨🇿',
    'de': '🇩🇪',
    'en': '🇬🇧',
    'pl': '🇵🇱',
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

    lessons.forEach(lesson => {
        const card = template.content.cloneNode(true);

        // Line 1: Time range | Level | Group size | Location
        const timeRange = `${lesson.start || '--:--'}-${lesson.end || '--:--'}`;
        card.querySelector('.lesson-time').textContent = timeRange;

        card.querySelector('.lesson-level').textContent =
            translateValue(lesson.level_key, 'levels');

        // Group size (count of participants)
        const count = lesson.participant_count || (lesson.participants ? lesson.participants.length : 0);
        card.querySelector('.lesson-count').textContent = count > 0 ? count : '';

        // Location (translated)
        card.querySelector('.lesson-location').textContent =
            translateValue(lesson.location_key, 'locations');

        // Line 2: Participants with individual language flags
        // Format: "Anna 🇩🇪, Max 🇬🇧, Petra 🇨🇿 *" (* = sponsor)
        const participantList = card.querySelector('.participant-list');
        const langEl = card.querySelector('.lesson-language');

        // Hide the lesson-level language element (we show per-participant now)
        if (langEl) langEl.style.display = 'none';

        if (lesson.participants && lesson.participants.length > 0) {
            const formatted = lesson.participants.map(formatParticipant).join(', ');
            participantList.textContent = formatted;
        } else if (lesson.sponsor) {
            participantList.textContent = lesson.sponsor;
        }

        // Line 3: Instructor
        const instructorEl = card.querySelector('.lesson-instructor');
        const instructorLabel = card.querySelector('.instructor-label');
        if (instructorLabel) {
            instructorLabel.textContent = getUIText('instructor');
        }

        if (lesson.instructor && lesson.instructor.name) {
            card.querySelector('.instructor-name').textContent = lesson.instructor.name;
        } else {
            instructorEl.style.display = 'none';
        }

        container.appendChild(card);
    });
}

/**
 * Show error message
 */
function showError(messageKey) {
    const containers = ['current-lessons', 'upcoming-lessons'];

    containers.forEach(id => {
        const container = document.getElementById(id);
        if (container) {
            container.innerHTML = `<div class="error">${getUIText(messageKey)}</div>`;
        }
    });
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
    banner.innerHTML = `
        <strong>DEBUG MODE</strong>
        ${state.dateOverride ? `| Date: ${state.dateOverride}` : ''}
        ${state.timeOverride ? `| Time: ${state.timeOverride}` : ''}
        | <a href="?">Exit debug</a>
    `;
    banner.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #ff5722;
        color: white;
        padding: 8px 16px;
        text-align: center;
        font-size: 14px;
        z-index: 9999;
    `;
    banner.querySelector('a').style.color = 'white';
    document.body.prepend(banner);
    document.body.style.paddingTop = '40px';
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

/**
 * Render date selector for debug mode
 */
function renderDateSelector(containerId, dates, currentDate) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';

    if (dates.length === 0) {
        container.innerHTML = '<div class="empty-state">No dates available</div>';
        return;
    }

    const selectorDiv = document.createElement('div');
    selectorDiv.className = 'date-selector';
    selectorDiv.style.cssText = 'display: flex; flex-wrap: wrap; gap: 8px; padding: 16px;';

    dates.forEach(date => {
        const btn = document.createElement('button');
        btn.textContent = date;
        btn.className = date === currentDate ? 'lang-btn active' : 'lang-btn';
        btn.onclick = () => {
            const url = new URL(window.location);
            url.searchParams.set('debug', 'true');
            url.searchParams.set('date', date);
            window.location.href = url.toString();
        };
        selectorDiv.appendChild(btn);
    });

    container.appendChild(selectorDiv);
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
