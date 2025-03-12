#!/usr/bin/env python
# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import os


def generate_delay_chart(trip_updates, output_path='output/charts/delay_distribution.png'):
    """
    Generate a histogram of delay distribution from trip updates
    
    Args:
        trip_updates (list): List of trip update dictionaries
        output_path (str): Path to save the generated chart
    """
    if not trip_updates:
        return None
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Extract delay values
    delays = [update['delay_minutes'] for update in trip_updates if 'delay_minutes' in update]
    
    if delays:
        plt.figure(figsize=(10, 6))
        plt.hist(delays, bins=20)
        plt.title('Distribution of Delays')
        plt.xlabel('Delay (minutes)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path)
        plt.close()
        return output_path
    return None


def generate_vehicle_position_map(vehicle_positions, output_path='output/charts/vehicle_positions.png'):
    """
    Generate a scatter plot of vehicle positions
    
    Args:
        vehicle_positions (list): List of vehicle position dictionaries
        output_path (str): Path to save the generated chart
    """
    if not vehicle_positions:
        return None
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create a DataFrame from vehicle positions
    df = pd.DataFrame(vehicle_positions)
    
    # Check if we have coordinate data
    if ('latitude' in df and 'longitude' in df and 
            df['latitude'].notna().any() and df['longitude'].notna().any()):
        plt.figure(figsize=(10, 8))
        plt.scatter(df['longitude'], df['latitude'], alpha=0.6)
        plt.title('Vehicle Positions')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path)
        plt.close()
        return output_path
    return None
