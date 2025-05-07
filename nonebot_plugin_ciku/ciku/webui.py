import json
from fastapi import APIRouter, Response, WebSocket, Request, Query,FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from nonebot import get_app
from fastapi import WebSocketDisconnect
import nonebot
from starlette.websockets import WebSocketState
import asyncio
from pathlib import Path
from nonebot.log import logger
from nonebot import require
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

data_dir = store.get_plugin_data_dir()

ck_path = data_dir / "词库文件"
custom_dir = data_dir / "自定义拓展"
group_list = data_dir / "群列表"
if not group_list.exists():
    group_list.mkdir()

from nonebot import get_driver
driver = get_driver()

router = APIRouter()
log_subscriptions = set()
log_lock = asyncio.Lock()

def validate_filename(filename: str, file_type: str) -> bool:
    try:
        target_dir = ck_path if file_type == "ck" else custom_dir
        resolved_path = (target_dir / filename).resolve()
        return (
            resolved_path.parent == target_dir.resolve()
            and target_dir.resolve() in resolved_path.parents
        )
    except (ValueError, FileNotFoundError):
        return False

@router.get("/ck_webui", response_class=HTMLResponse)
async def web_interface(request: Request):
    return """<!DOCTYPE html>
<html>
<head>
    <title>词库管理系统</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script src="https://unpkg.com/monaco-editor-locales@1.0.1/locales/zh-cn.js"></script>

    <link href="https://unpkg.com/monaco-editor@latest/min/vs/editor/editor.main.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
         @media screen and (max-width: 768px) {
            body {
                height: auto;
                min-height: 100vh;
            }
            .fab-container {
                bottom: 20px;
                right: 20px;
            }
            
            .fab-main {
                width: 48px;
                height: 48px;
                font-size: 20px;
            }
            
            .fab-tooltip {
                left: 55px;
                font-size: 11px;
                padding: 5px 10px;
            }
            .fab-tooltip {
                left: 45px !important;
                max-width: 120px;
            }

            .editor-container {
                margin-top: 0px;
            }

            #editor {
                height: 0vh;
            }

            .dialog {
                width: 90%;
                max-width: 400px;
                padding: 15px;
            }

            .file-item {
                padding: 12px;
                margin: 6px 0;
            }

            .log-entry {
                font-size: 12px;
                padding: 6px;
            }
            #logs-panel {
                top: 0px !important;
                height: calc(100% - 48px); 
            }

            .file-header button {
                padding: 8px 12px;
            }
            .file-manager {
                width: 100%;
                left: -100%;
                z-index: 1001;
                background: rgba(37, 37, 38, 0.98);
            }
            
            .file-manager.is-active {
                box-shadow: none;
            }
            
            .sidebar-backdrop {
                background: rgba(0,0,0,0.7);
                z-index: 1000;
            }
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: #1e1e1e;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
            height: 100vh;
            display: flex;
            position: relative;
        }

        #editor {
            width: 100%;
            height: 100%;
        }

        .file-manager {
            width: 300px;
            background: #252526;
            position: fixed;
            left: -300px;
            top: 0;
            bottom: 0;
            z-index: 1000;
            transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-right: 1px solid #3c3c3c;
            display: flex;
            flex-direction: column;
        }

        .file-manager.is-active {
            left: 0;
            box-shadow: 2px 0 15px rgba(0,0,0,0.5);
        }
        .file-header {
            padding: 15px;
            border-bottom: 1px solid #3c3c3c;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .file-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }

        .file-item {
            padding: 8px 12px;
            margin: 4px 0;
            background: #2d2d2d;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }

        .file-item:hover {
            background: #37373d;
        }

        .editor-container {
            flex: 1;
            height: 100vh;
            transition: margin-left 0.3s;
        }

        .sidebar-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.3);
            z-index: 999;
            display: none;
        }


        button {
            padding: 6px 12px;
            background: #3273c5;
            border: none;
            border-radius: 4px;
            color: white;
            cursor: pointer;
            transition: background 0.2s;
        }

        button:hover {
            background: #3b8ae6;
        }

        #logs-panel {
            display: none;
            flex-direction: column;
            position: absolute;  
            top: 0px;         
            left: 0;
            right: 0;
            bottom: 0;
            background: #1e1e1e; 
            z-index: 100;
        }
        

        .log-header {
            padding: 10px;
            background: #303030;
            border-bottom: 1px solid #3c3c3c;
        }

        .log-content {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }

        .log-entry {
            padding: 8px;
            margin: 4px 0;
            background: #2d2d2d;
            border-radius: 4px;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatIn {
            from {
                transform: translateY(100px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        .dialog {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #252526;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 15px rgba(0,0,0,0.5);
            z-index: 1000;
        }

        .dialog input {
            background: #333;
            border: 1px solid #444;
            color: white;
            padding: 8px;
            margin-bottom: 10px;
            width: 100%;
        }
        .mode-switcher {
            margin-left: 10px;
            background: #444 !important;
        }
        .mode-switcher.active {
            background: #3273c5 !important;
        }
        .settings-container {
            position: relative;
            margin-left: 10px;
        }

        .settings-btn {
            background: none !important;
            padding: 6px 12px !important;
        }


        .menu-item {
            width: 100%;
            padding: 10px 15px !important;
            text-align: left;
            background: none !important;
            border-radius: 0 !important;
        }

        /* 全屏群组面板 */
        .group-panel {
            position: fixed;
            top: 0;
            left: 100%;
            width: 100%;
            height: 100vh;
            background: #1e1e1e;
            transition: left 0.3s;
            z-index: 2000;
        }

        .group-panel.active {
            left: 0;
        }

        .panel-header {
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #3c3c3c;
            background: #252526;
        }

        .back-btn {
            background: none !important;
            margin-right: 20px;
        }

        .search-box {
            display: flex;
            gap: 10px;
            padding: 15px;
            background: #252526;
        }

        .search-box input {
            flex: 1;
            padding: 8px 12px;
        }

        /* 滑动开关样式 */
        .switch {
            position: relative;
            display: inline-block;
            width: 48px;
            height: 24px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #666;
            transition: .3s;
            border-radius: 12px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 20px;
            width: 20px;
            left: 2px;
            bottom: 2px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: #3273c5;
        }

        input:checked + .slider:before {
            transform: translateX(24px);
        }

        /* 群组项样式 */
        .group-item {
            display: flex;
            align-items: center;
            padding: 12px 20px;
            border-bottom: 1px solid #333;
        }

        .group-avatar {
            width: 40px;
            height: 40px;
            border-radius: 6px;
            margin-right: 15px;
        }
        .group-list {
            height: calc(100vh - 160px);
            overflow-y: auto;
        }

        .group-info {
            flex: 1;
            margin-right: 15px;
            min-width: 0;
        }

        .group-name {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 14px;
        }

        .group-id {
            color: #666;
            font-size: 12px;
            margin-top: 2px;
        }
        .fab-container {
            position: fixed;
            bottom: 30px;
            right: 30px;  /* 改为右侧定位 */
            left: auto;    /* 清除左侧定位 */
            z-index: 1000;
            display: flex;
            flex-direction: column-reverse;
            gap: 15px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .fab-container {
            animation: floatIn 0.6s cubic-bezier(0.23, 1, 0.32, 1);
        }

        /* 优化按钮投影 */
        .fab-main {
            box-shadow: 0 10px 25px rgba(50, 115, 197, 0.25);
        }

        .fab-item:hover {
            box-shadow: 0 6px 15px rgba(50, 115, 197, 0.3);
        }

        /* 调整工具提示位置 */
        .fab-tooltip {
            position: absolute;
            right: 60px; /* 固定左侧定位 */
            left: auto !important; /* 覆盖原有右侧定位 */
            transform: translateY(-50%);
            top: 50%;
            background: rgba(37, 37, 38, 0.95);
            padding: 6px 12px;
            border-radius: 4px;
            color: white;
            font-size: 12px;
            white-space: nowrap;
            pointer-events: none;
            opacity: 0;
            transition: 0.2s;
            /* 新增边缘检测 */
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .fab-item:hover .fab-tooltip {
            opacity: 1;
            left: 50px;  /* 悬停时微调 */
        }

        .fab-main {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3273c5, #3b8ae6);
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(50, 115, 197, 0.3);
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .fab-main:hover {
            transform: scale(1.1) rotate(90deg);
            box-shadow: 0 12px 25px rgba(50, 115, 197, 0.4);
        }

        .fab-menu {
            display: none;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 15px;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s;
        }

        .fab-menu.show {
            display: flex;
            opacity: 1;
            transform: translateY(0);
        }

        .fab-item {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(37, 37, 38, 0.9);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        .fab-item:hover {
            background: #3273c5;
            transform: scale(1.15);
        }

        /* 优化其他UI元素 */
        .file-manager {
            background: rgba(37, 37, 38, 0.95);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        .file-manager.animate-slide {
            transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1), 
                        opacity 0.2s ease;
        }

        .file-item {
            background: rgba(45, 45, 45, 0.6);
            margin: 8px 0;
            transition: all 0.2s;
        }

        .file-item:hover {
            background: rgba(55, 55, 61, 0.8);
            transform: translateX(5px);
        }
        

        .dialog {
            background: rgba(37, 37, 38, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .log-entry {
            background: rgba(45, 45, 45, 0.6);
            margin: 8px 0;
            padding: 12px;
            border-radius: 6px;
        }

        /* 优化滚动条 */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.1);
        }

        ::-webkit-scrollbar-thumb {
            background: #3273c5;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="sidebar-backdrop" onclick="toggleSidebar()"></div>
    <!-- 文件管理器 -->
    <div class="file-manager">
        <div class="file-header">
            <h3>词库文件</h3>
            <button onclick="showCreateDialog()">新建</button>
        </div>
        <div class="file-list" id="file-list"></div>
    </div>

    <div class="editor-container">
        <div class="fab-container">
            <button class="fab-main" onclick="toggleFabMenu()">
                <i class="fas fa-cog"></i>
            </button>
            
            <div class="fab-menu" id="fabMenu">
                <div class="fab-item" onclick="handleFileListToggle(event)">
                    <i class="fas fa-folder-open"></i>
                    <span class="fab-tooltip">文件列表</span>
                </div>
                <div class="fab-item" onclick="switchMode('ck')">
                    <i class="fas fa-book"></i>
                    <span class="fab-tooltip">编辑词库</span>
                </div>
                <div class="fab-item" onclick="switchMode('py')">
                    <i class="fas fa-code"></i>
                    <span class="fab-tooltip">编辑拓展</span>
                </div>
                <div class="fab-item" onclick="showPanel('logs')">
                    <i class="fas fa-clipboard-list"></i>
                    <span class="fab-tooltip">查看日志</span>
                </div>
                <div class="fab-item" onclick="saveFile()">
                    <i class="fas fa-save"></i>
                    <span class="fab-tooltip">保存文件</span>
                </div>
                <div class="fab-item" onclick="showGroupSwitch()">
                    <i class="fas fa-users-cog"></i>
                    <span class="fab-tooltip">群组管理</span>
                </div>
            </div>
        </div>

        <div id="editor" style="flex: 1; border: 1px solid #3c3c3c;"></div>

        <div id="logs-panel">
            <div class="log-header">实时日志</div>
            <div class="log-content" id="log-content"></div>
        </div>
        <div id="group-switch-panel" class="group-panel">
            <div class="panel-header">
                <button class="back-btn" onclick="closeGroupSwitch()">← 返回编辑器</button>
                <h3>群组开关管理</h3>
            </div>
            <div class="search-box">
                <input type="text" id="group-search" placeholder="搜索群名/群号">
                <button class="search-btn" onclick="refreshGroupList()">搜索</button>
            </div>
            <div class="global-switch">
                <span>总开关：</span>
                <label class="switch">
                    <input type="checkbox" id="global-switch">
                    <span class="slider"></span>
                </label>
            </div>
            <div class="group-list" id="group-list"></div>
        </div>
    </div>

    <div id="create-dialog" class="dialog" style="display: none">
        <h3 style="margin-bottom: 15px;">新建词库文件</h3>
        <input type="text" id="new-filename" placeholder="输入文件名（无需.ck后缀）">
        <div style="display: flex; gap: 10px; margin-top: 15px;">
            <button onclick="createFile()">创建</button>
            <button onclick="closeDialog()" style="background: #666">取消</button>
        </div>
    </div>

    <script src="https://unpkg.com/monaco-editor@latest/min/vs/loader.js"></script>
    <script>
        function handleFileListToggle(event) {
            event.stopPropagation(); // 阻止事件冒泡
            toggleSidebar();
            toggleFabMenu(); // 同时关闭悬浮菜单
        }
        const fabContainer = document.querySelector('.fab-container');
        let lastScrollTop = 0;

        window.addEventListener('scroll', () => {
            const st = window.pageYOffset || document.documentElement.scrollTop;
            
            // 向下滚动时隐藏
            if (st > lastScrollTop){
                fabContainer.style.transform = 'translateY(100px)';
            } else {  // 向上滚动时显示
                fabContainer.style.transform = 'translateY(0)';
            }
            lastScrollTop = st <= 0 ? 0 : st;
        }, false);

        // 优化触摸交互
        let tapTimer;
        fabContainer.addEventListener('touchstart', (e) => {
            tapTimer = setTimeout(() => {
                e.preventDefault();
                toggleFabMenu();
            }, 200);
        });

        fabContainer.addEventListener('touchend', () => {
            clearTimeout(tapTimer);
        });
        let isFabMenuOpen = false;

        function toggleFabMenu() {
            const fabMenu = document.getElementById('fabMenu');
            isFabMenuOpen = !isFabMenuOpen;
            fabMenu.classList.toggle('show');
            
            // 点击外部关闭
            if (isFabMenuOpen) {
                setTimeout(() => {
                    document.addEventListener('click', closeFabMenuOnClickOutside);
                }, 10);
            }
        }

        function closeFabMenuOnClickOutside(e) {
            if (!e.target.closest('.fab-container')) {
                toggleFabMenu();
                document.removeEventListener('click', closeFabMenuOnClickOutside);
            }
        }
        let currentMode = 'ck';
        let currentFile = null;
        function toggleSidebar() {
            const sidebar = document.querySelector('.file-manager');
            const backdrop = document.querySelector('.sidebar-backdrop');
            
            // 添加动画类
            sidebar.classList.add('animate-slide');
            backdrop.style.display = sidebar.classList.contains('is-active') ? 'none' : 'block';
            
            // 使用requestAnimationFrame确保动画流畅
            requestAnimationFrame(() => {
                sidebar.classList.toggle('is-active');
            });
        }
        // 模式切换函数
        function switchMode(newMode) {
            showPanel('editor'); 
            if (currentMode === newMode) return;
            
            currentMode = newMode;
            // 更新按钮状态
            document.querySelectorAll('.mode-switcher').forEach(btn => {
                btn.classList.toggle('active', btn.id === `${newMode}-mode`);
            });
            
            // 重置编辑器状态
            currentFile = null;
            editor.setValue('');
            
            // 切换语言高亮
            monaco.editor.setModelLanguage(editor.getModel(), newMode === 'ck' ? 'ck' : 'python');
            
            // 关键修复：更新文件列表请求参数
            loadFileList();  // 显式调用文件列表刷新
        }

        let touchStartX = 0;
        const SWIPE_THRESHOLD = 50;

        document.addEventListener('touchstart', e => {
            touchStartX = e.touches[0].clientX;
        });

        document.addEventListener('touchend', e => {
            const touchEndX = e.changedTouches[0].clientX;
            const diffX = touchEndX - touchStartX;

            if (Math.abs(diffX) > SWIPE_THRESHOLD) {
                if (diffX > 0) { 
                    const sidebar = document.querySelector('.file-manager');
                    if (!sidebar.classList.contains('is-active')) {
                        toggleSidebar();
                    }
                } else { 
                    const sidebar = document.querySelector('.file-manager');
                    if (sidebar.classList.contains('is-active')) {
                        toggleSidebar();
                    }
                }
            }
        });
        let editor = null;
        require.config({
            paths: { 
                vs: 'https://unpkg.com/monaco-editor@latest/min/vs' 
            },
            'vs/nls': {
                availableLanguages: { '*': 'zh-cn' }
            }
        });
        require(['vs/editor/editor.main'], () => {
            monaco.languages.register({ id: 'ck' });

            monaco.languages.setMonarchTokensProvider('ck', {
            tokenizer: {
                root: [
                // 注释
                //[/&&.*/, 'comment.line.ck'],
                
                // 函数块
                [/\$/, { token: 'entity.name.function.ck', bracket: '@open', next: '@function' }],
                
                // 变量
                [/%/, { token: 'variable.other.ck', bracket: '@open', next: '@variable' }],
                
                // 图片
                [/±/, { token: 'constant.image.ck', bracket: '@open', next: '@image' }],
                
                // 控制关键字
                [/(回调|调用)/, 'keyword.control.ck'],
                
                // 条件语句
                [/(返回|如果尾|如果)/, 'keyword.control.conditional.ck'],
                
                // 操作符
                [/[=><:;+\-*]/, 'keyword.operator.ck'],
                
                // 数组
                [/@(?!%)/, 'constant.array.ck'],
                
                // 数字
                [/(?<==)\d+/, 'constant.numeric.ck'],
                
                // 括号
                [/\[/, { token: 'punctuation.bracket.ck', bracket: '@open', next: '@bracket' }]
                ],

                function: [
                [/\$/, { token: 'entity.name.function.ck', bracket: '@close', next: '@pop' }],
                { include: 'root' }
                ],
                
                variable: [
                [/%/, { token: 'variable.other.ck', bracket: '@close', next: '@pop' }],
                [/[\w\u4e00-\u9fa5]+/, 'variable.other.ck']
                ],
                
                image: [
                [/±/, { token: 'constant.image.ck', bracket: '@close', next: '@pop' }],
                [/[\w\u4e00-\u9fa5]+/, 'constant.image.ck']
                ],
                
                bracket: [
                [/\]/, { token: 'punctuation.bracket.ck', bracket: '@close', next: '@pop' }],
                { include: 'root' }
                ]
            }
            });

            // 3. 注册主题
            monaco.editor.defineTheme('ck-theme', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'entity.name.function.ck', foreground: '#FF69B4' },
                { token: 'variable.other.ck', foreground: '#87CEFA' },
                { token: 'punctuation.bracket.ck', foreground: '#7FFFAA' },
                { token: 'constant.array.ck', foreground: '#F0E68C' },
                { token: 'keyword.control.ck', foreground: '#FFA500' },
                { token: 'keyword.operator.ck', foreground: '#0000FF' },
                { token: 'keyword.control.conditional.ck', foreground: '#FF0000' },
                { token: 'constant.image.ck', foreground: '#FFB6C1' },
                { token: 'constant.numeric.ck', foreground: '#00FF00' },
                { token: 'comment.line.ck', foreground: '#808080' }
            ],
            colors: {
                'editor.foreground': '#e0e0e0',
                'editor.background': '#1e1e1e'
            }
            });

            // 4. 初始化编辑器时应用主题
            editor = monaco.editor.create(document.getElementById('editor'), {
            value: '',
            language: 'ck',
            theme: 'ck-theme',
            automaticLayout: true,
            minimap: { enabled: false },
            wordWrap: 'off', // 禁用自动换行
            fontSize: window.innerWidth < 768 ? 14 : 16, // 移动端字体调整
            lineHeight: window.innerWidth < 768 ? 24 : 28
        });
            loadFileList();
        });
        window.addEventListener('resize', () => {
            if (window.innerWidth < 768 && document.querySelector('.file-manager.is-active')) {
                toggleSidebar();
            }
        });

        // 修改后的点击外部关闭逻辑
        document.addEventListener('click', function(event) {
            const sidebar = document.querySelector('.file-manager');
            const backdrop = document.querySelector('.sidebar-backdrop');
        });


        async function loadFileList() {
            try {
                // 确保携带当前模式参数
                const res = await fetch(`/ck_webui/files?type=${currentMode}`);
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                
                const files = await res.json();
                renderFileList(files);
            } catch (err) {
                console.error('文件列表加载失败:', err);
                alert('无法加载文件列表');
            }
        }
        function renderFileList(files) {
            const list = document.getElementById('file-list');
            list.innerHTML = files.map(file => `
                <div class="file-item" onclick="loadFile('${file.name}')">
                    <span>📄 ${file.name}</span>
                    <button onclick="deleteFile('${file.name}', event)">删除</button>
                </div>
            `).join('');
            
            // 新增：根据模式更新侧边栏标题
            document.querySelector('.file-header h3').textContent = 
                currentMode === 'ck' ? '词库文件' : '扩展脚本';
        }
        async function loadFile(filename) {
            try {
                const res = await fetch(`/ck_webui/load_ck?file=${encodeURIComponent(filename)}&type=${currentMode}`);
                const content = await res.text();
                editor.setValue(content);
                currentFile = filename;
            } catch (err) {
                alert('加载文件失败');
            }
        }


        async function saveFile() {
            if (!currentFile) return alert('请先选择文件');
            try {
                let content = editor.getValue();
                content = content.replace('\\r\\n', '\\n').replace('\\r', '\\n');
                // 添加type参数
                await fetch(`/ck_webui/save_ck?file=${currentFile}&type=${currentMode}`, {
                    method: 'POST',
                    body: content,
                    headers: { 'Content-Type': 'text/plain' }
                });
                alert('保存成功');
            } catch (err) {
                alert('保存失败');
            }
        }
        // 对话框管理
        function showCreateDialog() {
            document.getElementById('create-dialog').style.display = 'block';
        }

        function closeDialog() {
            document.getElementById('create-dialog').style.display = 'none';
        }

        async function createFile() {
            const ext = currentMode === 'ck' ? '.ck' : '.py';
            const filename = document.getElementById('new-filename').value + ext;
            
            try {
                const res = await fetch(`/ck_webui/create?file=${filename}&type=${currentMode}`, { 
                    method: 'POST' 
                });
                const result = await res.json();
                if (result.status === 'success') {
                    closeDialog();
                    loadFileList();
                } else {
                    alert(result.msg);
                }
            } catch (err) {
                alert('创建文件失败');
            }
        }

        async function deleteFile(filename, event) {
            event.stopPropagation();
            if (!confirm(`确定删除 ${filename} 吗？`)) return;
            try {
                await fetch(`/ck_webui/delete?file=${filename}&type=${currentMode}`, { 
                    method: 'DELETE' 
                });
                loadFileList();
            } catch (err) {
                alert('删除失败');
            }
        }

        // 面板切换
        function showPanel(type) {
            const isLogs = type === 'logs';
            document.getElementById('logs-panel').style.display = isLogs ? 'flex' : 'none';
            document.getElementById('editor').style.display = isLogs ? 'none' : 'block';
        }

        // 日志系统
        const logContent = document.getElementById('log-content');
        let logsWs = null;
        let reconnectAttempts = 0;
        let autoScroll = true;
        let scrollTimeout = null;
        let isProgrammaticScroll = false;

        // 滚动事件处理
        logContent.addEventListener('scroll', () => {
            if (isProgrammaticScroll) {
                isProgrammaticScroll = false;
                return;
            }

            const isAtBottom = logContent.scrollHeight - logContent.clientHeight <= logContent.scrollTop + 1;
            
            if (isAtBottom) {
                autoScroll = true;
                clearTimeout(scrollTimeout);
            } else {
                autoScroll = false;
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    autoScroll = true;
                }, 5000);
            }
        });

        function connectWebSocket() {
            logsWs = new WebSocket(`ws://${location.host}/ck_webui/logs`);

            logsWs.onmessage = (event) => {
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = `
                    <span style="color: #7f8c8d">[${new Date().toLocaleTimeString()}] 【LOG】</span>
                    ${event.data}
                `;
                logContent.appendChild(entry);
                
                if (autoScroll) {
                    isProgrammaticScroll = true;
                    logContent.scrollTop = logContent.scrollHeight;
                }
            };

            logsWs.onclose = () => {
                if (reconnectAttempts < 5) {
                    setTimeout(connectWebSocket, 1000 * ++reconnectAttempts);
                }
            };

            logsWs.onerror = (err) => {
                console.error('WebSocket错误:', err);
                logsWs.close();
            };
        }

        // 初始化WebSocket连接
        connectWebSocket();
        let groupConfig = [];
        document.getElementById('group-search').addEventListener('input', function(e) {
            filterGroups(e.target.value);
        });
        document.getElementById('global-switch').addEventListener('change', function(e) {
            const isChecked = e.target.checked;
            
            // 更新所有群组开关
            document.querySelectorAll('.group-item input').forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            
            // 更新配置
            groupConfig.global_enabled = isChecked;
            groupConfig.groups = groupConfig.groups.map(g => ({
                ...g,
                enabled: isChecked
            }));
            
            updateSwitchConfig();
        });
        function filterGroups(keyword) {
            const groups = Array.from(document.querySelectorAll('.group-item'));
            const lowerKeyword = keyword.toLowerCase();
            
            groups.forEach(group => {
                const name = group.querySelector('.group-name').textContent.toLowerCase();
                const id = group.querySelector('.group-id').textContent.toLowerCase();
                const isMatch = name.includes(lowerKeyword) || id.includes(lowerKeyword);
                
                group.style.display = isMatch ? 'flex' : 'none';
                group.style.order = isMatch ? -1 : 0;
            });
        }

        function showGroupSwitch() {
            document.getElementById('group-switch-panel').classList.add('active');
            loadGroupData();
        }

        async function loadGroupData() {
            try {
                const [groupsRes, configRes] = await Promise.all([
                    fetch('/ck_webui/groups'),
                    fetch('/ck_webui/switch-config')
                ]);
                const groups = await groupsRes.json();
                groupConfig = await configRes.json();
                renderGroups(groups);
            } catch (err) {
                console.error('加载群数据失败:', err);
            }
        }

        function renderGroups(groups) {
            const listEl = document.getElementById('group-list');
            // 从新配置结构中获取群组状态
            const groupStates = groupConfig.groups || [];
            
            listEl.innerHTML = groups.map(group => {
                // 匹配新版配置结构
                const groupState = groupStates.find(c => c.group_id === group.group_id);
                const isOn = groupState ? groupState.enabled : groupConfig.global_enabled;
                
                return `
                    <div class="group-item" data-group-id="${group.group_id}">
                        <img src="http://p.qlogo.cn/gh/${group.group_id}/${group.group_id}/0" 
                            class="group-avatar"
                            onerror="this.src='https://via.placeholder.com/40'">
                        <div class="group-info">
                            <div class="group-name">${group.group_name}</div>
                            <div class="group-id">(${group.group_id})</div>
                        </div>
                        <label class="switch">
                            <input type="checkbox" ${isOn ? 'checked' : ''} 
                                onchange="updateGroupSwitch(${group.group_id}, this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                `;
            }).join('');

            // 初始化总开关状态
            updateGlobalSwitch();
        }

        function updateGlobalSwitch() {
            const globalSwitch = document.getElementById('global-switch');
            const checkboxes = document.querySelectorAll('.group-item input');
            
            // 计算开启数量
            const enabledCount = Array.from(checkboxes).filter(cb => cb.checked).length;
            
            // 更新总开关状态
            if (enabledCount === checkboxes.length) {
                globalSwitch.checked = true;
                globalSwitch.indeterminate = false;
            } else if (enabledCount === 0) {
                globalSwitch.checked = false;
                globalSwitch.indeterminate = false;
            } else {
                globalSwitch.checked = false;
                globalSwitch.indeterminate = true;
            }
        }
        async function updateGroupSwitch(groupId, enabled) {
            // 更新本地配置
            const groupIndex = groupConfig.groups.findIndex(c => c.group_id === groupId);
            if (groupIndex > -1) {
                groupConfig.groups[groupIndex].enabled = enabled;
            } else {
                groupConfig.groups.push({ group_id: groupId, enabled });
            }
            
            // 自动同步总开关状态
            const allEnabled = groupConfig.groups.every(g => g.enabled);
            const anyDisabled = groupConfig.groups.some(g => !g.enabled);
            
            if (allEnabled) {
                groupConfig.global_enabled = true;
            } else if (anyDisabled) {
                groupConfig.global_enabled = false;
            }
            
            // 保存到服务器
            await fetch('/ck_webui/update-switch-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(groupConfig)
            });
            
            updateGlobalSwitch();
        }
        async function updateSwitchConfig() {
            const globalState = document.getElementById('global-switch').checked;
            const config = {
                global_enabled: globalState,
                groups: Array.from(document.querySelectorAll('.group-item')).map(item => ({
                    group_id: parseInt(item.dataset.groupId),
                    enabled: item.querySelector('input').checked
                }))
            };
            
            await fetch('/ck_webui/update-switch-config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
        }

        // 关闭面板时保存配置
        function closeGroupSwitch() {
            document.getElementById('group-switch-panel').classList.remove('active');
        }
    </script>
</body>
</html>"""

