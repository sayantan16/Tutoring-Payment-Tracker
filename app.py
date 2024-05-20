# app.py
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from pdf_to_xml import pdf_to_xml
from xml_parser import parse_xml_to_csv, merge_csv_files

app = Flask(__name__)
CORS(app)  # Add this line to enable CORS

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['NAMES_FILE'] = 'names_list.txt'
app.secret_key = 'supersecretkey'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def read_names_list():
    if not os.path.exists(app.config['NAMES_FILE']):
        # Create the file if it does not exist
        with open(app.config['NAMES_FILE'], 'w') as file:
            pass
        return set()
    with open(app.config['NAMES_FILE'], 'r') as file:
        names = {line.strip() for line in file}
    return names

def update_names_list(new_names):
    names = read_names_list()
    updated = False
    with open(app.config['NAMES_FILE'], 'a') as file:
        for name in new_names:
            if name not in names:
                file.write(name + '\n')
                names.add(name)
                updated = True
    return updated

def delete_files(filepaths):
    for filepath in filepaths:
        try:
            os.remove(filepath)
            print(f"Deleted file: {filepath}")
        except OSError as e:
            print(f"Error deleting file {filepath}: {e.strerror}")

def group_csv_by_month(csv_path):
    data_by_month = {}
    with open(csv_path, 'r') as file:
        next(file)  # Skip header row
        for line in file:
            columns = line.strip().split(',')
            if len(columns) >= 4:
                date = columns[0]
                month = date.split('/')[0]  # Extract month from date
                if month not in data_by_month:
                    data_by_month[month] = []
                data_by_month[month].append(columns)
    return data_by_month

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files or 'view' not in request.form:
            return redirect(request.url)

        # Delete specified files before processing
        delete_files(['log.txt', 'output_file.xml', 'payment_tracker.csv'])

        files = request.files.getlist('file')
        view = request.form['view']
        month = request.form.get('month', None)
        
        if not files:
            return redirect(request.url)

        filenames = []
        for file in files:
            if file.filename == '':
                continue
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                filenames.append(file_path)

        if not filenames:
            return redirect(request.url)

        # Convert PDF to XML and parse XML to CSV for each file
        csv_paths = []
        for file_path in filenames:
            output_xml_path = f'{file_path}.xml'
            log_path = f'{file_path}.log'
            pdf_to_xml(file_path, output_xml_path, log_path)

            output_csv_path = f'{file_path}.csv'
            parse_xml_to_csv(output_xml_path, output_csv_path)
            csv_paths.append(output_csv_path)

        # Merge all CSV files into one
        final_csv_path = 'payment_tracker.csv'
        merge_csv_files(csv_paths, final_csv_path)

        # Extract new names from the final CSV
        new_names = extract_names_from_csv(final_csv_path)

        # Update names list
        update_names_list(new_names)

        if view == 'payments':
            return redirect(url_for('show_csv'))
        elif view == 'unpaid':
            if not month:
                flash('Please select a month.', 'error')
                return redirect(request.url)
            unpaid_students = check_payments_for_month(month, final_csv_path)
            if unpaid_students is None:
                flash('The selected month is not present in the file.', 'error')
                return redirect(request.url)
            return render_template('unpaid_students.html', unpaid_students=unpaid_students, month=month)
    return render_template('index.html')

def extract_names_from_csv(csv_path):
    new_names = set()
    with open(csv_path, 'r') as file:
        next(file)  # Skip header row
        for line in file:
            columns = line.strip().split(',')
            if len(columns) >= 4:
                first_name, last_name = columns[2], columns[3]
                new_names.add(f"{first_name} {last_name}")
    return new_names

def check_payments_for_month(month, csv_path):
    paid_students = set()
    with open(csv_path, 'r') as file:
        next(file)  # Skip header row
        for line in file:
            columns = line.strip().split(',')
            if len(columns) >= 4:
                date = columns[0]
                if date.startswith(month):
                    first_name, last_name = columns[2], columns[3]
                    paid_students.add(f"{first_name} {last_name}")
    
    if not paid_students:
        return None
    
    all_students = read_names_list()
    unpaid_students = all_students - paid_students
    return unpaid_students

@app.route('/csv')
def show_csv():
    data_by_month = group_csv_by_month('payment_tracker.csv')
    month_names = {
        '01': 'January', '02': 'February', '03': 'March', '04': 'April',
        '05': 'May', '06': 'June', '07': 'July', '08': 'August',
        '09': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    return render_template('show_csv.html', data_by_month=data_by_month, month_names=month_names)

if __name__ == "__main__":
    app.run(debug=True, port=8080)