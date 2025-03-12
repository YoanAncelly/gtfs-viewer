#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

# Configuration file path
CONFIG_FILE = 'config/config.json'

# Default configuration
DEFAULT_CONFIG = {
    'sources': [
        {
            'name': 'Local Files',
            'active': True,
            'trip_update_url': '',
            'vehicle_position_url': '',
            'alert_url': '',
            'use_local_files': True
        }
    ],
    'current_source': 0
}


def load_config():
    """
    Load configuration from config file
    
    Returns:
        dict: Configuration dictionary
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        # Create default config file if it doesn't exist
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(config):
    """
    Save configuration to config file
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def add_source(source):
    """
    Add a new data source to the configuration
    
    Args:
        source (dict): Source configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()
    config['sources'].append(source)
    return save_config(config)


def update_source(index, source):
    """
    Update an existing data source in the configuration
    
    Args:
        index (int): Index of the source to update
        source (dict): Updated source configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()
    if 0 <= index < len(config['sources']):
        config['sources'][index] = source
        return save_config(config)
    return False


def remove_source(index):
    """
    Remove a data source from the configuration
    
    Args:
        index (int): Index of the source to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()
    if 0 <= index < len(config['sources']):
        config['sources'].pop(index)
        # Adjust current_source if needed
        if config['current_source'] >= len(config['sources']):
            config['current_source'] = max(0, len(config['sources']) - 1)
        return save_config(config)
    return False


def set_current_source(index):
    """
    Set the current active data source
    
    Args:
        index (int): Index of the source to set as current
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()
    if 0 <= index < len(config['sources']):
        config['current_source'] = index
        return save_config(config)
    return False


def get_current_source():
    """
    Get the current active data source configuration
    
    Returns:
        dict: Current source configuration
    """
    config = load_config()
    if 0 <= config['current_source'] < len(config['sources']):
        return config['sources'][config['current_source']]
    return None
