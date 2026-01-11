"""
Song routes - search, browse, view, edit.
"""

import os
import logging
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from src.web.app import get_song_service, get_media_service, get_sync_service

logger = logging.getLogger(__name__)
songs_bp = Blueprint('songs', __name__)


# ─────────────────────────────────────────────────────────────
# Search & Navigation
# ─────────────────────────────────────────────────────────────

@songs_bp.route('/')
def search():
    """Song search page."""
    service = get_song_service(current_app)
    if not service:
        return redirect(url_for('main.index'))
    
    # Get search parameters from query string or session
    field = request.args.get('field', session.get('last_field', 'artist'))
    value = request.args.get('value', session.get('last_value', ''))
    match = request.args.get('match', session.get('last_match', 'contains'))
    
    results = None
    position = 0
    
    if value or match == 'is_empty':
        # Save search to session
        session['last_field'] = field
        session['last_value'] = value
        session['last_match'] = match
        
        # Execute search
        results = service.search(field, value, match, limit=500)
        
        # Store result IDs in session for batch navigation
        session['result_ids'] = [r.primary_key for r in results]
        
        # Handle position navigation
        pos_str = request.args.get('pos')
        if pos_str:
            position = int(pos_str)
            results.position = position
    
            position = int(pos_str)
            results.position = position
    
    # Dynamic field list from schema
    search_fields = service.get_searchable_fields()
    
    # Get Grid Columns from Registry
    from src.web.app import get_registry
    registry = get_registry(current_app)
    
    # Default view for now (could be session-based later)
    view_name = session.get('grid_view', 'default')
    col_names = registry.get_grid_view(view_name)
    
    # Resolve to definitions
    table_def = registry.get_table('snDatabase')
    grid_columns = []
    if table_def:
        for name in col_names:
            col = table_def.get_column(name)
            if col: grid_columns.append(col)
            
    return render_template('songs/search.html',
                         search_fields=search_fields,
                         field=field,
                         value=value,
                         match=match,
                         results=results,
                         position=position,
                         grid_columns=grid_columns,
                         pk_field=table_def.primary_key,
                         active_view=view_name,
                         available_views=registry.get_available_views())

@songs_bp.route('/set-view/<view_name>')
def set_view(view_name):
    """Set the active grid view."""
    session['grid_view'] = view_name
    return redirect(url_for('songs.search'))


def get_nav_context(song_id: int) -> dict:
    """Get navigation context for batch editing."""
    result_ids = session.get('result_ids', [])
    if not result_ids or song_id not in result_ids:
        return {'prev_id': None, 'next_id': None, 'position': 0, 'total': 0}
    
    idx = result_ids.index(song_id)
    return {
        'prev_id': result_ids[idx - 1] if idx > 0 else None,
        'next_id': result_ids[idx + 1] if idx < len(result_ids) - 1 else None,
        'position': idx + 1,
        'total': len(result_ids)
    }


# ─────────────────────────────────────────────────────────────
# Individual Record Operations
# ─────────────────────────────────────────────────────────────

@songs_bp.route('/<int:song_id>')
def view(song_id):
    """View a single song."""
    service = get_song_service(current_app)
    if not service: return redirect(url_for('main.index'))
    
    song = service.get_by_id(song_id)
    if not song:
        return render_template('songs/not_found.html', song_id=song_id), 404
    
    display_data = service.get_display_data(song)
    nav_context = get_nav_context(song_id)
    media_service = get_media_service(current_app)
    file_info = media_service.get_file_info(song.filename)
    
    return render_template('songs/view.html',
                         song=song,
                         display_data=display_data,
                         file_info=file_info,
                         search_value=session.get('last_value', ''),
                         nav=nav_context)


@songs_bp.route('/<int:song_id>/edit')
def edit(song_id):
    """Edit a song."""
    service = get_song_service(current_app)
    if not service: return redirect(url_for('main.index'))
    
    song = service.get_by_id(song_id)
    if not song:
        return render_template('songs/not_found.html', song_id=song_id), 404
    
    display_data = service.get_display_data(song)
    nav_context = get_nav_context(song_id)
    media_service = get_media_service(current_app)
    file_info = media_service.get_file_info(song.filename)
    
    id3_data = None
    if file_info['exists']:
        id3_data = read_id3_tags(file_info['resolved_path'])
    elif file_info['vfs_status'] == 'virtual' and file_info['metadata']:
        id3_data = file_info['metadata']
    
    return render_template('songs/edit.html',
                         song=song,
                         display_data=display_data,
                         file_info=file_info,
                         id3_data=id3_data,
                         nav=nav_context,
                         genre_map=service.genre_map,
                         decade_map=service.decade_map,
                         tempo_map=service.tempo_map)


