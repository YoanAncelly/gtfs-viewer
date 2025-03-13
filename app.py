#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, send_from_directory, render_template, request, redirect, url_for
from flask_cors import CORS
import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict
from datetime import datetime
import requests
import shutil

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

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

# Function to load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        # Create default config file if it doesn't exist
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

# Function to save configuration
def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# Function to download GTFS-RT data from URL
def download_gtfs_rt_from_url(url, file_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"Error downloading GTFS-RT from {url}: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading GTFS-RT from {url}: {e}")
        return False

# Function to get GTFS-RT feed based on current configuration
def get_gtfs_rt_feed(feed_type):
    config = load_config()
    current_source = config['sources'][config['current_source']]
    
    # Define GTFS-RT directory and file paths
    GTFS_RT_DIR = 'data/gtfs_rt'
    os.makedirs(GTFS_RT_DIR, exist_ok=True)
    
    file_map = {
        'trip_update': os.path.join(GTFS_RT_DIR, 'TripUpdate.pb'),
        'vehicle_position': os.path.join(GTFS_RT_DIR, 'VehiclePosition.pb'),
        'alert': os.path.join(GTFS_RT_DIR, 'Alert.pb')
    }
    
    if not current_source['use_local_files']:
        # Download the file from URL
        url_key = f"{feed_type}_url"
        if url_key in current_source and current_source[url_key]:
            file_path = file_map[feed_type]
            download_gtfs_rt_from_url(current_source[url_key], file_path)
    
    return read_gtfs_rt_file(file_map[feed_type])

# Function to read GTFS-RT files
def read_gtfs_rt_file(file_path):
    if not os.path.exists(file_path):
        print(f"Warning: GTFS-RT file not found: {file_path}")
        return None
    
    feed = gtfs_realtime_pb2.FeedMessage()
    with open(file_path, 'rb') as f:
        feed.ParseFromString(f.read())
    return feed

# Function to convert feed to dictionary
def convert_to_dict(feed):
    if not feed:
        return None
    return MessageToDict(feed)

# Process trip updates
def process_trip_updates(feed):
    if not feed:
        return None
    
    trip_updates = []
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_update = entity.trip_update
            trip_id = trip_update.trip.trip_id if trip_update.trip.HasField('trip_id') else 'Unknown'
            route_id = trip_update.trip.route_id if trip_update.trip.HasField('route_id') else 'Unknown'
            
            for stop_time_update in trip_update.stop_time_update:
                stop_id = stop_time_update.stop_id if stop_time_update.HasField('stop_id') else 'Unknown'
                delay_seconds = stop_time_update.departure.delay if stop_time_update.HasField('departure') and stop_time_update.departure.HasField('delay') else (
                    stop_time_update.arrival.delay if stop_time_update.HasField('arrival') and stop_time_update.arrival.HasField('delay') else 0
                )
                delay_minutes = round(delay_seconds / 60, 1)
                
                # Format timestamps
                arrival_time = None
                departure_time = None
                
                if stop_time_update.HasField('arrival') and stop_time_update.arrival.HasField('time'):
                    arrival_time = datetime.fromtimestamp(stop_time_update.arrival.time).strftime('%Y-%m-%d %H:%M:%S')
                
                if stop_time_update.HasField('departure') and stop_time_update.departure.HasField('time'):
                    departure_time = datetime.fromtimestamp(stop_time_update.departure.time).strftime('%Y-%m-%d %H:%M:%S')
                
                trip_updates.append({
                    'trip_id': trip_id,
                    'route_id': route_id,
                    'stop_id': stop_id,
                    'delay_seconds': delay_seconds,
                    'delay_minutes': delay_minutes,
                    'arrival_time': arrival_time,
                    'departure_time': departure_time
                })
    
    return trip_updates

