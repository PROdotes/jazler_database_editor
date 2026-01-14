"""
Import Routes - Web UI for importing orphan files.

Provides endpoints for:
- Selecting files for import
- Previewing import results
- Executing the import with conflict resolution
"""

import logging
import os
import tempfile
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify

from src.services.import_parser import ImportStatus

logger = logging.getLogger(__name__)

import_bp = Blueprint('import', __name__, url_prefix='/import')


def get_import_service(app):
    """Get the ImportService from app context."""
    from src.web.app import get_services
    services = get_services(app)
    return services.get('import_service')


def get_audit_service(app):
    """Get the AuditService from app context."""
    from src.web.app import get_services
    services = get_services(app)
    return services.get('audit_service')


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@import_bp.route('/')
def index():
    """Show import landing page with option to scan for orphans."""
    return render_template('import/index.html')


@import_bp.route('/scan', methods=['POST'])
def scan():
    """Scan for orphan files and store in session."""
    audit_service = get_audit_service(current_app)
    if not audit_service:
        flash('Audit service not available', 'error')
        return redirect(url_for('import.index'))

    try:
        orphan_files = audit_service.find_untracked_files()
        # Store in session for selection
        session['orphan_files'] = orphan_files
        flash(f'Found {len(orphan_files)} untracked files', 'success')
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        flash(f'Scan failed: {str(e)}', 'error')
        return redirect(url_for('import.index'))


    return redirect(url_for('import.select'))


@import_bp.route('/manual_upload', methods=['POST'])
def manual_upload():
    """Handle manual file upload for testing import logic."""
    import_service = get_import_service(current_app)
    if not import_service:
        flash('Import service not available', 'error')
        return redirect(url_for('import.index'))

    if 'files' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('import.index'))

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('import.index'))

    temp_paths = []
    temp_dir = os.path.join(tempfile.gettempdir(), 'jazler_import_test')
    os.makedirs(temp_dir, exist_ok=True)

    try:
        for file in files:
            if file and file.filename.endswith('.mp3'):
                filename = secure_filename(file.filename)
                path = os.path.join(temp_dir, filename)
                file.save(path)
                temp_paths.append(path)

        if not temp_paths:
            flash('No valid MP3 files uploaded', 'warning')
            return redirect(url_for('import.index'))

        # Run preview
        candidates = import_service.preview_import(temp_paths)

        # Store candidates in session
        session['import_candidates'] = [
            {
                'file_path': c.file_path,
                'artist': c.metadata.artist,
                'title': c.metadata.title,
                'album': c.metadata.album,
                'year': c.metadata.year,
                'genre': c.metadata.genre,
                'duration': c.metadata.duration,
                'status': c.status.value,
                'existing_song_id': c.existing_song_id,
                'existing_path': c.existing_path,
                'existing_data': c.existing_data,
                'artist_id': c.artist_id,
                'artist_is_new': c.artist_is_new,
                'genre_ids': c.genre_ids,
                'decade_id': c.decade_id,
                'confidence': c.metadata.confidence,
                'source': c.metadata.source.value,
                'insertion_data': import_service.get_insertion_data(c),
                'insertion_diff': c.existing_data.get('_diff') if c.existing_data and '_diff' in c.existing_data else None,
            }
            for c in candidates
        ]

        # Count by status
        status_counts = {
            'new': sum(1 for c in candidates if c.status == ImportStatus.NEW),
            'duplicate': sum(1 for c in candidates if c.status == ImportStatus.DUPLICATE),
            'conflict': sum(1 for c in candidates if c.status == ImportStatus.CONFLICT),
        }

        # Get lookup maps
        genre_map = import_service.song_service.genre_map
        decade_map = import_service.song_service.decade_map

        return render_template(
            'import/preview.html',
            candidates=session['import_candidates'],
            status_counts=status_counts,
            genre_map=genre_map,
            decade_map=decade_map
        )

    except Exception as e:
        logger.error(f"Manual upload preview failed: {e}", exc_info=True)
        flash(f'Preview failed: {str(e)}', 'error')
        return redirect(url_for('import.index'))



@import_bp.route('/select')
def select():
    """Show orphan files for selection."""
    orphan_files = session.get('orphan_files', [])
    if not orphan_files:
        flash('No orphan files found. Run a scan first.', 'info')
        return redirect(url_for('import.index'))

    return render_template('import/select.html', files=orphan_files)


