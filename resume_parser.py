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
You are a professional resume parser. Extract the following fields from the resume below and respond ONLY in the exact JSON format shown, without adding or removing any keys.

Instructions:
- ONLY extract data if it is explicitly stated in the resume. DO NOT infer, guess, or fill in missing data.
- Use null or empty lists where data is missing.
- Follow formatting rules exactly for each field.

Expected JSON structure:
{{
    "Weaknesses_in_Resume": "can't be null, Write 2–4 full sentences that clearly mention 3–5 weaknesses visible in the resume. Only include specific and fixable issues that are obvious in the text, such as missing contact details, unclear project descriptions, outdated skills, or lack of metrics. Avoid assumptions.",
    "Technical_Career_Tips": "can't be null, Write 2–4 concise and practical sentences giving 3–5 technical suggestions based strictly on the skills already listed. Mention adjacent tools or languages to learn, certifications to consider, or improvements to current projects or tech stack. No general advice or guessing.",
    "name": "First Last",  // Only first and second name.
    "location": "Governorate Country", //e.g.: Cairo Egypt - Madrid spain
    "email": "example@example.com",  // Must be lowercase.
    "education": "Field, University",  // e.g., Computer Science, Helwan University. If multiple entries, separate by semicolon (,) in the same string.
    "skills": ["Only", "Technical", "Skills", "10 Maxiumum"],  // No soft skills. Only technologies, tools, languages, or platforms.
    "career_name": "Predict the MOST SPECIFIC job title based strictly on the resume’s technical skills, tools, and projects — do not guess or generalize, The format must be: '[Technology/Tool] [Role] [Optional Specialization or Industry]'
Return concise but complete titles. DO NOT return vague outputs like 'Frontend Developer', 'Mobile Developer', or 'Software Engineer'. Always include the tech stack or tool when mentioned.
Examples:
- 'React Frontend Developer'
- 'Flutter Mobile App Developer'
    "projects": ["Project 1", "Project 2"],
    "github_username": "username",  // Only return if found inside an explicit GitHub URL. Otherwise, return null.
    "linkedin_url": "https://linkedin.com/in/username",  //  Only return if found inside an explicit linkedin URL. Otherwise, return null.
    "resume_score": 0,  // Return a whole number from 0 to 100 based ONLY on the following strict rules. Do not guess or add partial credit. Do not include any explanations.
}}

Resume Text (truncated):
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