# Process vehicle positions
def process_vehicle_positions(feed):
    if not feed:
        return None
    
    # Load routes data
    routes_data = load_routes_data()
    
    vehicle_positions = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            vehicle = entity.vehicle
            vehicle_id = vehicle.vehicle.id if vehicle.HasField('vehicle') and vehicle.vehicle.HasField('id') else 'Unknown'
            trip_id = vehicle.trip.trip_id if vehicle.HasField('trip') and vehicle.trip.HasField('trip_id') else 'Unknown'
            route_id = vehicle.trip.route_id if vehicle.HasField('trip') and vehicle.trip.HasField('route_id') else 'Unknown'
            
            # Get position info
            latitude = vehicle.position.latitude if vehicle.HasField('position') and vehicle.position.HasField('latitude') else None
            longitude = vehicle.position.longitude if vehicle.HasField('position') and vehicle.position.HasField('longitude') else None
            bearing = vehicle.position.bearing if vehicle.HasField('position') and vehicle.position.HasField('bearing') else None
            speed = vehicle.position.speed if vehicle.HasField('position') and vehicle.position.HasField('speed') else None
            
            # Get status
            current_status = gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.Name(vehicle.current_status) if vehicle.HasField('current_status') else 'UNKNOWN'
            
            # Format timestamp
            timestamp = datetime.fromtimestamp(vehicle.timestamp).strftime('%Y-%m-%d %H:%M:%S') if vehicle.HasField('timestamp') else None
            
            # Add route information if available
            route_info = routes_data.get(route_id, {})
            
            vehicle_positions.append({
                "vehicle_id": vehicle_id,
                "trip_id": trip_id,
                "route_id": route_id,
                "latitude": latitude,
                "longitude": longitude,
                "bearing": bearing,
                "speed": speed,
                "current_status": current_status,
                "timestamp": timestamp,
                "route_short_name": route_info.get("route_short_name", ""),
                "route_long_name": route_info.get("route_long_name", ""),
                "route_color": route_info.get("route_color", ""),
                "route_text_color": route_info.get("route_text_color", "")
            })
    
    return vehicle_positions

# Load routes data from CSV
def load_routes_data():
    routes_path = 'data/gtfs/routes.csv'
    if not os.path.exists(routes_path):
        print(f"Warning: Routes file not found: {routes_path}")
        return {}
    
    try:
        routes_df = pd.read_csv(routes_path)
        routes_dict = {}
        for _, row in routes_df.iterrows():
            routes_dict[row['route_id']] = {
                'route_short_name': row['route_short_name'] if 'route_short_name' in row and pd.notna(row['route_short_name']) else '',
                'route_long_name': row['route_long_name'] if 'route_long_name' in row and pd.notna(row['route_long_name']) else '',
                'route_color': row['route_color'] if 'route_color' in row and pd.notna(row['route_color']) else '',
                'route_text_color': row['route_text_color'] if 'route_text_color' in row and pd.notna(row['route_text_color']) else ''
            }
        return routes_dict
    except Exception as e:
        print(f"Error loading routes data: {e}")
        return {}

# Process alerts
def process_alerts(feed):
    if not feed:
        return None
    
    alerts = []
    for entity in feed.entity:
        if entity.HasField('alert'):
            alert = entity.alert
            
            # Get header and description texts
            header_text = ''
            description_text = ''
            
            if alert.HasField('header_text'):
                for translation in alert.header_text.translation:
                    if translation.language == 'fr' or not header_text:
                        header_text = translation.text
            
            if alert.HasField('description_text'):
                for translation in alert.description_text.translation:
                    if translation.language == 'fr' or not description_text:
                        description_text = translation.text
            
            # Get cause and effect
            cause = gtfs_realtime_pb2.Alert.Cause.Name(alert.cause) if alert.HasField('cause') else 'UNKNOWN_CAUSE'
            effect = gtfs_realtime_pb2.Alert.Effect.Name(alert.effect) if alert.HasField('effect') else 'UNKNOWN_EFFECT'
            
            # Get time range
            start_time = None
            end_time = None
            
            if alert.active_period:
                for period in alert.active_period:
                    if period.HasField('start'):
                        start_time = datetime.fromtimestamp(period.start).strftime('%Y-%m-%d %H:%M:%S')
                    
                    if period.HasField('end'):
                        end_time = datetime.fromtimestamp(period.end).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get affected entities
            affected_entities = []
            for informed_entity in alert.informed_entity:
                entity_info = {}
                
                if informed_entity.HasField('agency_id'):
                    entity_info['agency_id'] = informed_entity.agency_id
                
                if informed_entity.HasField('route_id'):
                    entity_info['route_id'] = informed_entity.route_id
                
                if informed_entity.HasField('route_type'):
                    entity_info['route_type'] = informed_entity.route_type
                
                if informed_entity.HasField('stop_id'):
                    entity_info['stop_id'] = informed_entity.stop_id
                
                if informed_entity.HasField('trip'):
                    if informed_entity.trip.HasField('trip_id'):
                        entity_info['trip_id'] = informed_entity.trip.trip_id
                    
                    if informed_entity.trip.HasField('route_id'):
                        entity_info['route_id'] = informed_entity.trip.route_id
                
                affected_entities.append(entity_info)
            
            alerts.append({
                'header_text': header_text,
                'description_text': description_text,
                'cause': cause,
                'effect': effect,
                'start_time': start_time,
                'end_time': end_time,
                'affected_entities': affected_entities
            })
    
    return alerts