@router.get("/ck_webui/files")
async def list_files(file_type: str = Query("ck", alias="type")):
    # 确保目录路径正确
    target_dir = ck_path if file_type == "ck" else custom_dir
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # 修正文件匹配模式
    pattern = "*.ck" if file_type == "ck" else "*.py"
    files = []
    
    try:
        for f in target_dir.glob(pattern):
            if f.is_file() and validate_filename(f.name, file_type):
                files.append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "mtime": f.stat().st_mtime
                })
        return JSONResponse(sorted(files, key=lambda x: x["mtime"], reverse=True))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/ck_webui/create")
async def create_file(file: str = Query(...), file_type: str = Query("ck", alias="type")):
    target_dir = ck_path if file_type == "ck" else custom_dir
    if not validate_filename(file, file_type):
        return JSONResponse({"status": "error", "msg": "非法文件路径"}, status_code=400)
    
    file_path = target_dir / file
    if file_path.exists():
        return JSONResponse({"status": "error", "msg": "文件已存在"})
    
    file_path.touch()
    return JSONResponse({"status": "success"})

@router.delete("/ck_webui/delete")
async def delete_file(file: str = Query(...), file_type: str = Query("ck", alias="type")):
    target_dir = ck_path if file_type == "ck" else custom_dir
    if not validate_filename(file, file_type):
        return JSONResponse({"status": "error", "msg": "非法文件路径"}, status_code=400)
    
    file_path = target_dir / file
    if not file_path.exists():
        return JSONResponse({"status": "error", "msg": "文件不存在"})
    
    file_path.unlink()
    return JSONResponse({"status": "success"})

