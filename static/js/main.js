import { ChatManager } from './chat.js';
import { FileManager } from './fileManager.js';

class App {
    constructor() {
        this.initialize();
    }

    initialize() {
        // 初始化聊天管理器
        this.chatManager = new ChatManager();
        // 初始化文件管理器
        this.fileManager = new FileManager();
    }
}

// 当页面加载完成时初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new App();
});