# Generate delay distribution chart
def generate_delay_chart(trip_updates):
    if not trip_updates:
        return None
    
    delays = [update['delay_minutes'] for update in trip_updates]
    
    plt.figure(figsize=(10, 6))
    plt.hist(delays, bins=20, alpha=0.7, color='blue')
    plt.axvline(x=0, color='red', linestyle='dashed', linewidth=1)
    plt.xlabel('Retard (minutes)')
    plt.ylabel('Nombre de mises à jour')
    plt.title('Distribution des retards')
    plt.tight_layout()
    
    # Save the chart to a file
    chart_path = os.path.join('static', 'charts', 'delay_chart.png')
    plt.savefig(chart_path)
    plt.close()
    
    return 'delay_chart.png'

# Generate stats for trip updates
def get_trip_update_stats(trip_updates):
    if not trip_updates:
        return None
    
    delays = [update['delay_minutes'] for update in trip_updates]
    
    return {
        'count': len(trip_updates),
        'avg_delay_minutes': round(sum(delays) / len(delays), 1) if delays else 0,
        'max_delay_minutes': round(max(delays), 1) if delays else 0,
        'min_delay_minutes': round(min(delays), 1) if delays else 0,
        'delay_chart': generate_delay_chart(trip_updates)
    }

# Generate stats for vehicle positions
def get_vehicle_stats(vehicle_positions):
    if not vehicle_positions:
        return None
    
    # Filter out positions with no speed info
    speeds = [v['speed'] for v in vehicle_positions if v['speed'] is not None]
    
    status_counts = {}
    for vehicle in vehicle_positions:
        status = vehicle['current_status']
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
    
    return {
        'count': len(vehicle_positions),
        'avg_speed': round(sum(speeds) / len(speeds), 1) if speeds else None,
        'max_speed': round(max(speeds), 1) if speeds else None,
        'min_speed': round(min(speeds), 1) if speeds else None,
        'status_counts': status_counts
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def config():
    return render_template('config.html')

@app.route('/api/config')
def api_config():
    config = load_config()
    return jsonify(config)

@app.route('/api/config/save', methods=['POST'])
def api_config_save():
    try:
        config = request.json
        success = save_config(config)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/config/add-source', methods=['POST'])
def api_config_add_source():
    try:
        source = request.json
        
        # Validate required fields
        if 'name' not in source:
            return jsonify({'success': False, 'error': "Missing source name"}), 400
        
        # Initialize URLs if not provided
        if 'trip_update_url' not in source:
            source['trip_update_url'] = ''
        
        if 'vehicle_position_url' not in source:
            source['vehicle_position_url'] = ''
        
        if 'alert_url' not in source:
            source['alert_url'] = ''
        
        # Default to not using local files
        if 'use_local_files' not in source:
            source['use_local_files'] = False
        
        # Load current config
        config = load_config()
        
        # Add new source
        config['sources'].append(source)
        
        # Save updated config
        success = save_config(config)
        
        # Return the index of the new source
        return jsonify({'success': success, 'index': len(config['sources']) - 1 if success else -1})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/config/update-source', methods=['POST'])
def api_config_update_source():
    try:
        data = request.json
        
        # Validate required fields
        if 'index' not in data:
            return jsonify({'success': False, 'error': "Missing source index"}), 400
        
        if 'source' not in data:
            return jsonify({'success': False, 'error': "Missing source data"}), 400
        
        source = data['source']
        
        # Validate required fields in source
        if 'name' not in source:
            return jsonify({'success': False, 'error': "Missing source name"}), 400
        
        # Load current config
        config = load_config()
        
        # Validate source index
        if data['index'] < 0 or data['index'] >= len(config['sources']):
            return jsonify({'success': False, 'error': "Invalid source index"}), 400
        
        # Update source
        config['sources'][data['index']] = source
        
        # Save updated config
        success = save_config(config)
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/config/remove-source', methods=['POST'])
def api_config_remove_source():
    try:
        data = request.json
        
        # Validate source index
        if 'index' not in data:
            return jsonify({'success': False, 'error': "Missing source index"}), 400
        
        # Load current config
        config = load_config()
        
        # Validate source index
        if data['index'] < 0 or data['index'] >= len(config['sources']):
            return jsonify({'success': False, 'error': "Invalid source index"}), 400
        
        # Remove source
        config['sources'].pop(data['index'])
        
        # Update current source if needed
        if config['current_source'] >= len(config['sources']):
            config['current_source'] = len(config['sources']) - 1 if config['sources'] else 0
        
        # Save updated config
        success = save_config(config)
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/config/set-current-source', methods=['POST'])
def api_config_set_current_source():
    try:
        data = request.json
        
        # Validate source index
        if 'index' not in data:
            return jsonify({'success': False, 'error': "Missing source index"}), 400
        
        # Load current config
        config = load_config()
        
        # Validate source index
        if data['index'] < 0 or data['index'] >= len(config['sources']):
            return jsonify({'success': False, 'error': "Invalid source index"}), 400
        
        # Update current source
        config['current_source'] = data['index']
        
        # Save updated config
        success = save_config(config)
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/config/test-source', methods=['POST'])
def api_config_test_source():
    try:
        source = request.json
        results = {}
        
        # Only test URLs if not using local files
        # Use get() method with default value False if the key doesn't exist
        if not source.get('use_local_files', False):
            for feed_type in ['trip_update', 'vehicle_position', 'alert']:
                url_key = f"{feed_type}_url"
                if url_key in source and source[url_key]:
                    try:
                        response = requests.get(source[url_key])
                        results[feed_type] = {
                            'success': response.status_code == 200,
                            'status_code': response.status_code
                        }
                    except Exception as e:
                        results[feed_type] = {
                            'success': False,
                            'error': str(e)
                        }
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/refresh-data', methods=['POST'])
def api_refresh_data():
    try:
        config = load_config()
        current_source = config['sources'][config['current_source']]
        
        results = {}
        
        # Only download if not using local files
        if not current_source['use_local_files']:
            for feed_type in ['trip_update', 'vehicle_position', 'alert']:
                url_key = f"{feed_type}_url"
                if url_key in current_source and current_source[url_key]:
                    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/gtfs_rt/{feed_type.title().replace('_', '')}.pb")
                    success = download_gtfs_rt_from_url(current_source[url_key], file_path)
                    results[feed_type] = {'success': success}
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trip-updates')
def api_trip_updates():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    trip_update_path = os.path.join(current_dir, 'data/gtfs_rt', 'TripUpdate.pb')
    
    if not os.path.exists(trip_update_path):
        return jsonify({'error': 'Trip update data not found'}), 404
    
    # Read and process the trip updates
    trip_update_feed = read_gtfs_rt_file(trip_update_path)
    trip_updates = process_trip_updates(trip_update_feed)
    trip_stats = get_trip_update_stats(trip_updates)
    
    return jsonify({
        'header': {
            'version': trip_update_feed.header.gtfs_realtime_version,
            'timestamp': trip_update_feed.header.timestamp,
            'timestamp_formatted': datetime.fromtimestamp(trip_update_feed.header.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'entity_count': len(trip_update_feed.entity)
        },
        'stats': trip_stats,
        'data': trip_updates
    })

@app.route('/api/vehicle-positions')
def api_vehicle_positions():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    vehicle_position_path = os.path.join(current_dir, 'data/gtfs_rt', 'VehiclePosition.pb')
    
    if not os.path.exists(vehicle_position_path):
        return jsonify({'error': 'Vehicle position data not found'}), 404
    
    # Read and process the vehicle positions
    vehicle_position_feed = read_gtfs_rt_file(vehicle_position_path)
    vehicle_positions = process_vehicle_positions(vehicle_position_feed)
    vehicle_stats = get_vehicle_stats(vehicle_positions)
    
    return jsonify({
        'header': {
            'version': vehicle_position_feed.header.gtfs_realtime_version,
            'timestamp': vehicle_position_feed.header.timestamp,
            'timestamp_formatted': datetime.fromtimestamp(vehicle_position_feed.header.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'entity_count': len(vehicle_position_feed.entity)
        },
        'stats': vehicle_stats,
        'data': vehicle_positions
    })

@app.route('/api/alerts')
def api_alerts():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    alert_path = os.path.join(current_dir, 'data/gtfs_rt', 'Alert.pb')
    
    if not os.path.exists(alert_path):
        return jsonify({'error': 'Alert data not found'}), 404
    
    # Read and process the alerts
    alert_feed = read_gtfs_rt_file(alert_path)
    alerts = process_alerts(alert_feed)
    
    return jsonify({
        'header': {
            'version': alert_feed.header.gtfs_realtime_version,
            'timestamp': alert_feed.header.timestamp,
            'timestamp_formatted': datetime.fromtimestamp(alert_feed.header.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'entity_count': len(alert_feed.entity)
        },
        'count': len(alerts),
        'data': alerts
    })

@app.route('/api/all-data')
def api_all_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Trip updates
    trip_update_path = os.path.join(current_dir, 'data/gtfs_rt', 'TripUpdate.pb')
    trip_update_feed = get_gtfs_rt_feed('trip_update')
    trip_updates = process_trip_updates(trip_update_feed) if trip_update_feed else None
    trip_stats = get_trip_update_stats(trip_updates) if trip_updates else None
    
    # Vehicle positions
    vehicle_position_path = os.path.join(current_dir, 'data/gtfs_rt', 'VehiclePosition.pb')
    vehicle_position_feed = get_gtfs_rt_feed('vehicle_position')
    vehicle_positions = process_vehicle_positions(vehicle_position_feed) if vehicle_position_feed else None
    vehicle_stats = get_vehicle_stats(vehicle_positions) if vehicle_positions else None
    
    # Alerts
    alert_path = os.path.join(current_dir, 'data/gtfs_rt', 'Alert.pb')
    alert_feed = get_gtfs_rt_feed('alert')
    alerts = process_alerts(alert_feed) if alert_feed else None
    
    return jsonify({
        'trip_updates': {
            'header': {
                'version': trip_update_feed.header.gtfs_realtime_version if trip_update_feed else None,
                'timestamp': trip_update_feed.header.timestamp if trip_update_feed else None,
                'timestamp_formatted': datetime.fromtimestamp(trip_update_feed.header.timestamp).strftime('%Y-%m-%d %H:%M:%S') if trip_update_feed and trip_update_feed.header.timestamp else None,
                'entity_count': len(trip_update_feed.entity) if trip_update_feed else 0
            },
            'stats': trip_stats,
            'data': trip_updates
        },
        'vehicle_positions': {
            'header': {
                'version': vehicle_position_feed.header.gtfs_realtime_version if vehicle_position_feed else None,
                'timestamp': vehicle_position_feed.header.timestamp if vehicle_position_feed else None,
                'timestamp_formatted': datetime.fromtimestamp(vehicle_position_feed.header.timestamp).strftime('%Y-%m-%d %H:%M:%S') if vehicle_position_feed and vehicle_position_feed.header.timestamp else None,
                'entity_count': len(vehicle_position_feed.entity) if vehicle_position_feed else 0
            },
            'stats': vehicle_stats,
            'data': vehicle_positions
        },
        'alerts': {
            'header': {
                'version': alert_feed.header.gtfs_realtime_version if alert_feed else None,
                'timestamp': alert_feed.header.timestamp if alert_feed else None,
                'timestamp_formatted': datetime.fromtimestamp(alert_feed.header.timestamp).strftime('%Y-%m-%d %H:%M:%S') if alert_feed and alert_feed.header.timestamp else None,
                'entity_count': len(alert_feed.entity) if alert_feed else 0
            },
            'count': len(alerts) if alerts else 0,
            'data': alerts
        }
    })

if __name__ == '__main__':
    # Create static folder if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
        
    # Create charts directory if it doesn't exist
    charts_dir = os.path.join('static', 'charts')
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)
        
    # Create GTFS-RT directory if it doesn't exist
    gtfs_rt_dir = os.path.join('data', 'gtfs_rt')
    if not os.path.exists(gtfs_rt_dir):
        os.makedirs(gtfs_rt_dir)
        
    # Run the app
    app.run(debug=True)