@router.get("/ck_webui/load_ck")
async def load_file(file: str = Query(...), file_type: str = Query("ck", alias="type")):
    target_dir = ck_path if file_type == "ck" else custom_dir
    if not validate_filename(file, file_type):
        return Response("", media_type="text/plain")
    
    file_path = target_dir / file
    if not file_path.exists():
        return Response("", media_type="text/plain")
    
    
    return Response(file_path.read_text(encoding="utf-8"), media_type="text/plain")

@router.post("/ck_webui/save_ck")
async def save_file(file: str = Query(...), file_type: str = Query("ck", alias="type"), request: Request = None):
    target_dir = ck_path if file_type == "ck" else custom_dir
    if not validate_filename(file, file_type):
        return JSONResponse({"status": "error", "msg": "非法文件路径"}, status_code=400)
    
    content = (await request.body()).decode("utf-8")
    file_path = target_dir / file
    file_path.write_text(content, encoding="utf-8")
    return JSONResponse({"status": "success"})


@router.websocket("/ck_webui/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    
    async with log_lock:
        log_subscriptions.add(websocket)
    
    try:
        while True:
            try:
                await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30 
                )
            except asyncio.TimeoutError:
                await websocket.send_text("30秒的心跳消息")
    except WebSocketDisconnect:
        #print("客户端主动断开连接")
        pass
    except Exception as e:
        print(f"WebSocket错误: {e}")
    finally:
        async with log_lock:
            if websocket in log_subscriptions:
                log_subscriptions.remove(websocket)
        
        # 添加连接状态检查
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close(code=1000)
            except RuntimeError:
                pass 
        #print("WebSocket连接已安全关闭")