@songs_bp.route('/<int:song_id>/save', methods=['POST'])
def save(song_id):
    """Save song changes."""
    service = get_song_service(current_app)
    if not service: return redirect(url_for('main.index'))
    
    song = service.get_by_id(song_id)
    if not song:
        flash('Song not found', 'error')
        return redirect(url_for('songs.search'))
    
    fields_to_update = {}
    
    # Text & Boolean fields
    for field in ['title', 'album', 'composer', 'publisher', 'isrc']:
        form_value = request.form.get(field, '').strip()
        current_value = getattr(song, field, '') or ''
        
        # Special handling for ISRC (allow null)
        if field == 'isrc' and not form_value:
            form_value = None

        if form_value != current_value:
            fields_to_update[service._resolve_field_name(field)] = form_value
            
    # Toggles (Enabled, EnabledAuto)
    toggles = {
        'enabled': 'fldEnabled',
        'enabled_auto': 'fldEnabledAuto'
    }
    
    for form_key, db_col in toggles.items():
        is_on = request.form.get(form_key) == 'on'
        # Get current value (handle None as False)
        current_val = bool(getattr(song, form_key.replace('_', ''), False) or False)
        
        if is_on != current_val:
            fields_to_update[db_col] = is_on

    # Numeric/Lookup fields
    # We use resolve_field_name so we respect the schema registry
    numeric_fields = ['year', 'genre', 'subcat1', 'subcat2', 'decade', 'tempo']
    
    for field in numeric_fields:
        val_str = request.form.get(field, '').strip()
        db_col = service._resolve_field_name(field)
        
        try:
            val_int = int(val_str) if val_str else 0
            
            # Record access via db_col
            current_val = song[db_col] or 0
            
            if val_int != current_val:
                fields_to_update[db_col] = val_int
        except ValueError:
            pass # Ignore invalid numbers
    
    media_service = get_media_service(current_app)
    rename_physical = request.form.get('rename_physical') == 'on'
    
    if fields_to_update or rename_physical:
        sync_service = get_sync_service(current_app)
        try:
            if rename_physical:
                if media_service.exists(media_service.resolve_path(song.filename)):
                    new_basis = f"{song.artist} - {request.form.get('title', song.title)}"
                    new_db_path = media_service.rename_file(song.filename, new_basis)
                    if new_db_path and new_db_path != song.filename:
                        fields_to_update['fldFilename'] = new_db_path
                else:
                    extension = os.path.splitext(song.filename)[1]
                    new_name = media_service.sanitize_filename(f"{song.artist} - {request.form.get('title', song.title)}") + extension
                    new_db_path = os.path.join(os.path.dirname(song.filename), new_name).replace('/', '\\')
                    fields_to_update['fldFilename'] = new_db_path

            if fields_to_update:
                offline_mode = session.get('offline_mode', False)
                if offline_mode:
                    sync_service.queue_change(song_id, song.artist, song.title, fields_to_update)
                    flash(f'Offline Mode: Changes for #{song_id} queued.', 'info')
                else:
                    try:
                        success = service.backend.update(service._table, song_id, fields_to_update, primary_key_column=service.DEFAULT_PK)
                        if success: flash(f'Song #{song_id} saved successfully!', 'success')
                        else: flash('No changes were made', 'warning')
                    except Exception as db_err:
                        # Fallback to queue if DB fails (e.g. connection lost)
                        sync_service.queue_change(song_id, song.artist, song.title, fields_to_update)
                        flash(f'Station Offline: Changes for #{song_id} queued for sync.', 'info')
        except Exception as e:
            logger.error(f"Save error: {e}")
            flash(f'Error saving: {str(e)}', 'error')
    else:
        flash('No changes to save', 'info')
    
    next_action = request.form.get('next_action', '')
    nav = get_nav_context(song_id)
    if next_action == 'next' and nav['next_id']: return redirect(url_for('songs.edit', song_id=nav['next_id']))
    elif next_action == 'prev' and nav['prev_id']: return redirect(url_for('songs.edit', song_id=nav['prev_id']))
    
    return redirect(url_for('songs.view', song_id=song_id))


# ─────────────────────────────────────────────────────────────
# Bulk Operations
# ─────────────────────────────────────────────────────────────

@songs_bp.route('/bulk-edit', methods=['POST'])
def bulk_edit():
    """Show bulk edit form for selected songs."""
    service = get_song_service(current_app)
    if not service: return redirect(url_for('main.index'))
    
    id_list = [int(sid) for sid in request.form.get('ids', '').split(',') if sid]
    if not id_list:
        flash('No songs selected', 'warning')
        return redirect(url_for('songs.search'))
    
    songs = [service.get_by_id(sid) for sid in id_list if service.get_by_id(sid)]
    if not songs:
        flash('Selected songs not found', 'error')
        return redirect(url_for('songs.search'))

    common_values = service.get_bulk_summary(id_list)

    return render_template('songs/bulk_edit.html',
                         songs=songs,
                         ids=request.form.get('ids'),
                         common=common_values,
                         genre_map=service.genre_map,
                         decade_map=service.decade_map,
                         tempo_map=service.tempo_map)


