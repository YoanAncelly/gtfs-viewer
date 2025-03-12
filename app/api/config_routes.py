#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request
from app.utils.config_manager import (
    load_config, save_config, add_source, 
    update_source, remove_source, set_current_source
)
import requests

# Create a Blueprint for the config API routes
config_api = Blueprint('config_api', __name__)


@config_api.route('/api/config', methods=['GET'])
def api_config():
    """
    Get the current configuration
    """
    return jsonify(load_config())


@config_api.route('/api/config/save', methods=['POST'])
def api_config_save():
    """
    Save the configuration
    """
    config = request.json
    if save_config(config):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to save configuration'}), 500


@config_api.route('/api/config/add-source', methods=['POST'])
def api_config_add_source():
    """
    Add a new data source
    """
    source = request.json
    
    # Validate the source
    required_fields = ['name']
    for field in required_fields:
        if field not in source:
            return jsonify({
                'status': 'error', 
                'message': f'Missing required field: {field}'
            }), 400
    
    # Apply defaults
    defaults = {
        'active': True,
        'trip_update_url': '',
        'vehicle_position_url': '',
        'alert_url': '',
        'use_local_files': True
    }
    
    for key, value in defaults.items():
        if key not in source:
            source[key] = value
    
    if add_source(source):
        return jsonify({'status': 'success', 'source': source})
    return jsonify({'status': 'error', 'message': 'Failed to add source'}), 500


@config_api.route('/api/config/update-source/<int:index>', methods=['PUT'])
def api_config_update_source(index):
    """
    Update an existing data source
    """
    source = request.json
    
    # Validate the source
    required_fields = ['name']
    for field in required_fields:
        if field not in source:
            return jsonify({
                'status': 'error', 
                'message': f'Missing required field: {field}'
            }), 400
    
    if update_source(index, source):
        return jsonify({'status': 'success', 'source': source})
    return jsonify({'status': 'error', 'message': 'Failed to update source'}), 500


@config_api.route('/api/config/remove-source/<int:index>', methods=['DELETE'])
def api_config_remove_source(index):
    """
    Remove a data source
    """
    config = load_config()
    
    if index < 0 or index >= len(config['sources']):
        return jsonify({
            'status': 'error', 
            'message': 'Invalid source index'
        }), 400
    
    if len(config['sources']) <= 1:
        return jsonify({
            'status': 'error', 
            'message': 'Cannot remove the last source'
        }), 400
    
    if remove_source(index):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Failed to remove source'}), 500


@config_api.route('/api/config/set-current-source/<int:index>', methods=['POST'])
def api_config_set_current_source(index):
    """
    Set the current active data source
    """
    config = load_config()
    
    if index < 0 or index >= len(config['sources']):
        return jsonify({
            'status': 'error', 
            'message': 'Invalid source index'
        }), 400
    
    if set_current_source(index):
        return jsonify({'status': 'success', 'current_source': index})
    return jsonify({'status': 'error', 'message': 'Failed to set current source'}), 500


@config_api.route('/api/config/test-source', methods=['POST'])
def api_config_test_source():
    """
    Test a data source by attempting to download from the URLs
    """
    source = request.json
    results = {
        'trip_update': False,
        'vehicle_position': False,
        'alert': False
    }
    
    # Test each URL
    for feed_type in results.keys():
        url_key = f"{feed_type}_url"
        if url_key in source and source[url_key]:
            try:
                response = requests.get(source[url_key], timeout=10)
                results[feed_type] = response.status_code == 200
            except Exception:
                results[feed_type] = False
    
    return jsonify({
        'status': 'success',
        'results': results
    })
