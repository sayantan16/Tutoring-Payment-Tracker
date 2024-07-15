import os
from flask import Flask, request, redirect, url_for, render_template, flash, jsonify
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from werkzeug.utils import secure_filename
import ssl
import re
import calendar

from pdf_to_xml import pdf_to_xml
from xml_parser import merge_csv_files, parse_xml_to_csv  

# Create an unverified context to handle SSL issues with SendGrid
ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'uploads'
app.config['NAMES_FILE'] = 'names_list.txt'
app.secret_key = 'supersecretkey'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def get_month_name(month_number):
    return calendar.month_name[int(month_number)]

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

def delete_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except OSError as e:
            print(f"Error deleting file {file_path}: {e.strerror}")

def group_csv_by_month(csv_path):
    data_by_month = {}
    with open(csv_path, 'r') as file:
        next(file)  # Skip header row
        for line in file:
            columns = line.strip().split(',')
            if len(columns) >= 4:
                date = columns[0]
                month = date.split('/')[0].zfill(2)  # Ensure two-digit month format
                if month not in data_by_month:
                    data_by_month[month] = []
                data_by_month[month].append(columns)
    
    # Sort records by date within each month
    for month in data_by_month:
        data_by_month[month] = sorted(data_by_month[month], key=lambda x: (int(x[0].split('/')[1]), int(x[0].split('/')[0])))
    
    return data_by_month

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
    available_months = set()
    month_exists = False
    with open(csv_path, 'r') as file:
        next(file)  # Skip header row
        for line in file:
            columns = line.strip().split(',')
            if len(columns) >= 4:
                date = columns[0]
                file_month = date.split('/')[0].zfill(2)  # Ensure two-digit month format
                available_months.add(file_month)
                if file_month == month.zfill(2):
                    month_exists = True
                    first_name, last_name = columns[2], columns[3]
                    paid_students.add(f"{first_name} {last_name}")

    if not month_exists:
        print(f"Month {month} does not exist in the file.")
        return None, available_months

    all_students = read_names_list()
    unpaid_students = all_students - paid_students

    print(f"Paid students for {month}: {paid_students}")
    print(f"Unpaid students for {month}: {unpaid_students}")
    
    return unpaid_students, available_months

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files or 'view' not in request.form:
            return jsonify({'message': 'Missing file or view selection.'}), 400

        # Delete all files in the uploads folder before processing new uploads
        delete_files_in_folder(app.config['UPLOAD_FOLDER'])

        files = request.files.getlist('file')
        view = request.form['view']
        month = request.form.get('month', None)
        
        if not files:
            return jsonify({'message': 'No files uploaded.'}), 400

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
            return jsonify({'message': 'No valid files uploaded.'}), 400

        # Convert PDF to XML and parse XML to CSV for each file
        csv_paths = []
        for file_path in filenames:
            output_xml_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{os.path.basename(file_path)}.xml')
            log_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{os.path.basename(file_path)}.log')
            pdf_to_xml(file_path, output_xml_path, log_path)

            output_csv_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{os.path.basename(file_path)}.csv')
            parse_xml_to_csv(output_xml_path, output_csv_path)
            csv_paths.append(output_csv_path)

        # Merge all CSV files into one
        final_csv_path = os.path.join(app.config['OUTPUT_FOLDER'], 'payment_tracker.csv')
        merge_csv_files(csv_paths, final_csv_path)

        # Extract new names from the final CSV
        new_names = extract_names_from_csv(final_csv_path)

        # Update names list
        update_names_list(new_names)

        if view == 'payments':
            return jsonify({'redirect_url': url_for('show_csv')})
        elif view == 'unpaid':
            if not month:
                return jsonify({'message': 'Please select a month.'}), 400
            unpaid_students, available_months = check_payments_for_month(month.zfill(2), final_csv_path)
            if unpaid_students is None:
                available_months_names = [get_month_name(int(m)) for m in sorted(available_months)]
                return jsonify({'message': 'The selected month does not exist in the file.', 'available_months': available_months_names}), 400
            month_name = get_month_name(int(month))
            return jsonify({'redirect_url': url_for('show_unpaid_students', month=month.zfill(2))})
    return render_template('index.html')

@app.route('/unpaid_students/<month>')
def show_unpaid_students(month):
    final_csv_path = os.path.join(app.config['OUTPUT_FOLDER'], 'payment_tracker.csv')
    unpaid_students, _ = check_payments_for_month(month.zfill(2), final_csv_path)
    if unpaid_students is None:
        unpaid_students = []
    print(f"Rendering unpaid students for {month}: {unpaid_students}")
    return render_template('unpaid_students.html', unpaid_students=unpaid_students, month=get_month_name(int(month)))

@app.route('/csv')
def show_csv():
    data_by_month = group_csv_by_month(os.path.join(app.config['OUTPUT_FOLDER'], 'payment_tracker.csv'))
    month_names = {
        '01': 'January', '02': 'February', '03': 'March', '04': 'April',
        '05': 'May', '06': 'June', '07': 'July', '08': 'August',
        '09': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    return render_template('show_csv.html', data_by_month=data_by_month, month_names=month_names)

@app.route('/send_email', methods=['POST'])
def send_email():
    recipient = request.form['email']
    month_name = request.form['month']
    
    # Validate the email address
    if not re.match(r"[^@]+@[^\s@]+\.[^\s@]+", recipient):
        return {"message": "Invalid email address.", "status": "error"}, 400

    unpaid_students = request.form.getlist('unpaid_students')

    if unpaid_students:
        unpaid_list = "\n".join(unpaid_students)
        html_content = (
            "<strong>The following students have not paid for " + month_name + ":</strong><br><br>" +
            unpaid_list.replace('\n', '<br>')
        )
        message = Mail(
            from_email='sayantankundu93@gmail.com',
            to_emails=recipient,
            subject=f"Unpaid Students for {month_name}",
            html_content=html_content
        )
        try:
            sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
            if not sendgrid_api_key:
                print("SendGrid API key is not set")
                return {"message": "SendGrid API key is not set.", "status": "error"}, 500
            
            print(f"Using SendGrid API key: {sendgrid_api_key}")  # Debugging information
            sg = SendGridAPIClient(sendgrid_api_key)
            response = sg.send(message)
            
            print("SendGrid Response Status Code:", response.status_code)
            print("SendGrid Response Body:", response.body)
            print("SendGrid Response Headers:", response.headers)
            
            if response.status_code == 202:
                return {"message": f"Email sent to {recipient}", "status": "success"}, 200
            else:
                return {"message": "Failed to send email.", "status": "error"}, response.status_code
        except Exception as e:
            print(e)
            return {"message": f"Failed to send email: {str(e)}", "status": "error"}, 500
    else:
        return {"message": "All students have paid for this month.", "status": "info"}, 200

if __name__ == "__main__":
    app.run(debug=True, port=8888)
