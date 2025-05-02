import fitz
from io import BytesIO
import json
from groq import Groq
import os

# Initialize Groq client (use environment variable for safety)
client = Groq(api_key='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')

def extract_resume_data(file):
    """Extract text from PDF and process with Groq AI to return structured resume data."""

    def read_pdf_file(file_obj):
        """Reads text from a PDF file (stream or file path)."""
        if isinstance(file_obj, str):
            # If file_obj is a string, assume it's a file path
            with open(file_obj, 'rb') as f:
                file_bytes = f.read()
        elif hasattr(file_obj, 'read'):
            # If file_obj is a stream, read the content
            file_bytes = file_obj.read()
        else:
            raise ValueError("Unsupported file type")

        # Open the PDF and extract text
        doc = fitz.open(stream=BytesIO(file_bytes), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])

    try:
        # Extract resume text from the file
        resume_text = read_pdf_file(file)

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
