#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import pandas as pd
import matplotlib.pyplot as plt
from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict
from datetime import datetime


def read_gtfs_rt_file(file_path):
    """
    Read a GTFS-RT protobuf file and return the parsed feed message
    
    Args:
        file_path (str): Path to the GTFS-RT .pb file
        
    Returns:
        feed (gtfs_realtime_pb2.FeedMessage): Parsed GTFS-RT feed message
    """
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        with open(file_path, 'rb') as f:
            feed.ParseFromString(f.read())
        return feed
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def convert_to_dict(feed):
    """
    Convert a GTFS-RT feed message to a Python dictionary
    
    Args:
        feed (gtfs_realtime_pb2.FeedMessage): Parsed GTFS-RT feed message
        
    Returns:
        dict: Dictionary representation of the feed
    """
    if feed is None:
        return None
    return MessageToDict(feed)


def print_feed_info(feed, feed_type):
    """
    Print basic information about the feed
    
    Args:
        feed (gtfs_realtime_pb2.FeedMessage): Parsed GTFS-RT feed message
        feed_type (str): Type of the feed (TripUpdate, VehiclePosition, Alert)
    """
    if feed is None:
        print(f"No {feed_type} feed available")
        return
    
    print(f"\n{'-'*50}")
    print(f"Feed type: {feed_type}")
    print(f"Feed version: {feed.header.gtfs_realtime_version}")
    timestamp = feed.header.timestamp
    if timestamp:
        print(f"Timestamp: {timestamp} ({datetime.fromtimestamp(timestamp)})")
    print(f"Number of entities: {len(feed.entity)}")
    print(f"{'-'*50}\n")


