from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
from config.config import API_KEY, KNOWLEDGE_BASE_DIR
from src.rag.rag_system import RAGSystem

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = KNOWLEDGE_BASE_DIR
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化 RAG 系统
rag = RAGSystem(
    knowledge_base_dir=KNOWLEDGE_BASE_DIR,
    api_key=API_KEY
)

# 支持的文件类型
ALLOWED_EXTENSIONS = {'doc', 'docx', 'pdf', 'txt', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if not file or not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型。支持的类型：doc, docx, pdf, txt, jpg, jpeg, png'}), 400
            
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 如果文件已存在，添加数字后缀
        base, extension = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base}_{counter}{extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            counter += 1
            
        file.save(file_path)
        
        # 重新加载知识库
        rag.load_knowledge_base(app.config['UPLOAD_FOLDER'])
        
        return jsonify({
            'message': '文件上传成功',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                files.append(filename)
        return jsonify(sorted(files))  # 按字母顺序排序文件列表
    except Exception as e:
        return jsonify({'error': f'获取文件列表失败: {str(e)}'}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        # 构建完整的文件路径
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 使用RAG系统的删除方法，它会同时处理存储和物理文件
        if rag.delete_file(file_path):
            return jsonify({'message': '文件删除成功'})
        else:
            return jsonify({'error': '文件删除失败'}), 500
        
    except Exception as e:
        return jsonify({'error': f'删除文件时出错: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': '消息不能为空'}), 400
        
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
    except Exception as e:
        return jsonify({'error': f'处理问题时出错: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)