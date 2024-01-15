from pathlib import Path

from flask import Flask, render_template, jsonify, request, send_from_directory
from map_generation_manager import map_generation_manager
import processor

app = Flask(__name__)

@app.route('/')
def index():
    districts = processor.get_district_list()
    return render_template('index.html', districts=districts)

@app.route('/generate_map', methods=['POST'])
def generate_map():
    district_code = request.form.get('district_code')
    num_classes = request.form.get('num_classes', type=int)
    color_palette_name = request.form.get('color_palette_name')

    if not district_code or num_classes is None or not color_palette_name:
        return jsonify({'status': 'Error', 'message': 'Invalid input parameters'}), 400

    if map_generation_manager.generate_map_for_district(district_code, num_classes, color_palette_name):
        return jsonify({'status': 'Accepted', 'message': 'Map generation started'})
    else:
        return jsonify({'status': 'Already Processing', 'message': 'Map is already being generated'})

@app.route('/map_status', methods=['GET'])
def map_status():
    district_code = request.args.get('district_code')
    num_classes = request.args.get('num_classes')
    color_palette_name = request.args.get('color_palette_name')

    if not district_code or not num_classes or not color_palette_name:
        return jsonify({'status': 'Error', 'message': 'Invalid input parameters'}), 400

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

    if not district_code:
        return jsonify({'status': 'Error', 'message': 'Invalid district'}), 400

    try:
        land_data = processor.get_land_data(district_code)
        return jsonify({'status': 'Success', 'table': land_data})
    except Exception as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)
