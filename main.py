import os
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from pdf_parser import parse_pdf
from ai_analyzer import analyze_report
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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
            
            return jsonify({'message': 'File uploaded and analyzed successfully', 'data': analysis_result['data']}), 200
        return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_markdown', methods=['POST'])
def download_markdown():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        markdown_content = f"""# {data['report_title']}

## Audit Organization
{data['audit_organization']}

## Audit Objectives
{', '.join(data['audit_objectives'])}

## Overall Conclusion
{data['overall_conclusion']}

## Key Findings
{chr(10).join(['- ' + finding for finding in data['key_findings']])}

## Recommendations
{chr(10).join(['- ' + recommendation for recommendation in data['recommendations']])}

## AI-Generated Insight
{data['llm_insight']}

## Potential Future Audit Objectives
{chr(10).join(['- ' + objective for objective in data['potential_audit_objectives']])}
"""

        buffer = io.BytesIO()
        buffer.write(markdown_content.encode('utf-8'))
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{data['report_title']}.md",
            mimetype='text/markdown'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
