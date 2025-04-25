from fastapi import APIRouter, Response, WebSocket, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from nonebot import get_app
from fastapi import WebSocketDisconnect
from starlette.websockets import WebSocketState
import asyncio
from pathlib import Path
from .parsing_method import ck_path,custom_dir

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
    <style>
         @media screen and (max-width: 768px) {
            body {
                height: auto;
                min-height: 100vh;
            }

            .file-manager {
                width: 100%;
                left: -100%;
                z-index: 1001;
            }

            .toolbar button {
                padding: 8px 10px;
                font-size: 14px;
            }

            .editor-container {
                margin-top: 55px;
            }

            #editor {
                height: 60vh;
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
                top: 55px !important;
                height: calc(100% - 48px); 
            }

            .toolbar {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 999;
                padding: 4px 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }

            .file-header button {
                padding: 8px 12px;
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

        /* 调整工具栏按钮顺序 */
        .toolbar {
            padding: 10px;
            background: #252526;
            border-bottom: 1px solid #3c3c3c;
            display: flex;
            gap: 10px;
        }

        .toolbar button:first-child {
            margin-right: auto;
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
            top: 40px;         
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
        <div class="toolbar">
            <button onclick="toggleSidebar()">☰ 文件</button>
            <button class="mode-switcher active" id="ck-mode" onclick="switchMode('ck')">编辑词库</button>
            <button class="mode-switcher" id="py-mode" onclick="switchMode('py')">编辑拓展</button>
            <button onclick="showPanel('logs')">日志</button>
            <button onclick="saveFile()" style="margin-left: auto">保存</button>
        </div>

        <div id="editor" style="flex: 1; border: 1px solid #3c3c3c;"></div>

        <div id="logs-panel">
            <div class="log-header">实时日志</div>
            <div class="log-content" id="log-content"></div>
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
        let currentMode = 'ck';
        let currentFile = null;
        function toggleSidebar() {
            const sidebar = document.querySelector('.file-manager');
            const backdrop = document.querySelector('.sidebar-backdrop');
            sidebar.classList.toggle('is-active');
            backdrop.style.display = sidebar.classList.contains('is-active') ? 'block' : 'none';
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

        // 修改后的点击外部关闭逻辑
        document.addEventListener('click', function(event) {
            const sidebar = document.querySelector('.file-manager');
            const backdrop = document.querySelector('.sidebar-backdrop');
            const sidebarToggle = document.querySelector('.toolbar button:first-child');

            if (!sidebar.contains(event.target) && 
                event.target !== sidebarToggle &&
                backdrop.style.display === 'block') {
                toggleSidebar();
            }
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
                await fetch(`/ck_webui/save_ck?file=${currentFile}`, {
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

        connectWebSocket();
    </script>
</body>
</html>"""

@router.get("/ck_webui/files")
async def list_files(file_type: str = Query("ck", alias="type")):
    target_dir = ck_path if file_type == "ck" else custom_dir
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
    
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
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close(code=1000)
            except RuntimeError:
                pass 
        #print("WebSocket连接已安全关闭")

async def push_log(message: str):
    async with log_lock:
        dead_connections = []
        
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


driver.on_shutdown(cancel_log_subscriptions)

@driver.on_startup
async def _register_router():
    app = get_app()
    app.include_router(router)