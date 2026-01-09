/**
 * IPC API 封装 - 用于前端调用 Python 后端
 */

// 发送 GET 请求
export async function get(endpoint) {
    if (!window.electronAPI) {
        console.warn('Not running in Electron environment');
        return { success: false, error: 'Not in Electron' };
    }
    return await window.electronAPI.invoke('GET', endpoint);
}

// 发送 POST 请求
export async function post(endpoint, data) {
    if (!window.electronAPI) {
        console.warn('Not running in Electron environment');
        return { success: false, error: 'Not in Electron' };
    }
    return await window.electronAPI.invoke('POST', endpoint, data);
}

// 检查后端状态
export async function checkHealth() {
    if (!window.electronAPI) {
        return { online: false, error: 'Not in Electron' };
    }
    return await window.electronAPI.checkBackendHealth();
}

// 获取表格数据
export async function getSheetData() {
    return await get('/api/sheet/data');
}

// 保存表格数据
export async function saveSheetData(data) {
    return await post('/api/sheet/data', data);
}
