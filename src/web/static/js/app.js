/**
 * Database Toolkit - Client-side JavaScript
 */

// Keyboard shortcuts
document.addEventListener('keydown', function (e) {
    // F1 - Focus search
    if (e.key === 'F1') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
});

// Auto-submit search on Enter
document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    searchForm.submit();
                }
            });
        }
    }
});

console.log('🎵 Database Toolkit loaded');
