const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

let mainWindow;
let pythonProcess;

const PYTHON_SERVER_URL = 'http://127.0.0.1:8000';

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            webSecurity: false,  // 禁用 web 安全限制以支持本地文件加载
        },
        title: 'AI-Sheet-Pro',
        backgroundColor: '#FAFAFC',
    });

    // 加载打包文件
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));

    // 打开开发者工具调试
    // mainWindow.webContents.openDevTools();
}

// 启动 Python 后端服务
function startPythonServer() {
    const serverPath = path.join(__dirname, 'server');
    const venvPython = path.join(serverPath, 'venv', 'Scripts', 'python.exe');

    pythonProcess = spawn(venvPython, ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000'], {
        cwd: serverPath,
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`[Python] ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`[Python Error] ${data}`);
    });
}

// IPC 处理
ipcMain.handle('api-request', async (event, { method, endpoint, data }) => {
    try {
        const url = `${PYTHON_SERVER_URL}${endpoint}`;
        const response = await axios({
            method: method || 'GET',
            url,
            data,
            headers: { 'Content-Type': 'application/json' },
        });
        return { success: true, data: response.data };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

ipcMain.handle('check-backend-health', async () => {
    try {
        const response = await axios.get(`${PYTHON_SERVER_URL}/api/health`);
        return { online: true, data: response.data };
    } catch (error) {
        return { online: false, error: error.message };
    }
});

app.whenReady().then(() => {
    // 先启动 Python 后端服务
    startPythonServer();

    // 等待后端启动后再创建窗口
    setTimeout(() => {
        createWindow();
    }, 2000); // 给后端 2 秒启动时间

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
