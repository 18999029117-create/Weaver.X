const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
    // 发起 API 请求到 Python 后端
    invoke: async (method, endpoint, data) => {
        return await ipcRenderer.invoke('api-request', { method, endpoint, data });
    },

    // 检查后端健康状态
    checkBackendHealth: async () => {
        return await ipcRenderer.invoke('check-backend-health');
    },
});
