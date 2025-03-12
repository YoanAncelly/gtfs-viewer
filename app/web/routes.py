#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from app.api.config_routes import config_api
from app.api.data_routes import data_api
import os

# Create Flask application
app = Flask(__name__, 
          static_folder='../../static', 
          template_folder='../../templates')
CORS(app)

# Register blueprints
app.register_blueprint(config_api)
app.register_blueprint(data_api)


@app.route('/')
def index():
    """
    Render the main dashboard page
    """
    return render_template('index.html')


@app.route('/config')
def config():
    """
    Render the configuration page
    """
    return render_template('config.html')


@app.route('/output/charts/<path:filename>')
def serve_chart(filename):
    """
    Serve generated chart images
    """
    return send_from_directory('../output/charts', filename)


@app.route('/output/csv/<path:filename>')
def serve_csv(filename):
    """
    Serve generated CSV files
    """
    return send_from_directory('../output/csv', filename)
