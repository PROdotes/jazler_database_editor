/**
 * Database Toolkit - Edit Page Tools
 * 
 * Quick tools for editing song metadata:
 * - Parse Album: Split "Album; Publisher; Year" format
 * - Trim Whitespace: Clean up all editable fields
 * - Title Case: Fix title casing
 * - Normalize feat.: Standardize featuring patterns
 * - Clear Composer: One-click clear
 */

/**
 * Highlight a field to show it was changed
 * @param {HTMLElement} field - The field to highlight
 * @param {string} color - CSS background color
 */
function highlightField(field, color = '#1a3a1a') {
    if (!field) return;
    field.style.backgroundColor = color;
    setTimeout(() => field.style.backgroundColor = '', 1500);
}

/**
 * Update the comparison icon between DB and ID3
 * @param {string} inputId - ID of the database input
 * @param {string} id3Id - ID of the ID3 display element
 */
function updateSyncStatus(inputId, id3Id) {
    const input = document.getElementById(inputId);
    const id3 = document.getElementById(id3Id);
    if (!input || !id3) return;

    const row = input.closest('.compare-row');
    if (!row) return;

    const bridgeIcon = row.querySelector('.bridge-icon');
    const icon = bridgeIcon ? bridgeIcon.querySelector('i') : null;

    // Normalize values for comparison
    const dbVal = input.value.trim().toLowerCase();
    const id3Val = id3.textContent.trim().toLowerCase();

    // ID3 values of '—' or empty should be treated as empty
    const isEmptyId3 = id3Val === '—' || id3Val === '';
    const isEmptyDb = dbVal === '';

    let match = false;
    if (isEmptyId3 && isEmptyDb) {
        match = true;
    } else if (!isEmptyId3) {
        match = (dbVal === id3Val);
    }

    // Special logic for Year/Decade: Both must match ID3 AND be consistent with each other
    if (inputId === 'year' && match) {
        const decadeSelect = document.getElementById('decade');
        if (decadeSelect && dbVal) {
            const yearNum = parseInt(dbVal);
            const decadeText = decadeSelect.options[decadeSelect.selectedIndex].text;
            const expectedDecadeStart = Math.floor(yearNum / 10) * 10;

            // Check if selected decade string contains the expected decade start year
            if (!decadeText.includes(expectedDecadeStart.toString())) {
                match = false; // Integrity fail: Year is 1993, but Decade is 2000's
            }
        }
    }

    if (match) {
        row.classList.remove('mismatch');
        row.classList.add('match');
        if (icon) {
            icon.className = 'fas fa-check';
        }
        if (bridgeIcon) bridgeIcon.title = 'Matches';
    } else {
        row.classList.remove('match');
        row.classList.add('mismatch');
        if (icon) {
            icon.className = 'fas fa-sync-alt';
        }
        if (bridgeIcon) bridgeIcon.title = 'Mismatched';
    }
}

/**
 * Update all sync statuses on the page
 */
function updateAllSyncStatuses() {
    updateSyncStatus('fldArtistCode_display', 'id3-artist');
    updateSyncStatus('title', 'id3-title');
    updateSyncStatus('album', 'id3-album');
    updateSyncStatus('year', 'id3-year');
}


/**
 * Parse the Album field if it contains "Album; Publisher; Year" format
 * and distribute the values to the appropriate fields.
 */
function parseAlbumField() {
    const albumField = document.getElementById('album');
    const yearField = document.getElementById('year');
    const publisherField = document.getElementById('publisher');

    if (!albumField) return;

    const albumValue = albumField.value.trim();

    // Check for semicolon-separated format
    if (!albumValue.includes(';')) {
        alert('Album field does not contain semicolons to parse.');
        return;
    }

    const parts = albumValue.split(';').map(p => p.trim());

    if (parts.length >= 3) {
        // Format: Album; Publisher; Year
        const album = parts[0];
        const publisher = parts[1];
        const year = parts[2];

        // Update fields
        albumField.value = album;
        highlightField(albumField);

        // Only update if target field is empty
        if (publisherField && !publisherField.value.trim()) {
            publisherField.value = publisher;
            highlightField(publisherField);
        }

        if (yearField && !yearField.value.trim() && /^\d{4}$/.test(year)) {
            yearField.value = year;
            highlightField(yearField);
        }

        updateAllSyncStatuses();
    } else if (parts.length === 2) {
        // Format: Album; Year or Album; Publisher
        const album = parts[0];
        const second = parts[1];

        albumField.value = album;
        highlightField(albumField);

        // Check if second part is a year
        if (/^\d{4}$/.test(second)) {
            if (yearField && !yearField.value.trim()) {
                yearField.value = second;
                highlightField(yearField);
            }
        } else {
            if (publisherField && !publisherField.value.trim()) {
                publisherField.value = second;
                highlightField(publisherField);
            }
        }
        updateAllSyncStatuses();
    }
}


/**
 * Trim whitespace from all editable text fields
 */
