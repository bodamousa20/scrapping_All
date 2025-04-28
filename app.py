# Flask Application (app.py)
from flask import Flask, jsonify, request, send_file
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from wuzzufSpider.wuzzufSpider.spiders.wuzzuf import WuzzufSpider
from wuzzufSpider.wuzzufSpider.spiders.courses import ClassCentralSpider
import os
import tempfile
from werkzeug.utils import secure_filename
import multiprocessing
import logging
import json
import time
from resume_parser import pdf_to_image, extract_resume_data
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

# Temporary Folder for Uploaded Files and Scraped Data
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
TEMP_JOBS_DATA_FILE = os.path.join(UPLOAD_FOLDER, 'wuzzuf_jobs_data.json')
TEMP_COURSES_DATA_FILE = os.path.join(UPLOAD_FOLDER, 'classcentral_courses_data.json')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_wuzzuf_spider_process(search_query, requiredPages, output_file):
    try:
        settings = get_project_settings()
        settings['FEEDS'] = {
            output_file: {'format': 'json', 'overwrite': True}
        }
        process = CrawlerProcess(settings)
        process.crawl(WuzzufSpider, search_query=search_query, requiredPages=requiredPages)
        process.start()
    except Exception as e:
        logger.error(f"Error running Wuzzuf spider process: {e}")
        with open(output_file, 'w') as f:
            json.dump({"error": str(e)}, f)

def run_classcentral_spider_process(search_query, requiredPages, output_file, language='english'):
    try:
        settings = get_project_settings()
        settings['FEEDS'] = {
            output_file: {'format': 'json', 'overwrite': True}
        }
        process = CrawlerProcess(settings)
        process.crawl(ClassCentralSpider, search_query=search_query, requiredPages=requiredPages, language=language)
        process.start()
    except Exception as e:
        logger.error(f"Error running Class Central spider process: {e}")
        with open(output_file, 'w') as f:
            json.dump({"error": str(e)}, f)

@app.route('/scrape-jobs', methods=['GET'])
def scrape_jobs():
    search_query = request.args.get('query', 'java')
    requiredPages = int(request.args.get('pages', 1))

    process = multiprocessing.Process(target=run_wuzzuf_spider_process, args=(search_query, requiredPages, TEMP_JOBS_DATA_FILE))
    process.start()
    process.join()

    time.sleep(2)  # Add a delay to ensure the file is fully written

    try:
        with open(TEMP_JOBS_DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Scraped jobs data file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Error decoding scraped jobs data"}), 500

    if "error" in data:
        return jsonify({"status": "error", "message": data["error"]}), 500

    results = data

    if not results:
        return jsonify({"status": "error", "message": "No jobs found"}), 404

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


@app.route('/scrape-courses', methods=['GET'])
def scrape_courses():
    search_query = request.args.get('query', 'python')
    requiredPages = int(request.args.get('pages', 1))
    language = request.args.get('lang', 'english')

    process = multiprocessing.Process(target=run_classcentral_spider_process, args=(search_query, requiredPages, TEMP_COURSES_DATA_FILE, language))
    process.start()
    process.join()

    time.sleep(2)  # Add a delay for course scraping as well

    try:
        with open(TEMP_COURSES_DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Scraped courses data file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Error decoding scraped courses data"}), 500

    if "error" in data:
        return jsonify({"status": "error", "message": data["error"]}), 500

    results = data

    if not results:
        return jsonify({"status": "error", "message": "No courses found"}), 404

    return jsonify({
        'result': results,
        'scraped-courses': len(results)
    })

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000, debug=True)