@import_bp.route('/preview', methods=['POST'])
def preview():
    """Preview import results for selected files."""
    import_service = get_import_service(current_app)
    if not import_service:
        flash('Import service not available', 'error')
        return redirect(url_for('import.index'))

    # Get selected files from form
    selected_files = request.form.getlist('files')
    if not selected_files:
        flash('No files selected', 'warning')
        return redirect(url_for('import.select'))

    try:
        # Run preview
        candidates = import_service.preview_import(selected_files)

        # Store candidates in session for execute step
        # Convert to serializable format
        session['import_candidates'] = [
            {
                'file_path': c.file_path,
                'artist': c.metadata.artist,
                'title': c.metadata.title,
                'album': c.metadata.album,
                'year': c.metadata.year,
                'genre': c.metadata.genre,
                'duration': c.metadata.duration,
                'status': c.status.value,
                'existing_song_id': c.existing_song_id,
                'existing_path': c.existing_path,
                'existing_data': c.existing_data,  # Full record for side-by-side comparison
                'artist_id': c.artist_id,
                'artist_is_new': c.artist_is_new,
                'genre_ids': c.genre_ids,
                'decade_id': c.decade_id,
                'confidence': c.metadata.confidence,
                'source': c.metadata.source.value,
                'insertion_data': import_service.get_insertion_data(c),
                'insertion_diff': c.existing_data.get('_diff') if c.existing_data and '_diff' in c.existing_data else None,
            }
            for c in candidates
        ]

        # Count by status
        status_counts = {
            'new': sum(1 for c in candidates if c.status == ImportStatus.NEW),
            'duplicate': sum(1 for c in candidates if c.status == ImportStatus.DUPLICATE),
            'conflict': sum(1 for c in candidates if c.status == ImportStatus.CONFLICT),
        }

        # Get lookup maps for resolved names in comparison view
        genre_map = import_service.song_service.genre_map
        decade_map = import_service.song_service.decade_map

        return render_template(
            'import/preview.html',
            candidates=session['import_candidates'],
            status_counts=status_counts,
            genre_map=genre_map,
            decade_map=decade_map
        )

    except Exception as e:
        logger.error(f"Preview failed: {e}", exc_info=True)
        flash(f'Preview failed: {str(e)}', 'error')
        return redirect(url_for('import.select'))


@import_bp.route('/execute', methods=['POST'])
def execute():
    """Execute the import with user decisions."""
    import_service = get_import_service(current_app)
    if not import_service:
        flash('Import service not available', 'error')
        return redirect(url_for('import.index'))

    candidates_data = session.get('import_candidates', [])
    if not candidates_data:
        flash('No candidates found. Run preview first.', 'warning')
        return redirect(url_for('import.index'))

    try:
        from src.services.import_parser import (
            ImportCandidate, ParsedMetadata, ParseSource, ImportStatus
        )

        # Rebuild candidates with user decisions
        candidates = []
        for data in candidates_data:
            # Get user decision for this file (from form)
            file_key = data['file_path'].replace('\\', '_').replace('/', '_').replace(':', '_')
            user_decision = request.form.get(f'decision_{file_key}', 'skip')

            meta = ParsedMetadata(
                artist=data['artist'],
                title=data['title'],
                album=data.get('album', ''),
                year=data.get('year', 0),
                genre=data.get('genre', ''),
                duration=data.get('duration', 0.0),
                source=ParseSource(data.get('source', 'fallback')),
                confidence=data.get('confidence', 0.0)
            )

            candidate = ImportCandidate(
                file_path=data['file_path'],
                metadata=meta,
                status=ImportStatus(data['status']),
                existing_song_id=data.get('existing_song_id'),
                existing_path=data.get('existing_path'),
                artist_id=data.get('artist_id'),
                artist_is_new=data.get('artist_is_new', False),
                genre_ids=data.get('genre_ids', [18, 0, 0]),
                decade_id=data.get('decade_id', 0),
                user_decision=user_decision
            )
            candidates.append(candidate)

        # Execute import
        summary = import_service.execute_import(candidates)

        # Clear cache after import
        import_service.clear_cache()

        # Clear session data
        session.pop('import_candidates', None)
        session.pop('orphan_files', None)

        return render_template('import/results.html', summary=summary)

    except Exception as e:
        logger.error(f"Execute failed: {e}", exc_info=True)
        flash(f'Import failed: {str(e)}', 'error')
        return redirect(url_for('import.index'))


@import_bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint to analyze a single file (for AJAX)."""
    import_service = get_import_service(current_app)
    if not import_service:
        return jsonify({'error': 'Import service not available'}), 500

    file_path = request.json.get('file_path')
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400

    try:
        candidates = import_service.preview_import([file_path])
        if candidates:
            c = candidates[0]
            return jsonify({
                'artist': c.metadata.artist,
                'title': c.metadata.title,
                'album': c.metadata.album,
                'year': c.metadata.year,
                'genre': c.metadata.genre,
                'duration': c.metadata.duration,
                'status': c.status.value,
                'confidence': c.metadata.confidence,
                'source': c.metadata.source.value,
            })
        return jsonify({'error': 'No result'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