function trimWhitespace() {
    const fields = ['title', 'album', 'composer', 'publisher'];  // Not artist - it's read-only
    let trimmed = 0;

    fields.forEach(id => {
        const field = document.getElementById(id);
        if (field) {
            const original = field.value;
            const trimmedValue = original.trim();
            if (original !== trimmedValue) {
                field.value = trimmedValue;
                highlightField(field);
                trimmed++;
            }
        }
    });

    if (trimmed === 0) {
        alert('No whitespace to trim.');
    } else {
        updateAllSyncStatuses();
    }
}


/**
 * Convert Title to Title Case (not Artist - it's read-only/linked)
 */
function titleCaseTitle() {
    const field = document.getElementById('title');
    if (!field || !field.value) return;

    function toTitleCase(str) {
        return str.replace(/\w\S*/g, function (txt) {
            // Keep certain words lowercase unless first word
            const lowercaseWords = ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'of', 'in'];
            const word = txt.toLowerCase();
            if (lowercaseWords.includes(word)) {
                return word;
            }
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    }

    const original = field.value;
    // Capitalize first letter of the string regardless
    let newValue = toTitleCase(original);
    newValue = newValue.charAt(0).toUpperCase() + newValue.slice(1);

    if (original !== newValue) {
        field.value = newValue;
        highlightField(field);
        updateAllSyncStatuses();
    }
}


/**
 * Normalize "feat", "ft.", "featuring" to "feat."
 */
function normalizeFeat() {
    const field = document.getElementById('title');
    if (!field) return;

    const original = field.value;
    // Patterns to normalize
    const patterns = [
        /\s+featuring\s+/gi,
        /\s+feat\s+/gi,
        /\s+ft\.\s+/gi,
        /\s+ft\s+/gi,
        /\(featuring\s+/gi,
        /\(feat\s+/gi,
        /\(ft\.\s+/gi,
        /\(ft\s+/gi,
    ];

    let newValue = original;
    patterns.forEach(pattern => {
        if (pattern.source.startsWith('\\(')) {
            newValue = newValue.replace(pattern, '(feat. ');
        } else {
            newValue = newValue.replace(pattern, ' feat. ');
        }
    });

    if (original !== newValue) {
        field.value = newValue;
        highlightField(field);
        updateAllSyncStatuses();
    } else {
        alert('No "feat" variations found to normalize.');
    }
}


/**
 * Clear the composer field
 */
function clearComposer() {
    const field = document.getElementById('composer');
    if (field && field.value.trim()) {
        field.value = '';
        highlightField(field, '#3a1a1a'); // Red tint for clearing
    }
}

/**
 * Handle rename checkbox and preview
 */
function setupRenamePreview() {
    const checkbox = document.getElementById('rename_physical');
    const previewDiv = document.getElementById('rename-preview');
    const previewText = document.getElementById('preview-text');
    const titleInput = document.getElementById('title');

    // We get artist name from the readonly div
    const artistDiv = document.querySelector('.readonly-value');
    const artistName = artistDiv ? artistDiv.textContent.trim() : 'Unknown Artist';

    function updatePreview() {
        if (checkbox.checked) {
            const title = titleInput.value.trim() || 'Untitled';
            const sanitized = (artistName + ' - ' + title).replace(/[<>:"/\\|?*]/g, '_');
            previewText.textContent = sanitized + '.mp3'; // Extension is assumed for preview
            previewDiv.style.display = 'block';
        } else {
            previewDiv.style.display = 'none';
        }
    }

    if (checkbox) {
        checkbox.addEventListener('change', updatePreview);
        if (titleInput) {
            titleInput.addEventListener('input', updatePreview);
        }
        // Initial state
        updatePreview();
    }
}

/**
 * Setup input listeners for real-time comparison
 */
function setupSyncChecks() {
    const fields = [
        { input: 'fldArtistCode_display', id3: 'id3-artist' },
        { input: 'title', id3: 'id3-title' },
        { input: 'album', id3: 'id3-album' },
        { input: 'year', id3: 'id3-year' }
    ];

    fields.forEach(pair => {
        const input = document.getElementById(pair.input);
        if (input) {
            input.addEventListener('input', () => updateSyncStatus(pair.input, pair.id3));

            // Also listen for decade change to update the year row status
            if (pair.input === 'year') {
                const decadeSelect = document.getElementById('decade');
                if (decadeSelect) {
                    decadeSelect.addEventListener('change', () => updateSyncStatus('year', 'id3-year'));
                }
            }

            // Initial run
            updateSyncStatus(pair.input, pair.id3);
        }
    });

    // Handle entity picker selection (it might not fire 'input' if changed via JS)
    // We can poll or just hook into the picker's onclick if we had a cleaner way,
    // but the picker macro already updates the input.value.
    // Let's add an observer for the hidden artist code field just in case.
    const artistHidden = document.getElementById('fldArtistCode');
    if (artistHidden) {
        // Since input values changed via JS don't fire events, we can poll briefly
        // or just wait for the display input to change which usually happens.
        // The entity_picker macro sets input.value directly. 
        // We'll rely on the display input being updated.
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setupRenamePreview();
    setupSyncChecks();
});

console.log('🔧 Edit tools loaded');
