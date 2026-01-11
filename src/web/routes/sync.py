"""
Sync routes - manage offline changes and batch synchronization.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from src.web.app import get_sync_service, get_song_service

logger = logging.getLogger(__name__)
sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/')
def index():
    """Show pending sync changes."""
    sync_service = get_sync_service(current_app)
    pending = sync_service.get_pending()
    return render_template('sync/index.html', pending=pending)

@sync_bp.route('/apply', methods=['POST'])
def apply():
    """Apply all pending changes to the database."""
    sync_service = get_sync_service(current_app)
    song_service = get_song_service(current_app)
    
    if not song_service:
        flash('Cannot sync: Database backend is not available.', 'error')
        return redirect(url_for('sync.index'))
    
    pending = sync_service.get_pending()
    if not pending:
        flash('No pending changes to sync.', 'info')
        return redirect(url_for('sync.index'))
    
    success_count = 0
    fail_count = 0
    
    for item in pending:
        song_id = item['id']
        fields = item['fields']
        
        try:
            success = song_service.backend.update(
                song_service._table,
                song_id,
                fields,
                primary_key_column=song_service.DEFAULT_PK
            )
            if success:
                sync_service.remove_change(song_id)
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Failed to sync song #{song_id}: {e}")
            fail_count += 1
            
    if success_count > 0:
        flash(f'Successfully synced {success_count} songs!', 'success')
    if fail_count > 0:
        flash(f'Failed to sync {fail_count} songs. Check database connection.', 'error')
        
    return redirect(url_for('sync.index'))

@sync_bp.route('/discard/<int:song_id>', methods=['POST'])
def discard(song_id):
    """Discard a single pending change."""
    sync_service = get_sync_service(current_app)
    sync_service.remove_change(song_id)
    flash(f'Discarded changes for song #{song_id}.', 'info')
    return redirect(url_for('sync.index'))

@sync_bp.route('/clear', methods=['POST'])
def clear():
    """Clear all pending changes."""
    sync_service = get_sync_service(current_app)
    sync_service.clear()
    flash('All pending changes cleared.', 'info')
    return redirect(url_for('sync.index'))