@songs_bp.route('/bulk-save', methods=['POST'])
def bulk_save():
    """Execute bulk update for selected songs."""
    service = get_song_service(current_app)
    sync_service = get_sync_service(current_app)
    if not service: return redirect(url_for('main.index'))
    
    id_list = [int(sid) for sid in request.form.get('ids', '').split(',') if sid]
    if not id_list:
        flash('No songs selected', 'warning')
        return redirect(url_for('songs.search'))

    # Build the update payload
    updates = {}
    mapping = {
        'genre': ('fldCat1a', int),
        'decade': ('fldCat2', int),
        'tempo': ('fldCat3', int),
        'album': ('fldAlbum', str),
        'publisher': ('fldPublisher', str),
        'year': ('fldYear', int)
    }

    # Handle Artist separately (requires ID lookup + Name propagation)
    if request.form.get('update_artist') == 'on':
        try:
            from src.web.app import get_artist_service
            artist_service = get_artist_service(current_app)
            new_artist_id = int(request.form.get('fldArtistCode', 0))
            
            if new_artist_id > 0:
                artist_rec = artist_service.get_by_id(new_artist_id)
                if artist_rec:
                    updates['fldArtistCode'] = new_artist_id
                    updates['fldArtistName'] = artist_rec['fldName']
        except ValueError:
            pass # Invalid ID or empty

    for form_key, (db_field, cast_func) in mapping.items():
        if request.form.get(f'update_{form_key}') == 'on':
            val = request.form.get(form_key, '').strip()
            try: updates[db_field] = cast_func(val) if val else None
            except: updates[db_field] = val

    do_path_swap = request.form.get('update_path_swap') == 'on'
    path_old = request.form.get('path_old', '')
    path_new = request.form.get('path_new', '')
    
    do_trim = request.form.get('trim_whitespace') == 'on'

    if not updates and not do_path_swap and not do_trim:
        flash('No changes selected to apply.', 'info')
        return redirect(url_for('songs.search'))

    offline_mode = session.get('offline_mode', False)
    success_count = 0

    for sid in id_list:
        try:
            song_updates = updates.copy()
            song = service.get_by_id(sid)
            if not song: continue

            # Apply Path Swap
            if do_path_swap and song.filename and path_old:
                new_filename = song.filename.replace(path_old, path_new)
                if new_filename != song.filename:
                    song_updates['fldFilename'] = new_filename
            
            # Apply Whitespace Trim
            if do_trim:
                for field_name, db_col in [('title', 'fldTitle'), ('album', 'fldAlbum'), ('composer', 'fldComposer'), ('publisher', 'fldPublisher')]:
                    current_val = getattr(song, field_name)
                    if current_val and isinstance(current_val, str):
                        trimmed = current_val.strip()
                        if trimmed != current_val:
                            song_updates[db_col] = trimmed

            if not song_updates: continue

            if offline_mode:
                sync_service.queue_change(sid, song.artist if song else "Multiple", "Bulk Update", song_updates)
                success_count += 1
            else:
                if service.backend.update(service._table, sid, song_updates, primary_key_column=service.DEFAULT_PK):
                    success_count += 1
        except Exception as e:
            logger.error(f"Bulk update failed for #{sid}: {e}")

    if success_count > 0:
        msg = f'Successfully updated {success_count} songs.'
        if offline_mode: msg = f'Queued updates for {success_count} songs for sync.'
        flash(msg, 'success')
    else:
        flash('Bulk update failed. See logs for details.', 'error')

    return redirect(url_for('songs.search'))


@songs_bp.route('/bulk-disable', methods=['POST'])
def bulk_disable():
    """Disable multiple songs at once."""
    service = get_song_service(current_app)
    sync_service = get_sync_service(current_app)
    if not service: return redirect(url_for('main.index'))
    
    id_list = [int(sid) for sid in request.form.get('ids', '').split(',') if sid]
    if not id_list:
        flash('No songs selected', 'warning')
        return redirect(url_for('songs.search'))

    updates = {'fldEnabled': 0}
    offline_mode = session.get('offline_mode', False)
    
    if offline_mode:
        for sid in id_list:
            sync_service.queue_change(sid, "Bulk", "Disable", updates)
        success_count = len(id_list)
    else:
        success_count = service.perform_bulk_update(id_list, updates)

    if success_count > 0:
        flash(f'Successfully disabled {success_count} songs.', 'success')
    else:
        flash('Bulk disable failed.', 'error')

    return redirect(url_for('songs.search'))


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def read_id3_tags(filepath: str) -> dict:
    """Read ID3 tags from a file (mutagen)."""
    try:
        from mutagen.easyid3 import EasyID3
        from mutagen.mp3 import MP3
        audio = MP3(filepath, ID3=EasyID3)
        return {
            'artist': audio.get('artist', [None])[0],
            'title': audio.get('title', [None])[0],
            'album': audio.get('album', [None])[0],
            'year': audio.get('date', [None])[0],
            'genre': audio.get('genre', [None])[0],
        }
    except Exception as e:
        logger.debug(f"ID3 read failed: {e}")
        return None
