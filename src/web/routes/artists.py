from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g, current_app
from src.web.app import get_artist_service

bp = Blueprint('artists', __name__, url_prefix='/artists')

@bp.route('/search')
def search():
    """JSON search API for entity picker."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    service = get_artist_service(current_app)
    results = service.search(query)
    
    # Format for Select2 or generic autocomplete
    return jsonify([
        {'id': r['AUID'], 'text': r['fldName']} 
        for r in results
    ])

@bp.route('/create', methods=['POST'])
def create():
    """AJAX endpoint to create a new artist."""
    name = request.form.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
        
    service = get_artist_service(current_app)
    try:
        new_id = service.create(name)
        return jsonify({'id': new_id, 'text': name, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/')
def index():
    """Artist Manager Dashboard."""
    service = get_artist_service(current_app)
    # Default limit 2000 for performance
    valid_limit = 2000 
    
    query = request.args.get('q')
    artists = service.get_all_with_counts(limit=valid_limit, query_filter=query)
    
    return render_template('artists/index.html', artists=artists)

@bp.route('/update/<int:id>', methods=['POST'])
def update(id):
    """
    Update artist details (e.g., rename).
    Handles rename propagation via Service.
    """
    data = request.json or request.form
    new_name = data.get('name')
    
    if not new_name:
        return jsonify({'error': 'Name is required'}), 400
        
    service = get_artist_service(current_app)
    
    # Check for name collision
    existing = service.get_by_name(new_name)
    if existing and existing['AUID'] != id:
        return jsonify({
            'error': f"Artist '{new_name}' already exists (ID: {existing['AUID']}). Please use Merge instead."
        }), 409
        
    try:
        success = service.update(id, {'fldName': new_name})
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Update failed in backend'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/merge', methods=['POST'])
def merge():
    """
    Merge two artists.
    Source ID -> Target ID.
    Source is deleted.
    """
    data = request.json or request.form
    source_id = data.get('source_id')
    target_id = data.get('target_id')
    
    if not source_id or not target_id:
        return jsonify({'error': 'Source and Target IDs are required'}), 400
        
    service = get_artist_service(current_app)
    try:
        success = service.merge(int(source_id), int(target_id))
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Merge failed in backend'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
