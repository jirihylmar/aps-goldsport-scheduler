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
};

/**
 * Initialize the application
 */
async function init() {
    // Get language from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    state.language = urlParams.get('lang') || CONFIG.defaultLanguage;

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

    renderLessons('current-lessons', state.schedule.current_lessons, 'no_current_lessons');
    renderLessons('upcoming-lessons', state.schedule.upcoming_lessons, 'no_upcoming_lessons');
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

        // Time
        card.querySelector('.time-start').textContent = lesson.start || '--:--';
        card.querySelector('.time-end').textContent = lesson.end || '--:--';

        // Level (translated)
        card.querySelector('.lesson-level').textContent =
            translateValue(lesson.level_key, 'levels');

        // Location (translated)
        card.querySelector('.lesson-location').textContent =
            translateValue(lesson.location_key, 'locations');

        // Language (translated)
        card.querySelector('.lesson-language').textContent =
            translateValue(lesson.language_key, 'languages');

        // Instructor
        const instructorEl = card.querySelector('.lesson-instructor');
        if (lesson.instructor && lesson.instructor.name) {
            card.querySelector('.instructor-name').textContent = lesson.instructor.name;
            if (lesson.instructor.photo) {
                card.querySelector('.instructor-photo').src = lesson.instructor.photo;
                card.querySelector('.instructor-photo').alt = lesson.instructor.name;
            }
        } else {
            instructorEl.style.display = 'none';
        }

        // Participants
        const participantsEl = card.querySelector('.lesson-participants');
        card.querySelector('.participant-label').textContent = getUIText('participants');

        if (lesson.participants && lesson.participants.length > 0) {
            // Show participant names
            card.querySelector('.participant-list').textContent = lesson.participants.join(', ');
            card.querySelector('.participant-count').textContent = '';
        } else if (lesson.participant_count > 0) {
            // Show count only
            card.querySelector('.participant-list').textContent = '';
            card.querySelector('.participant-count').textContent =
                `(${lesson.participant_count})`;
        } else {
            participantsEl.style.display = 'none';
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
