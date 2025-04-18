from flask import Flask, request, jsonify, send_file
import pdfplumber
import re
import json
from groq import Groq
import os
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from PIL import Image
import tempfile

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Groq client
client = Groq(api_key="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")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def pdf_to_image(pdf_path):
    """Convert first page of PDF to JPEG image"""
    try:
        pages = convert_from_path(pdf_path, first_page=1, last_page=1, fmt='jpeg')
        if pages:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'preview.jpg')
            pages[0].save(image_path, 'JPEG')
            return image_path
    except Exception as e:
        print(f"Image conversion error: {e}")
    return None


def extract_resume_data(pdf_path):
    """Extract text and process with Groq"""

    def read_pdf_file(pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages])

    resume_text = read_pdf_file(pdf_path)

    prompt = f"""
    Extract the following from this resume in STRICT JSON format:
    {{
        "name": "Full Name",
        "location": "City, Country",
        "education": ["Degree, Institution, Year"],
        "skills": ["List", "Of", "Technical", "Skills"],
        "career_name": "Predict the MOST SPECIFIC job title. Format: '[Seniority] [Tech Stack] [Role] [Industry?]'",
        "projects": ["Project 1", "Project 2"],
        "github_username": "Only the username (no URL, no @ symbol)",
        "linkedin_url": "Full profile URL or null"
    }}
    Resume: {resume_text[:3000]}  # Truncate to save tokens
    """

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

