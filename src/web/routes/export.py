"""
Export routes - data portability and reporting.
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, Response, session
from src.web.app import get_export_service, get_song_service, get_audit_service

logger = logging.getLogger(__name__)
export_bp = Blueprint('export', __name__)

@export_bp.route('/')
def index():
    """Export dashboard."""
    service = get_song_service(current_app)
    if not service:
        flash('Not connected to a database.', 'warning')
        return redirect(url_for('main.index'))
        
    return render_template('export/index.html')

@export_bp.route('/download', methods=['POST'])
def download():
    """Generate and download export file."""
    export_type = request.form.get('type', 'songs_all')
    format = request.form.get('format', 'csv')
    include_resolved = request.form.get('resolve_lookups') == 'on'
    
    export_service = get_export_service(current_app)
    song_service = get_song_service(current_app)
    
    if not export_service or not song_service:
        flash('Export service not available.', 'error')
        return redirect(url_for('export.index'))

    records = []
    filename_prefix = "export"

    try:
        if export_type == 'songs_all':
            records = song_service.get_all(limit=100000)
            filename_prefix = "all_songs"
        elif export_type == 'search_results':
            ids = session.get('result_ids', [])
            if not ids:
                flash('No search results to export. Run a search first.', 'warning')
                return redirect(url_for('export.index'))
            
            # Fetch these specifically
            for sid in ids:
                rec = song_service.get_by_id(sid)
                if rec:
                    records.append(rec)
            filename_prefix = "search_results"
        elif export_type == 'selected_songs':
            id_str = request.form.get('ids', '')
            ids = id_str.split(',') if id_str else []
            if not ids:
                flash('No songs selected for export.', 'warning')
                return redirect(url_for('export.index'))
            
            for sid in ids:
                if sid:
                    rec = song_service.get_by_id(int(sid))
                    if rec:
                        records.append(rec)
            filename_prefix = "selected_songs"
        elif export_type == 'audit_ghosts':
            # Access the audit cache
            from src.web.routes.audit import app_audit_cache
            audit_results = app_audit_cache.get(current_app.name)
            
            if not audit_results:
                 flash('No audit data found. Please run an Audit first.', 'warning')
                 return redirect(url_for('audit.index'))
            
            ghosts = audit_results.get('missing', [])
            for g in ghosts:
                rec = song_service.get_by_id(g['id'])
                if rec:
                    records.append(rec)
            filename_prefix = "audit_ghosts"

        if not records:
            flash('No records found to export.', 'warning')
            return redirect(url_for('export.index'))

        # Generate content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        if format == 'csv':
            content = export_service.to_csv(records, include_resolved=include_resolved)
            mimetype = "text/csv"
            filename = f"{filename_prefix}_{timestamp}.csv"
        else:
            content = export_service.to_json(records, include_resolved=include_resolved)
            mimetype = "application/json"
            filename = f"{filename_prefix}_{timestamp}.json"

        return Response(
            content,
            mimetype=mimetype,
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Export failed: {e}")
        flash(f"Export failed: {e}", "error")
        return redirect(url_for('export.index'))
