import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ['FLASK_APP'] = 'main.py'

import os
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from database import init_db, get_db
from models import Report
from pdf_parser import parse_pdf
from ai_analyzer import analyze_report
from utils import generate_markdown
from flask_migrate import Migrate

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = init_db(app)
migrate = Migrate(app, db)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Parse PDF and analyze content
            pdf_content = parse_pdf(file_path)
            ai_model = request.form.get('ai_model', 'gpt-4')
            analysis_result = analyze_report(pdf_content, ai_model=ai_model)
            if not analysis_result['success']:
                return jsonify({'error': analysis_result['error']}), 500
            analysis_result = analysis_result['data']
            
            # Save to database
            db = get_db()
            report = Report(
                file_name=filename,
                content=analysis_result
            )
            db.add(report)
            db.commit()
            
            return jsonify({'message': 'File uploaded and analyzed successfully', 'id': report.id}), 200
        return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reports', methods=['GET'])
def get_reports():
    db = get_db()
    reports = db.query(Report).order_by(Report.upload_date.desc()).all()
    return jsonify([report.to_dict() for report in reports])

@app.route('/report/<int:report_id>', methods=['GET'])
def get_report(report_id):
    db = get_db()
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        return jsonify(report.to_dict())
    return jsonify({'error': 'Report not found'}), 404

@app.route('/export/<int:report_id>', methods=['GET'])
def export_report(report_id):
    db = get_db()
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        markdown_content = generate_markdown(report)
        return send_file(
            markdown_content,
            as_attachment=True,
            download_name=f"{report.file_name}.md",
            mimetype='text/markdown'
        )
    return jsonify({'error': 'Report not found'}), 404

@app.route('/delete/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    db = get_db()
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        db.delete(report)
        db.commit()
        return jsonify({'message': 'Report deleted successfully'}), 200
    return jsonify({'error': 'Report not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
