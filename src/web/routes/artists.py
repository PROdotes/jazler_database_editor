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
