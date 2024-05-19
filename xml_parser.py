# xml_parser.py
import xml.etree.ElementTree as ET
import csv
import re  # Add this import

def parse_xml_to_csv(input_xml_path, output_csv_path):
    # Parse the XML file
    tree = ET.parse(input_xml_path)
    root = tree.getroot()

    # Prepare the CSV file for writing
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Date', 'Amount', 'First Name', 'Last Name'])  # Write CSV header

        # Iterate through the XML structure
        for page in root.findall('Page'):
            lines = page.findall('Line')
            found_summary = False

            for i, line in enumerate(lines):
                text = line.text.strip()
                if text in ['ATM/Debit Card Summary', 'ATM/Debit Card Summary (Continued)']:
                    found_summary = True
                    continue

                if found_summary:
                    if 'ELECTRONIC DEPOSIT/CREDIT' in text:
                        amount = text.split()[-1]
                        date = lines[i+1].text.strip()
                        details = lines[i+2].text.strip()

                        # Extract Name and ID
                        if 'ZELLE' in details:
                            name_id = details.replace('ZELLE', '').strip()
                            name, id_info = name_id.rsplit(' ', 1)

                            # Extract month and date from the date string
                            date_match = re.search(r'\d{2}/\d{2}', date)
                            if date_match:
                                date = date_match.group(0)

                            # Write to CSV file
                            writer.writerow([date, amount, name, id_info])

    print(f"Payment tracker created: {output_csv_path}")

def merge_csv_files(csv_paths, output_path):
    header_saved = False
    with open(output_path, 'w', newline='') as fout:
        for csv_path in csv_paths:
            with open(csv_path, 'r') as fin:
                header = next(fin)
                if not header_saved:
                    fout.write(header)
                    header_saved = True
                for line in fin:
                    fout.write(line)
