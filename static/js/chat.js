export class ChatManager {
    constructor() {
        this.container = null;
        this.initialize();
    }

    initialize() {
        this.renderChatPanel();
        this.bindEvents();
        // 加载Marked.js库
        this.loadMarkedJS();
    }

    loadMarkedJS() {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js';
        script.onload = () => {
            // 配置marked选项
            marked.setOptions({
                breaks: true,  // 支持GitHub风格的换行
                gfm: true,     // 启用GitHub风格Markdown
                highlight: function(code, language) {
                    if (language && hljs.getLanguage(language)) {
                        try {
                            return hljs.highlight(code, { language }).value;
                        } catch (__) {}
                    }
                    return hljs.highlight(code, { language: 'plaintext' }).value;
                },
                langPrefix: 'hljs language-'  // 添加highlight.js的类前缀
            });
        };
        document.head.appendChild(script);
    }

    renderChatPanel() {
        const chatPanel = document.getElementById('chatPanel');
        chatPanel.innerHTML = this.getChatTemplate();
        this.container = document.getElementById('chatContainer');
    }

    getChatTemplate() {
        return `
            <div id="chatContainer" class="chat-container h-[600px] overflow-y-auto p-6 space-y-4"></div>
            <div class="p-4 bg-gray-50 border-t border-gray-100">
                <div class="flex gap-3">
                    <input type="text" 
                           id="messageInput" 
                           class="flex-1 px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                           placeholder="请输入您的问题...">
                    <button id="sendButton"
                            class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                        发送
                    </button>
                </div>
            </div>
        `;
    }

    bindEvents() {
        const input = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        sendButton.addEventListener('click', () => this.sendMessage());
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        if (!message) return;

        this.appendMessage('user', message);
        input.value = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            const result = await response.json();
            
            if (result.answer) {
                this.appendMessage('bot', result.answer, result.sources);
            } else {
                this.appendMessage('bot', '抱歉，处理您的问题时出现错误。');
            }
        } catch (error) {
            this.appendMessage('bot', '抱歉，出现错误：' + error.message);
            console.error('Chat error:', error);
        }
    }

    appendMessage(type, text, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message max-w-[80%] ${type === 'user' ? 'ml-auto' : 'mr-auto'}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = `rounded-lg p-4 ${type === 'user' ? 
            'bg-indigo-600 text-white' : 
            'bg-gray-100 text-gray-800'
        }`;
        
        // 使用marked渲染Markdown
        if (typeof marked !== 'undefined') {
            // 为用户消息和机器人消息使用不同的渲染处理
            if (type === 'user') {
                contentDiv.textContent = text;
            } else {
                contentDiv.innerHTML = marked.parse(text);
                // 为代码块添加样式
                contentDiv.querySelectorAll('pre code').forEach(block => {
                    block.className = 'p-2 bg-gray-800 text-white rounded';
                });
                // 为表格添加基础样式
                contentDiv.querySelectorAll('table').forEach(table => {
                    table.className = 'border-collapse border border-gray-300 my-2';
                    table.querySelectorAll('th, td').forEach(cell => {
                        cell.className = 'border border-gray-300 p-2';
                    });
                });
            }
        } else {
            contentDiv.textContent = text;
        }
        
        messageDiv.appendChild(contentDiv);

        if (sources?.length) {
            messageDiv.appendChild(this.createSourcesElement(sources));
        }

        this.container.appendChild(messageDiv);
        this.container.scrollTop = this.container.scrollHeight;
        messageDiv.classList.add('animate__animated', 'animate__fadeInUp');
    }

    createSourcesElement(sources) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'mt-2 p-3 bg-gray-50 rounded-lg text-sm border border-gray-200';
        sourcesDiv.innerHTML = sources.map(source => `
            <div class="mb-3 last:mb-0">
                <div class="flex items-center justify-between mb-1">
                    <div class="font-medium text-gray-700">
                        ${source.source.split('/').pop()}
                    </div>
                    <div class="text-indigo-600 text-xs">
                        相似度：${(source.score * 100).toFixed(1)}%
                    </div>
                </div>
                <div class="text-gray-600 text-sm">
                    ${source.content}
                </div>
            </div>
        `).join('');
        return sourcesDiv;
    }
}