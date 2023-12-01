from flask import Flask, render_template, request, send_file
import main  # Import your main script

app = Flask(__name__)

@app.route('/')
def index():
    districts = main.get_district_list()  # Function to retrieve district list
    return render_template('index.html', districts=districts)

@app.route('/generate_map', methods=['POST'])
def generate_map():
    district_name = request.form['district']
    main.process_district_by_name(district_name)  # Modified function to process by district name
    return send_file(f'maps/map_{district_name}.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
