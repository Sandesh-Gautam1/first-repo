# api_server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import gridfs
import io
import pdfplumber
import os

app = Flask(__name__)
CORS(app)  # Allow anyone to access the API

# MongoDB connection
uri = "mongodb+srv://santoshraut9862281653:6R1eKwbwn26Qec6S@cluster0.1vlslv8.mongodb.net/hello"
client = MongoClient(uri)
db = client['hello']
fs = gridfs.GridFS(db)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API is running 🚀"}), 200

@app.route('/get_user_suggestions', methods=['GET'])
def get_user_suggestions():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({"error": "Missing user ObjectId in query."}), 400
    
    try:
        user = db.User.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found."}), 404
        
        # Check if auditFileData exists
        audit_data = user.get('auditFileData')
        if not audit_data:
            return jsonify({"error": "No audit file found for this user."}), 404
        
        # Save BSON binary as PDF
        pdf_path = f"temp_audit_{user_id}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(audit_data)
        
        # SCRAPE the PDF
        scraped_courses = scrape_pdf_for_courses(pdf_path)

        # OPTIONAL: Delete the temp file after processing
        os.remove(pdf_path)

        # Generate course suggestions
        suggestions = generate_course_suggestions(scraped_courses)
        
        return jsonify({
            "user": {
                "name": user.get("name"),
                "email": user.get("email"),
                "major": user.get("major"),
                "classStanding": user.get("classStanding")
            },
            "suggestedCourses": suggestions
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def scrape_pdf_for_courses(pdf_path):
    """ Placeholder simple PDF scraping: returns list of scraped course codes """
    extracted_courses = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    import re
                    matches = re.findall(r'[A-Z]{2,4}\s*[-]?\s*\d{3}', text)
                    for match in matches:
                        clean_code = match.replace(' ', '').replace('-', '')
                        extracted_courses.append(clean_code)
    except Exception as e:
        print("Error reading PDF:", e)
    return extracted_courses

def generate_course_suggestions(taken_courses):
    """ Generate dummy suggestions based on what courses were scraped """
    suggestions = []
    if "CS195" in taken_courses:
        suggestions.append({
            "courseCode": "CS 196",
            "courseName": "Introduction to Data Structures"
        })
    if "MA140" in taken_courses:
        suggestions.append({
            "courseCode": "MA 141",
            "courseName": "Calculus II"
        })
    if not suggestions:
        suggestions.append({
            "courseCode": "EN 111",
            "courseName": "English Composition"
        })
    return suggestions

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render needs this
    app.run(host='0.0.0.0', port=port)
