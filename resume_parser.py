import pdfx
from io import BytesIO
import json
from groq import Groq
import os
import re
# Initialize Groq client (use environment variable for safety)
client = Groq(api_key='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')

def extract_resume_data(file):
    """Extract text from PDF and process with Groq AI to return structured resume data."""

    def read_pdf_file(pdf_path):
        pdf = pdfx.PDFx(pdf_path)
        text = pdf.get_text()
        urls = pdf.get_references_as_dict().get("url", [])
        return text + "\n\nExtracted URLs:\n" + "\n".join(urls)

    
    try:
        # Extract resume text from the file
        resume_text = read_pdf_file(file)
        resume_text = re.sub(r'\s+', ' ', resume_text)  # Replace multiple whitespace with single space
        resume_text = re.sub(r'[^\x00-\x7F]+', ' ', resume_text)  # Remove non-ASCII characters
        resume_text = resume_text.strip()

        # Groq prompt to extract structured resume data
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
  "education": ["Degree, Institution, Year"] all in one line Example Bachelor Degree in Computer Science, Helwan University, 2021 - 2025 GPA 3.2,
  "skills": ["List", "Of", "Technical", "Skills"],
  "career_name": "Predict the MOST SPECIFIC job title based strictly on the resume’s technical skills, tools, and projects  [Senior Level] [ Programming Language Or Tech FrameWork ] Developer example junior Java backend Devoleper , junior Laravel Backend Devoleper, Kotlin Mobile Devolper
  "projects": ["Project 1", "Project 2"],
  "github_username": "Only the username (no URL, no @). Must be mentioned explicitly. if not found put null",
  "linkedin_url": "Full URL (must start with https://). Return null if not provided."
}}

Resume:
{resume_text}
"""

        # Get the response from Groq API
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        # Parse and return the structured resume data
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        # In case of an error, return a meaningful message
        return {"error": str(e)}
