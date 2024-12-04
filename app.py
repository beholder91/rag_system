from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
from config.config import API_KEY, KNOWLEDGE_BASE_DIR
from src.rag.rag_system import RAGSystem

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = KNOWLEDGE_BASE_DIR
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化 RAG 系统
rag = RAGSystem(
    knowledge_base_dir=KNOWLEDGE_BASE_DIR,
    api_key=API_KEY
)

ALLOWED_EXTENSIONS = {'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 重新加载知识库
        rag.load_knowledge_base(app.config['UPLOAD_FOLDER'])
        
        return jsonify({'message': 'File uploaded successfully'})
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/files', methods=['GET'])
def list_files():
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.endswith(('.doc', '.docx')):
            files.append(filename)
    return jsonify(files)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    result = rag.answer_question(data['message'])
    return jsonify({
        'answer': result['answer'],
        'sources': [
            {
                'content': doc['text'],
                'source': doc['metadata']['source'],
                'score': doc['score']
            }
            for doc in result['retrieved_documents']
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)