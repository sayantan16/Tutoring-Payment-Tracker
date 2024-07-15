import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from pytesseract import Output
import xml.etree.ElementTree as ET
import sys

def pdf_to_xml(pdf_path, output_xml_path, log_path='log.txt'):
    # Redirect stdout to a log file
    log_file = open(log_path, 'w')
    sys.stdout = log_file

    pdf_document = fitz.open(pdf_path)

    # Check basic metadata
    metadata = pdf_document.metadata
    print("Metadata:", metadata)

    # Check number of pages
    num_pages = pdf_document.page_count
    print(f'This PDF has {num_pages} pages')

    def ocr_page(image):
        return pytesseract.image_to_string(image, output_type=Output.STRING)

    # Create the root element for XML
    root = ET.Element("PDFDocument")
    metadata_elem = ET.SubElement(root, "Metadata")
    for key, value in metadata.items():
        ET.SubElement(metadata_elem, key).text = str(value)

    for page_num in range(num_pages):
        pdf_page = pdf_document.load_page(page_num)
        print(f"----- Page {page_num + 1} -----")

        # Try to fetch the text in different ways
        try:
            text = pdf_page.get_text("text")
            if text.strip():
                print("Text mode:")
                print(text)

                # Create a new element for each page in the XML
                page_elem = ET.SubElement(root, "Page", number=str(page_num + 1))
                for line in text.split("\n"):
                    ET.SubElement(page_elem, "Line").text = line
            else:
                print(f"Page {page_num + 1} does not contain text or is empty.")
        except Exception as e:
            print(f"Error extracting text from page {page_num + 1}: {e}")

        # Convert PDF page to image for OCR
        try:
            images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1, dpi=300)
            for image in images:
                ocr_text = ocr_page(image)
                if ocr_text.strip():
                    print("OCR mode:")
                    print(ocr_text)

                    # Clean up OCR text
                    clean_text = "\n".join([line.strip() for line in ocr_text.splitlines() if line.strip()])

                    # Create a new element for each page in the XML
                    page_elem = ET.SubElement(root, "Page", number=str(page_num + 1))
                    for line in clean_text.split("\n"):
                        ET.SubElement(page_elem, "Line").text = line
                else:
                    print(f"Page {page_num + 1} OCR did not find any text.")
        except Exception as e:
            print(f"Error performing OCR on page {page_num + 1}: {e}")

    # Convert the ElementTree to a string
    xml_content = ET.tostring(root, encoding='unicode')

    # Save the XML content to a file
    with open(output_xml_path, 'w', encoding='utf-8') as file:
        file.write(xml_content)

    # Close the log file
    log_file.close()

    # Reset stdout to the default value
    sys.stdout = sys.__stdout__

    print(f"XML file created: {output_xml_path}")
    print("Log file created: {log_path}")

# Usage example:
# pdf_to_xml('example.pdf', 'output.xml')
