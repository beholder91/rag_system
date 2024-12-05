export class FileManager {
    constructor() {
        this.uploadArea = null;
        this.fileInput = null;
        this.initialize();
    }

    initialize() {
        this.renderDocPanel();
        this.initializeElements();
        this.bindEvents();
        this.loadFiles();
    }

    renderDocPanel() {
        const docPanel = document.getElementById('docPanel');
        docPanel.innerHTML = this.getDocTemplate();
    }

    getDocTemplate() {
        return `
            <h2 class="text-xl font-semibold text-gray-900 mb-6">文档管理</h2>
            <div class="space-y-6">
                <div class="upload-area p-6 bg-gray-50 rounded-lg">
                    <input type="file" id="fileInput" class="hidden" accept=".doc,.docx">
                    <div id="uploadContent" class="text-center">
                        <label for="fileInput" class="cursor-pointer inline-flex flex-col items-center w-full">
                            <div class="p-3 bg-white rounded-full shadow-sm mb-3 inline-flex">
                                <svg class="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                                </svg>
                            </div>
                            <span class="text-sm font-medium text-gray-600">拖拽文件到此处或点击上传</span>
                            <span class="mt-2 text-xs text-gray-500">支持 .doc, .docx 格式</span>
                        </label>
                    </div>
                    <div id="selectedFile" class="hidden file-preview">
                        <div class="flex items-center space-x-3">
                            <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            <span class="text-sm text-gray-700 truncate max-w-[200px]"></span>
                        </div>
                        <button id="clearFileBtn" class="p-1 hover:bg-gray-200 rounded-full transition-colors">
                            <svg class="w-5 h-5 text-gray-500 hover:text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <button id="uploadButton"
                        class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors font-medium">
                    上传文档
                </button>
                <div class="mt-8">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">已上传文档</h3>
                    <div id="fileList" class="space-y-2 max-h-[300px] overflow-y-auto"></div>
                </div>
            </div>
        `;
    }

    initializeElements() {
        this.uploadArea = document.querySelector('.upload-area');
        this.fileInput = document.getElementById('fileInput');
    }

    bindEvents() {
        this.fileInput.addEventListener('change', () => this.updateFileDisplay());
        document.getElementById('clearFileBtn').addEventListener('click', (e) => this.clearFileSelection(e));
        document.getElementById('uploadButton').addEventListener('click', () => this.uploadFile());
        this.setupDragAndDrop();
    }

    setupDragAndDrop() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => this.uploadArea.classList.add('drag-over'));
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => this.uploadArea.classList.remove('drag-over'));
        });

        this.uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.fileInput.files = files;
            this.updateFileDisplay();
        });
    }

    updateFileDisplay() {
        const selectedFile = document.getElementById('selectedFile');
        const uploadContent = document.getElementById('uploadContent');
        const fileNameSpan = selectedFile.querySelector('span');

        if (this.fileInput.files.length > 0) {
            fileNameSpan.textContent = this.fileInput.files[0].name;
            selectedFile.classList.remove('hidden');
            uploadContent.classList.add('hidden');
        } else {
            selectedFile.classList.add('hidden');
            uploadContent.classList.remove('hidden');
        }
    }

    clearFileSelection(event) {
        event.preventDefault();
        event.stopPropagation();
        
        this.fileInput.value = '';
        this.updateFileDisplay();
    }

    async loadFiles() {
        try {
            const response = await fetch('/api/files');
            const files = await response.json();
            this.renderFileList(files);
        } catch (error) {
            console.error('加载文件列表失败:', error);
            this.renderFileList([], true);
        }
    }

    renderFileList(files, error = false) {
        const fileList = document.getElementById('fileList');
        if (error) {
            fileList.innerHTML = '<div class="text-red-500 text-sm p-3">加载文件列表失败</div>';
            return;
        }

        fileList.innerHTML = files.map(file => `
            <div class="file-item flex items-center p-3 hover:bg-gray-50 rounded-lg">
                <svg class="w-5 h-5 text-indigo-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <span class="text-gray-700">${file}</span>
            </div>
        `).join('');
    }

    async uploadFile() {
        const file = this.fileInput.files[0];
        if (!file) {
            alert('请选择文件');
            return;
        }
    
        // 创建加载弹窗
        const loadingModal = document.createElement('div');
        loadingModal.innerHTML = `
            <div class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-8 max-w-sm w-full mx-4 shadow-xl">
                    <div class="flex flex-col items-center space-y-4">
                        <div class="animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent"></div>
                        <h3 class="text-lg font-semibold text-gray-900">正在处理文档</h3>
                        <p class="text-gray-600 text-center text-sm">正在写入向量数据库，请稍候...</p>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(loadingModal);
    
        const formData = new FormData();
        formData.append('file', file);
    
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            
            // 移除加载弹窗
            document.body.removeChild(loadingModal);
            
            alert(result.message || '上传成功');
            await this.loadFiles();
            this.fileInput.value = '';
            this.updateFileDisplay();
        } catch (error) {
            // 确保在发生错误时也移除加载弹窗
            document.body.removeChild(loadingModal);
            
            alert('上传失败: ' + error);
            console.error('上传错误:', error);
        }
    }
}