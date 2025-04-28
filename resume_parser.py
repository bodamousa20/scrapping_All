from flask import Flask, request, jsonify, send_file
import pdfx
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
You are a professional resume parser. Extract the following fields from the resume below and respond ONLY in the exact JSON format shown, without adding or removing keys.

Instructions:
- ONLY extract data if it is explicitly stated in the resume. DO NOT infer or guess missing information.
- For GitHub and LinkedIn, only return values if actual links or usernames are mentioned directly.
- If a value is missing, use null or an empty list as appropriate.

Expected JSON structure:
{{
    "name": "Full Name",
    "location": "City, Country",
    "email": "email@example.com",
    "education": ["Degree, Institution, Year"],
    "skills": ["List", "Of", "Technical", "Skills"],  // Only technical skills, no soft skills
    "career_name": "Predict the MOST SPECIFIC job title based strictly on the resume’s technical skills, tools, and projects — do not guess or generalize. Combine these elements in the title:
1) Seniority level if stated or implied (e.g., Junior, Mid-Level, Senior, Lead),
2) The PRIMARY technology, framework, or tool used (e.g., React, Kotlin, Laravel, Flutter, Spring Boot, AutoCAD, Power BI),
3) Role type (e.g., Developer, Engineer, Architect, Analyst, Designer),
4) Optional specialization or platform if clear (e.g., Web, Mobile, AI, Embedded, Game, Finance).

The format must be: '[Seniority] [Technology/Tool] [Role] [Optional Specialization or Industry]'
Return concise but complete titles. DO NOT return vague outputs like 'Frontend Developer', 'Mobile Developer', or 'Software Engineer'. Always include the tech stack or tool when mentioned.
Examples:
- 'Junior React Frontend Developer'
- 'Flutter Mobile App Developer'
- 'Spring Boot Backend Java Engineer'
- 'Laravel PHP Backend Developer'
- 'Power BI Business Analyst'
- 'AutoCAD Civil Drafting Engineer'
- 'Entry-Level Illustrator Graphic Designer'
- 'Senior Python Django Full-Stack Web Developer'
If the resume lacks enough detail for a full title, return the most specific title based on available data — but never guess missing technologies.",
    "projects": ["Project 1", "Project 2"],  // Only technical/personal/academic projects
    "github_username": "Only the username (no URL, no @). Must be mentioned explicitly.",
    "linkedin_url": "Full URL (must start with https://). Return null if not provided."
}}

Resume Text (truncated):
{resume_text}
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

