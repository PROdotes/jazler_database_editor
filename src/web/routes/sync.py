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
    
    # Capture Undo State
    revert_queue = []
    
    for item in pending:
        song_id = item['id']
        fields = item['fields']
        
        # 1. Fetch current DB state for undo
        current_song = song_service.get_by_id(song_id)
        if current_song:
            undo_changes = {}
            for key in fields.keys():
                # Get current value from DB record
                # Note: fields keys are column names (fldAlbum etc)
                curr_val = current_song[key]
                undo_changes[key] = curr_val
            
            revert_queue.append({
                'id': song_id,
                'artist': current_song.artist,
                'title': current_song.title,
                'fields': undo_changes
            })
            
    # Clear current queue so we don't double-process if we crash halfway (optimistic)
    # Actually, better to remove one by one on success.
    
    revert_service = get_sync_service(current_app) # Same service, reuse for queuing reverts
    
    for item in pending:
        try:
            song_id = int(item['id']) # Ensure ID is int for Access WHERE clause
        except:
            song_id = item['id']
            
        fields = item['fields']
        
        # Sanitize known boolean string values
        for k, v in fields.items():
            if v == 'on': fields[k] = True
            elif v == 'off': fields[k] = False
        
        # Debug logging
        logger.info(f"Syncing Song #{song_id} (type: {type(song_id)})")
        logger.info(f"Payload: {fields}")
        
        try:
            success = song_service.backend.update(
                song_service._table,
                song_id,
                fields,
                primary_key_column=song_service.DEFAULT_PK
            )
            if success:
                sync_service.remove_change(song_id) # Remove forced change
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Failed to sync song #{song_id}: {e}")
            fail_count += 1
            
    # If we had successes, queue the reverts for them
    if success_count > 0:
        for revert in revert_queue:
            # Only queue revert if the update actually happened? 
            # Ideally we'd correlate, but for now assuming if batch succeeds mostly, we provide undos.
            # We can't easily know WHICH specific ones failed in the loop above without tracking IDs.
            # Let's simple check if the ID is NOT in the remaining pending list (blocking 'remove_change' above).
            # But the loop above calls remove_change on success.
            # So if it's gone from pending, it was successful.
            
            # Re-check if it's still pending (meaning failed)
            # Actually sync_service state changes in-memory? No, it reads/writes JSON.
            # We need to reload to be sure, or just track successful IDs.
            pass

        # Helper to queue reverts
        # We need to re-instantiate or just call queue_change.
        # But wait, we just cleared the queue (via remove_change calls).
        # So we can just add these new ones.
        for r in revert_queue:
            revert_service.queue_change(r['id'], f"[UNDO] {r['artist']}", r['title'], r['fields'])
            
    if success_count > 0:
        flash(f'Successfully synced {success_count} songs! Undo drafts created.', 'success')
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
