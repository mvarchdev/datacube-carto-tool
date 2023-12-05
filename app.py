import json
from pathlib import Path

import flask
from flask import Flask, render_template, jsonify, request, send_from_directory
from map_generation_manager import map_generation_manager
import main

app = Flask(__name__)

@app.route('/')
def index():
    districts = main.get_district_list()  # Function to fetch all district names
    return render_template('index.html', districts=districts)

@app.route('/generate_map', methods=['POST'])
def generate_map():
    district_code = request.form.get('district_code')
    num_classes = request.form.get('num_classes', type=int)
    color_palette_name = request.form.get('color_palette_name')
    if district_code:
        if map_generation_manager.generate_map_for_district(district_code, num_classes, color_palette_name):
            return jsonify({'status': 'Accepted', 'message': 'Map generation started'})
        else:
            return jsonify({'status': 'Already Processing', 'message': 'Map is already being generated'})
    return jsonify({'status': 'Error', 'message': 'Invalid district'})

@app.route('/map_status', methods=['GET'])
def map_status():
    district_code = request.args.get('district_code')
    num_classes = request.args.get('num_classes')
    color_palette_name = request.args.get('color_palette_name')
    status = map_generation_manager.get_status(district_code, num_classes, color_palette_name)
    return jsonify({'status': status})

@app.route('/maps/<district_code>/<num_classes>/<color_palette_name>')
def serve_map(district_code, num_classes, color_palette_name):
    file_path = Path('maps') / f'map_{district_code}_{num_classes}_{color_palette_name}.png'
    if file_path.exists():
        return send_from_directory(file_path.parent, file_path.name)
    return 'Map not found', 404

@app.route('/get_data', methods=['GET'])
def get_data():
    district_code = request.args.get('district_code')
    if district_code:
        try:
            land_data = main.get_land_data(district_code)  # Function to fetch land data for the district
            return jsonify({'status': 'success', 'table': land_data})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    return jsonify({'status': 'error', 'message': 'Invalid district'})


if __name__ == '__main__':
    app.run(debug=False)
