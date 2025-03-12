#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, send_file
from app.utils.config_manager import load_config, get_current_source
from app.core.gtfs_rt_reader import read_gtfs_rt_file, convert_to_dict
import os
import pandas as pd
import requests
import csv

# Create a Blueprint for the data API routes
data_api = Blueprint('data_api', __name__)

# GTFS-RT file paths
GTFS_RT_DIR = 'data/gtfs_rt'
FILE_PATHS = {
    'trip_update': os.path.join(GTFS_RT_DIR, 'TripUpdate.pb'),
    'vehicle_position': os.path.join(GTFS_RT_DIR, 'VehiclePosition.pb'),
    'alert': os.path.join(GTFS_RT_DIR, 'Alert.pb')
}

# Ensure GTFS-RT directory exists
os.makedirs(GTFS_RT_DIR, exist_ok=True)


def download_gtfs_rt_from_url(url, file_path):
    """
    Download GTFS-RT data from URL
    
    Args:
        url (str): URL to download from
        file_path (str): Path to save the downloaded file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"Error downloading GTFS-RT from {url}: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading GTFS-RT from {url}: {e}")
        return False


def get_gtfs_rt_feed(feed_type):
    """
    Get GTFS-RT feed based on current configuration
    
    Args:
        feed_type (str): Type of feed to get (trip_update, vehicle_position, alert)
        
    Returns:
        feed: GTFS-RT feed message
    """
    current_source = get_current_source()
    
    if not current_source['use_local_files']:
        # Download the file from URL
        url_key = f"{feed_type}_url"
        if url_key in current_source and current_source[url_key]:
            file_path = FILE_PATHS[feed_type]
            download_gtfs_rt_from_url(current_source[url_key], file_path)
    
    return read_gtfs_rt_file(FILE_PATHS[feed_type])


def process_trip_updates(feed):
    """
    Process trip updates from GTFS-RT feed
    
    Args:
        feed: GTFS-RT feed message
        
    Returns:
        list: Processed trip updates
    """
    if not feed:
        return []
    
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
                    from datetime import datetime
                    arrival_time = datetime.fromtimestamp(stop_time_update.arrival.time).strftime('%Y-%m-%d %H:%M:%S')
                
                if stop_time_update.HasField('departure') and stop_time_update.departure.HasField('time'):
                    from datetime import datetime
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


def process_vehicle_positions(feed):
    """
    Process vehicle positions from GTFS-RT feed
    
    Args:
        feed: GTFS-RT feed message
        
    Returns:
        list: Processed vehicle positions
    """
    if not feed:
        return []
    
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
            from google.transit import gtfs_realtime_pb2
            current_status = gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.Name(vehicle.current_status) if vehicle.HasField('current_status') else 'UNKNOWN'
            
            # Format timestamp
            from datetime import datetime
            timestamp = datetime.fromtimestamp(vehicle.timestamp).strftime('%Y-%m-%d %H:%M:%S') if vehicle.HasField('timestamp') else None
            
            vehicle_positions.append({
                'vehicle_id': vehicle_id,
                'trip_id': trip_id,
                'route_id': route_id,
                'latitude': latitude,
                'longitude': longitude,
                'bearing': bearing,
                'speed': speed,
                'current_status': current_status,
                'timestamp': timestamp
            })
    
    return vehicle_positions


def process_alerts(feed):
    """
    Process alerts from GTFS-RT feed
    
    Args:
        feed: GTFS-RT feed message
        
    Returns:
        list: Processed alerts
    """
    if not feed:
        return []
    
    alerts = []
    for entity in feed.entity:
        if entity.HasField('alert'):
            alert = entity.alert
            
            # Get header text
            header = ''
            if alert.HasField('header_text'):
                for translation in alert.header_text.translation:
                    if translation.HasField('text'):
                        header = translation.text
                        break
            
            # Get description text
            description = ''
            if alert.HasField('description_text'):
                for translation in alert.description_text.translation:
                    if translation.HasField('text'):
                        description = translation.text
                        break
            
            # Get cause and effect
            from google.transit import gtfs_realtime_pb2
            cause = gtfs_realtime_pb2.Alert.Cause.Name(alert.cause) if alert.HasField('cause') else 'UNKNOWN_CAUSE'
            effect = gtfs_realtime_pb2.Alert.Effect.Name(alert.effect) if alert.HasField('effect') else 'UNKNOWN_EFFECT'
            
            # Get affected entities
            affected_entities = []
            for informed_entity in alert.informed_entity:
                entity_info = {}
                if informed_entity.HasField('agency_id'):
                    entity_info['agency_id'] = informed_entity.agency_id
                if informed_entity.HasField('route_id'):
                    entity_info['route_id'] = informed_entity.route_id
                if informed_entity.HasField('stop_id'):
                    entity_info['stop_id'] = informed_entity.stop_id
                if informed_entity.HasField('trip'):
                    if informed_entity.trip.HasField('trip_id'):
                        entity_info['trip_id'] = informed_entity.trip.trip_id
                affected_entities.append(entity_info)
            
            alerts.append({
                'header': header,
                'description': description,
                'cause': cause,
                'effect': effect,
                'affected_entities': affected_entities
            })
    
    return alerts


# API routes
@data_api.route('/api/refresh-data', methods=['GET'])
def api_refresh_data():
    """
    Refresh GTFS-RT data by re-downloading from URLs
    """
    current_source = get_current_source()
    results = {
        'trip_update': False,
        'vehicle_position': False,
        'alert': False
    }
    
    if not current_source['use_local_files']:
        for feed_type in results.keys():
            url_key = f"{feed_type}_url"
            if url_key in current_source and current_source[url_key]:
                results[feed_type] = download_gtfs_rt_from_url(
                    current_source[url_key], 
                    FILE_PATHS[feed_type]
                )
    
    return jsonify({
        'status': 'success',
        'results': results
    })


@data_api.route('/api/trip-updates', methods=['GET'])
def api_trip_updates():
    """
    Get trip updates from GTFS-RT feed
    """
    format_param = request.args.get('format', 'json')
    
    # Get trip updates
    feed = get_gtfs_rt_feed('trip_update')
    trip_updates = process_trip_updates(feed)
    
    if format_param == 'csv':
        # Export as CSV
        csv_path = 'output/csv/trip_updates.csv'
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df = pd.DataFrame(trip_updates)
        df.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
        return send_file(csv_path, as_attachment=True)
    
    return jsonify({
        'status': 'success',
        'feed_timestamp': feed.header.timestamp if feed else None,
        'trip_updates': trip_updates
    })


@data_api.route('/api/vehicle-positions', methods=['GET'])
def api_vehicle_positions():
    """
    Get vehicle positions from GTFS-RT feed
    """
    format_param = request.args.get('format', 'json')
    
    # Get vehicle positions
    feed = get_gtfs_rt_feed('vehicle_position')
    vehicle_positions = process_vehicle_positions(feed)
    
    if format_param == 'csv':
        # Export as CSV
        csv_path = 'output/csv/vehicle_positions.csv'
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df = pd.DataFrame(vehicle_positions)
        df.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
        return send_file(csv_path, as_attachment=True)
    
    return jsonify({
        'status': 'success',
        'feed_timestamp': feed.header.timestamp if feed else None,
        'vehicle_positions': vehicle_positions
    })


@data_api.route('/api/alerts', methods=['GET'])
def api_alerts():
    """
    Get alerts from GTFS-RT feed
    """
    # Get alerts
    feed = get_gtfs_rt_feed('alert')
    alerts = process_alerts(feed)
    
    return jsonify({
        'status': 'success',
        'feed_timestamp': feed.header.timestamp if feed else None,
        'alerts': alerts
    })


@data_api.route('/api/all-data', methods=['GET'])
def api_all_data():
    """
    Get all GTFS-RT data (trip updates, vehicle positions, and alerts)
    """
    # Get all data
    trip_update_feed = get_gtfs_rt_feed('trip_update')
    vehicle_position_feed = get_gtfs_rt_feed('vehicle_position')
    alert_feed = get_gtfs_rt_feed('alert')
    
    # Process data
    trip_updates = process_trip_updates(trip_update_feed)
    vehicle_positions = process_vehicle_positions(vehicle_position_feed)
    alerts = process_alerts(alert_feed)
    
    # Get statistics for trip updates
    trip_update_stats = {}
    if trip_updates:
        df = pd.DataFrame(trip_updates)
        # Delay statistics
        if 'delay_minutes' in df.columns:
            trip_update_stats['delay'] = {
                'average': round(df['delay_minutes'].mean(), 1) if not df['delay_minutes'].empty else 0,
                'max': round(df['delay_minutes'].max(), 1) if not df['delay_minutes'].empty else 0,
                'min': round(df['delay_minutes'].min(), 1) if not df['delay_minutes'].empty else 0,
                'median': round(df['delay_minutes'].median(), 1) if not df['delay_minutes'].empty else 0
            }
        # Trip/Route statistics
        if 'trip_id' in df.columns:
            trip_update_stats['trips'] = len(df['trip_id'].unique())
        if 'route_id' in df.columns:
            trip_update_stats['routes'] = len(df['route_id'].unique())
    
    # Get statistics for vehicle positions
    vehicle_stats = {}
    if vehicle_positions:
        df = pd.DataFrame(vehicle_positions)
        # Vehicle count
        if 'vehicle_id' in df.columns:
            vehicle_stats['vehicles'] = len(df['vehicle_id'].unique())
        # Status counts
        if 'current_status' in df.columns and not df['current_status'].empty:
            vehicle_stats['status'] = df['current_status'].value_counts().to_dict()
    
    return jsonify({
        'status': 'success',
        'feed_timestamps': {
            'trip_update': trip_update_feed.header.timestamp if trip_update_feed else None,
            'vehicle_position': vehicle_position_feed.header.timestamp if vehicle_position_feed else None,
            'alert': alert_feed.header.timestamp if alert_feed else None
        },
        'trip_updates': trip_updates,
        'vehicle_positions': vehicle_positions,
        'alerts': alerts,
        'statistics': {
            'trip_updates': trip_update_stats,
            'vehicles': vehicle_stats,
            'alerts': {
                'count': len(alerts)
            }
        }
    })