async def push_log(message: str):
    async with log_lock:
        dead_connections = []
        
        # 遍历所有订阅连接
        for ws in log_subscriptions:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(f"{message}")
                else:
                    dead_connections.append(ws)
            except (WebSocketDisconnect, RuntimeError):
                dead_connections.append(ws)
        
        for ws in dead_connections:
            if ws in log_subscriptions:
                log_subscriptions.remove(ws)


def cancel_log_subscriptions():
    async def _cleanup():
        async with log_lock:
            for ws in log_subscriptions.copy():
                if ws.client_state != WebSocketState.DISCONNECTED:
                    try:
                        await ws.close(code=1001)
                    except: 
                        pass
                log_subscriptions.remove(ws)
    
    if log_subscriptions:
        asyncio.get_event_loop().create_task(_cleanup())

@router.get("/ck_webui/groups")
async def get_groups():
    try:
        (bot,) = nonebot.get_bots().values()
        data = await bot.call_api("get_group_list", no_cache=True)
        return JSONResponse(data)
    except Exception as e:
        logger.error(f"获取群列表失败: {e}")
        return JSONResponse({"error": "获取群列表失败"}, status_code=500)
@router.get("/ck_webui/switch-config")
async def get_switch_config():
    (bot,) = nonebot.get_bots().values()
    data = await bot.call_api("get_group_list", no_cache=True)
    config_file = group_list / "group_switches.json"
    default_config = {
                    "global_enabled": True,
                    "groups": [
                        {"group_id": g["group_id"], "enabled": True} 
                        for g in data
                    ]
                }
    config_file.write_text(json.dumps(default_config, ensure_ascii=False, indent=2))
    return JSONResponse(json.loads(config_file.read_text(encoding="utf-8")))

@router.post("/ck_webui/update-switch-config")
async def update_switch_config(request: Request):
    config = await request.json()
    config_file = group_list / "group_switches.json"
    config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2))
    return JSONResponse({"status": "success"})


driver.on_shutdown(cancel_log_subscriptions)

@driver.on_startup
async def _register_router():
    app = get_app()
    if isinstance(app, FastAPI):
        app.include_router(router)
    else:
        logger.warning(f"当前driver_app不是FastAPI，无法实行ck_webui挂载")