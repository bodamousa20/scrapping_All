# Flask Application (app.py)
from flask import Flask, jsonify, request, send_file
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from wuzzufSpider.wuzzufSpider.spiders.wuzzuf import WuzzufSpider
import os
import tempfile
from werkzeug.utils import secure_filename
from resume_parser import pdf_to_image, extract_resume_data
import multiprocessing
import logging
import json
from scrape_course import scrape_classcentral_courses

app = Flask(__name__)

# Temporary Folder for Uploaded Files and Scraped Data
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
TEMP_SCRAPED_DATA_FILE = os.path.join(UPLOAD_FOLDER, 'scraped_data.json')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_spider_process(search_query, requiredPages, output_file):
    try:
        settings = get_project_settings()
        settings['FEEDS'] = {
            output_file: {'format': 'json', 'overwrite': True}
        }
        process = CrawlerProcess(settings)
        process.crawl(WuzzufSpider, search_query=search_query, requiredPages=requiredPages)
        process.start()
    except Exception as e:
        logger.error(f"Error running spider process: {e}")
        with open(output_file, 'w') as f:
            json.dump({"error": str(e)}, f)

@app.route('/scrape', methods=['GET'])
def scrape():
    search_query = request.args.get('query', 'java')
    requiredPages = int(request.args.get('pages', 1))

    process = multiprocessing.Process(target=run_spider_process, args=(search_query, requiredPages, TEMP_SCRAPED_DATA_FILE))
    process.start()
    process.join()

    try:
        with open(TEMP_SCRAPED_DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Scraped data file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Error decoding scraped data"}), 500

    if "error" in data:
        return jsonify({"status": "error", "message": data["error"]}), 500

    results = data

    if not results:
        return jsonify({"status": "error", "message": "No results found"}), 404

    return jsonify({
        'result': results,
        'scraped-jobs': len(results)
    })

@app.route('/process-resume', methods=['POST'])
def process_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    try:
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)

        # image_path = pdf_to_image(pdf_path)
        parsed_data = extract_resume_data(pdf_path)

        response = {
            "data": parsed_data,
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for f in os.listdir(app.config['UPLOAD_FOLDER']):
            if f != 'preview.jpg':
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))



@app.route('/courses', methods=['GET'])
def get_courses():
    query = request.args.get('query', default='python')
    pages = int(request.args.get('pages', default=1))
    courses = scrape_classcentral_courses(query, pages)
    result = {
        "scraped-courses" : len(courses),
        "courses": courses
    }
    return jsonify(result)


    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000, debug=True)
