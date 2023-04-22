from flask import Flask, render_template, request
import pandas as pd
import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import requests
import json
from io import StringIO

app = Flask(__name__)

pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
receipts_folder = "./archive/SROIE2019/train/img"

def image_clearer(image):
    # Open the image
    img = Image.open(image)
    # Rotate the image
    img = img.rotate(90)
    # Enhance image sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2)
    # Enhance image brightness
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.5)
    # Enhance image contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    # Remove image noise
    img = img.filter(ImageFilter.MedianFilter(size=5))
    return img

def extract_data(text):
    date_pattern = re.compile(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}')
    amount_pattern = re.compile(r'\d+\.\d{2}')
    amount_type_pattern = re.compile(r'USD|EUR|INR|GBP')
    title_pattern = re.compile(r'(^|\n)([A-Z][a-z]+(\s[A-Z][a-z]+)*)+')
    product_pattern = r'(\d+)\s+([\w\s]+)\s+([\d\.]+)'
    date = date_pattern.findall(text)[0] if date_pattern.findall(text) else None
    amount = amount_pattern.findall(text)[0] if amount_pattern.findall(text) else None
    amount_type = amount_type_pattern.findall(text)[0] if amount_type_pattern.findall(text) else None
    title = title_pattern.search(text).group(0).strip() if title_pattern.search(text) else None
    products = re.findall(product_pattern, text) if re.findall(product_pattern, text) else None
    return {'Date': date, 'Title': title, 'Amount': amount, 'Payment_Type': amount_type, 'Products': products}

def extract_receipts_data(receipts_path):
    receipts_data = []
    for file in os.listdir(receipts_path):
        if file.endswith(".jpg") or file.endswith(".png"):
            image = image_clearer(os.path.join(receipts_path, file))
            text = pytesseract.image_to_string(image)
            receipt_data = extract_data(text)
            receipts_data.append(receipt_data)
    return receipts_data

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if request.form.get('input') == 'folder':
            folder_path = request.form['path']
            data = extract_receipts_data(folder_path)
            df = pd.DataFrame(data)
            return render_template('index.html', data=df.to_html())
        else:
            file = request.files['file']
            image = Image.open(file.stream)
            text = pytesseract.image_to_string(image)
            receipt_data = extract_data(text)
            df = pd.DataFrame([receipt_data])
            return render_template('index.html', data=df.to_html())
    else:
        return render_template('index.html')


from werkzeug.exceptions import BadRequestKeyError

import json

@app.route('/download_csv', methods=['POST'])
def download_csv():
    csv_data = request.form['csv_data']
    try:
        df = pd.read_json(json.loads(csv_data))
    except json.JSONDecodeError:
        return "Invalid JSON data"
    csv = df.to_csv(index=False)
    response = make_response(csv)
    response.headers['Content-Disposition'] = 'attachment; filename=data.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@app.route("/dashboard", methods=["POST"])
def dashboard():
    # Your dashboard code here
    return render_template("dashboard.html")


if __name__ == '__main__':
    app.run(debug=True)

        
        