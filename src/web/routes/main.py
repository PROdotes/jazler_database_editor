"""
Main routes - home, database selection.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from src.web.app import reset_services

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page - database selector or dashboard."""
    connections = current_app.config['CONNECTIONS']
    databases = connections.get('databases', {})
    
    # If already connected, show dashboard
    if session.get('db_name'):
        return render_template('index.html', 
                             databases=databases,
                             connected=True)
    
    # Otherwise show connection page
    return render_template('index.html', 
                         databases=databases,
                         connected=False)


@main_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to a database."""
    db_name = request.form.get('database', 'jazler_test')
    
    # Store in session
    session['db_name'] = db_name
    session['is_live'] = 'live' in db_name.lower()
    
    # Auto-sync Test DB from Live if possible
    if db_name == 'jazler_test':
        connections = current_app.config['CONNECTIONS']
        live_config = connections.get('databases', {}).get('jazler_live', {})
        live_path = live_config.get('path')
        
        from src.utils.db_sync import sync_test_db
        synced_path, was_copied = sync_test_db(live_path)
        
        if synced_path:
            if was_copied:
                flash("Test DB successfully refreshed from Live terminal.", "success")
            else:
                flash("Using existing Test DB copy found in Downloads folder.", "info")
            session['active_db_path'] = synced_path
        else:
            flash("Could not sync Test DB. Using default path.", "warning")
            db_config = connections.get('databases', {}).get(db_name, {})
            session['active_db_path'] = db_config.get('path')
    else:
        connections = current_app.config['CONNECTIONS']
        db_config = connections.get('databases', {}).get(db_name, {})
        session['active_db_path'] = db_config.get('path')
    
    # Clear cached connections to force reconnect
    reset_services()
    
    return redirect(url_for('songs.search'))


@main_bp.route('/toggle-offline', methods=['POST'])
def toggle_offline():
    """Toggle manual offline mode."""
    current = session.get('offline_mode', False)
    session['offline_mode'] = not current
    status = "ON (Drafting Mode)" if not current else "OFF (Live Editing)"
    flash(f"Offline Mode: {status}", "info")
    return redirect(request.referrer or url_for('main.index'))


@main_bp.route('/disconnect')
def disconnect():
    """Disconnect and return to home."""
    # Clear session and cached objects
    reset_services()
    session.clear()
    
    return redirect(url_for('main.index'))
