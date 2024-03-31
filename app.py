from flask import Flask, render_template, request
from PIL import Image
import fitz
from io import BytesIO
import requests
import json

app = Flask(__name__)

def pdf_to_image(pdf_bytes):
    # Convert PDF to PIL images
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    zoom = 4
    mat = fitz.Matrix(zoom, zoom)

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        pixmap = page.get_pixmap(matrix=mat)
        img = Image.open(BytesIO(pixmap.tobytes()))

        # Resize image if it exceeds 1000x1000 pixels while maintaining aspect ratio
        max_size = 1000
        width, height = img.size
        if width > max_size or height > max_size:
            ratio = min(max_size / width, max_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            # img = img.resize((new_width, new_height), Image.ANTIALIAS)

        images.append(img)

    total_height = sum(image.height for image in images)
    max_width = max(image.width for image in images)

    stitched_image = Image.new('RGB', (max_width, total_height))
    current_height = 0

    for image in images:
        stitched_image.paste(image, (0, current_height))
        current_height += image.height

    doc.close()
    return stitched_image

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    
    if file.filename == '':
        return render_template('index.html', error='No file selected')

    # Read the file
    file_bytes = file.read()

    # Convert PDF to image if the file is a PDF
    if file.filename.lower().endswith('.pdf'):
        image = pdf_to_image(file_bytes)
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        files = {'file': ('invoice.png', img_byte_arr, 'image/png')}
    else:
        files = {'file': (file.filename, file_bytes)}

    # Send the request
    url = "https://invoice-parser-demanual.vercel.app//parse_invoice"
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        response_json = response.json()
        return render_template('index.html', response=response_json)
    else:
        return render_template('index.html', error=f'Error: {response.text}')

if __name__ == "__main__":
    app.run(debug=True)