def analyze_trip_updates(feed):
    """
    Analyze and display information about trip updates
    
    Args:
        feed (gtfs_realtime_pb2.FeedMessage): Parsed GTFS-RT feed message for trip updates
    """
    if feed is None:
        return
    
    delays = []
    trip_ids = []
    route_ids = []
    stop_ids = []
    
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_update = entity.trip_update
            trip_id = trip_update.trip.trip_id
            route_id = trip_update.trip.route_id if trip_update.trip.HasField('route_id') else 'N/A'
            
            for stop_time_update in trip_update.stop_time_update:
                delay = stop_time_update.arrival.delay if stop_time_update.HasField('arrival') else (
                    stop_time_update.departure.delay if stop_time_update.HasField('departure') else 0)
                stop_id = stop_time_update.stop_id
                
                delays.append(delay)
                trip_ids.append(trip_id)
                route_ids.append(route_id)
                stop_ids.append(stop_id)
    
    if delays:
        # Create a DataFrame for analysis
        df = pd.DataFrame({
            'trip_id': trip_ids,
            'route_id': route_ids,
            'stop_id': stop_ids,
            'delay_seconds': delays,
            'delay_minutes': [d/60 for d in delays]
        })
        
        print(f"Trip Updates Analysis:")
        print(f"Total number of stop time updates: {len(df)}")
        print(f"Average delay: {df['delay_seconds'].mean():.2f} seconds ({df['delay_minutes'].mean():.2f} minutes)")
        print(f"Max delay: {df['delay_seconds'].max():.2f} seconds ({df['delay_minutes'].max():.2f} minutes)")
        print(f"Min delay: {df['delay_seconds'].min():.2f} seconds ({df['delay_minutes'].min():.2f} minutes)")
        
        # Plot delay distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df['delay_minutes'], bins=20)
        plt.title('Distribution of Delays')
        plt.xlabel('Delay (minutes)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        plt.savefig('delay_distribution.png')
        print("Delay distribution plot saved as 'delay_distribution.png'")
        
        return df
    else:
        print("No trip updates found with delay information")
        return None


def analyze_vehicle_positions(feed):
    """
    Analyze and display information about vehicle positions
    
    Args:
        feed (gtfs_realtime_pb2.FeedMessage): Parsed GTFS-RT feed message for vehicle positions
    """
    if feed is None:
        return
    
    vehicle_data = []
    
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            vehicle = entity.vehicle
            vehicle_id = vehicle.vehicle.id if vehicle.HasField('vehicle') and vehicle.vehicle.HasField('id') else 'N/A'
            trip_id = vehicle.trip.trip_id if vehicle.HasField('trip') and vehicle.trip.HasField('trip_id') else 'N/A'
            route_id = vehicle.trip.route_id if vehicle.HasField('trip') and vehicle.trip.HasField('route_id') else 'N/A'
            
            position_data = {
                'vehicle_id': vehicle_id,
                'trip_id': trip_id,
                'route_id': route_id,
                'latitude': vehicle.position.latitude if vehicle.HasField('position') else None,
                'longitude': vehicle.position.longitude if vehicle.HasField('position') else None,
                'bearing': vehicle.position.bearing if vehicle.HasField('position') and vehicle.position.HasField('bearing') else None,
                'speed': vehicle.position.speed if vehicle.HasField('position') and vehicle.position.HasField('speed') else None,
                'current_status': vehicle.current_status if vehicle.HasField('current_status') else None,
                'timestamp': vehicle.timestamp if vehicle.HasField('timestamp') else None
            }
            
            vehicle_data.append(position_data)
    
    if vehicle_data:
        df = pd.DataFrame(vehicle_data)
        
        print(f"Vehicle Positions Analysis:")
        print(f"Total number of vehicles: {len(df)}")
        
        if 'speed' in df and df['speed'].notna().any():
            print(f"Average speed: {df['speed'].mean():.2f} m/s")
            print(f"Max speed: {df['speed'].max():.2f} m/s")
            print(f"Min speed: {df['speed'].min():.2f} m/s")
        
        # If we have coordinates, we could plot them
        if 'latitude' in df and 'longitude' in df and df['latitude'].notna().any() and df['longitude'].notna().any():
            plt.figure(figsize=(10, 8))
            plt.scatter(df['longitude'], df['latitude'], alpha=0.6)
            plt.title('Vehicle Positions')
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.grid(True, alpha=0.3)
            plt.savefig('vehicle_positions.png')
            print("Vehicle positions plot saved as 'vehicle_positions.png'")
        
        return df
    else:
        print("No vehicle position data found")
        return None


def analyze_alerts(feed):
    """
    Analyze and display information about alerts
    
    Args:
        feed (gtfs_realtime_pb2.FeedMessage): Parsed GTFS-RT feed message for alerts
    """
    if feed is None:
        return
    
    alert_data = []
    
    for entity in feed.entity:
        if entity.HasField('alert'):
            alert = entity.alert
            
            # Get affected entities
            affected_entities = []
            for informed_entity in alert.informed_entity:
                entity_info = {}
                if informed_entity.HasField('agency_id'):
                    entity_info['agency_id'] = informed_entity.agency_id
                if informed_entity.HasField('route_id'):
                    entity_info['route_id'] = informed_entity.route_id
                if informed_entity.HasField('trip'):
                    entity_info['trip_id'] = informed_entity.trip.trip_id
                if informed_entity.HasField('stop_id'):
                    entity_info['stop_id'] = informed_entity.stop_id
                affected_entities.append(entity_info)
            
            # Get header text
            header_text = ''
            if alert.HasField('header_text'):
                for translation in alert.header_text.translation:
                    if translation.HasField('text'):
                        header_text = translation.text
                        break
            
            # Get description text
            description_text = ''
            if alert.HasField('description_text'):
                for translation in alert.description_text.translation:
                    if translation.HasField('text'):
                        description_text = translation.text
                        break
            
            alert_info = {
                'id': entity.id,
                'cause': alert.cause if alert.HasField('cause') else None,
                'effect': alert.effect if alert.HasField('effect') else None,
                'header_text': header_text,
                'description_text': description_text,
                'affected_entities': affected_entities
            }
            
            alert_data.append(alert_info)
    
    if alert_data:
        print(f"Alerts Analysis:")
        print(f"Total number of alerts: {len(alert_data)}")
        
        for i, alert in enumerate(alert_data, 1):
            print(f"\nAlert {i}:")
            print(f"ID: {alert['id']}")
            print(f"Cause: {alert['cause']}")
            print(f"Effect: {alert['effect']}")
            print(f"Header: {alert['header_text']}")
            print(f"Description: {alert['description_text'][:100]}..." if len(alert['description_text']) > 100 else f"Description: {alert['description_text']}")
            print(f"Affected entities: {len(alert['affected_entities'])}")
        
        return alert_data
    else:
        print("No alert data found")
        return None


def main():
    # Define paths to GTFS-RT files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    trip_update_path = os.path.join(current_dir, 'TripUpdate.pb')
    vehicle_position_path = os.path.join(current_dir, 'VehiclePosition.pb')
    alert_path = os.path.join(current_dir, 'Alert.pb')
    
    # Read GTFS-RT files
    trip_update_feed = read_gtfs_rt_file(trip_update_path)
    vehicle_position_feed = read_gtfs_rt_file(vehicle_position_path)
    alert_feed = read_gtfs_rt_file(alert_path)
    
    # Print basic information about each feed
    print_feed_info(trip_update_feed, 'TripUpdate')
    print_feed_info(vehicle_position_feed, 'VehiclePosition')
    print_feed_info(alert_feed, 'Alert')
    
    # Analyze each feed type
    trip_updates_df = analyze_trip_updates(trip_update_feed)
    vehicle_positions_df = analyze_vehicle_positions(vehicle_position_feed)
    alerts_data = analyze_alerts(alert_feed)
    
    print("\nAnalysis complete!")
    
    # You can save the DataFrames to CSV files if needed
    if trip_updates_df is not None:
        trip_updates_df.to_csv('trip_updates.csv', index=False)
        print("Trip updates data saved to 'trip_updates.csv'")
    
    if vehicle_positions_df is not None:
        vehicle_positions_df.to_csv('vehicle_positions.csv', index=False)
        print("Vehicle positions data saved to 'vehicle_positions.csv'")


if __name__ == '__main__':
    main()
