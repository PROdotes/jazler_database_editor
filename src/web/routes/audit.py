"""
Audit routes - library integrity reports and ghost management.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from src.web.app import get_audit_service

logger = logging.getLogger(__name__)
audit_bp = Blueprint('audit', __name__)

# Global cache for audit results to avoid session bloat
app_audit_cache = {}

@audit_bp.route('/')
def index():
    """Show audit dashboard and recent results."""
    # We store last audit results in session for simplicity, 
    # or just show the trigger button.
    results = session.get('last_audit')
    return render_template('audit/index.html', results=results)

@audit_bp.route('/run', methods=['POST'])
def run():
    """Execute the library audit."""
    service = get_audit_service(current_app)
    if not service:
        flash('Cannot run audit: Services not initialized. Connect to a database first.', 'error')
        return redirect(url_for('audit.index'))
    
    try:
        results = service.run_audit()
        # Store a summary in session, not the whole thing (too big)
        session['last_audit'] = {
            'total': results['total'],
            'found': results['found'],
            'virtual': results['virtual'],
            'moved_count': len(results['moved']),
            'missing_count': len(results['missing']),
            'timestamp': results.get('timestamp') # we didn't add timestamp yet
        }
        
        # We'll need a way to pass the full results to the report page.
        # For now, let's keep it in a global or similar if it's too big for session.
        # Actually, let's just re-run or use a cache file.
        # For this demo, let's use a simple global cache for results.
        app_audit_cache[current_app.name] = results
        
        flash('Audit complete!', 'success')
        return redirect(url_for('audit.report'))
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        flash(f"Audit failed: {e}", 'error')
        return redirect(url_for('audit.index'))

@audit_bp.route('/report')
def report():
    """Show detailed audit report."""
    results = app_audit_cache.get(current_app.name)
    if not results:
        flash('No audit data found. Please run an audit first.', 'info')
        return redirect(url_for('audit.index'))
        
    return render_template('audit/report.html', results=results)

@audit_bp.route('/run-untracked', methods=['POST'])
def run_untracked():
    """Execute the untracked files scan."""
    service = get_audit_service(current_app)
    if not service:
        flash('Service unavailable', 'error')
        return redirect(url_for('audit.index'))
        
    try:
        files = service.find_untracked_files()
        count = len(files)
        # Store in cache
        app_audit_cache[f"{current_app.name}_untracked"] = files
        
        flash(f'Scan complete. Found {count} untracked files.', 'success')
        return redirect(url_for('audit.untracked_report'))
    except Exception as e:
        logger.error(f"Untracked scan failed: {e}")
        flash(f"Scan failed: {e}", 'error')
        return redirect(url_for('audit.index'))

@audit_bp.route('/untracked-report')
def untracked_report():
    """Show untracked files report."""
    files = app_audit_cache.get(f"{current_app.name}_untracked")
    if files is None: 
        # Using None check specifically because empty list is a valid result
        flash('No scan data found. Please run a scan first.', 'info')
        return redirect(url_for('audit.index'))
        
    return render_template('audit/untracked.html', files=files)
