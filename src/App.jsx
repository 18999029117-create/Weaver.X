import React, { useState, useEffect, useRef } from 'react';
import { Workbook } from '@fortune-sheet/react';
import '@fortune-sheet/react/dist/index.css';
import './App.css';
import DebugConsole from './components/DebugConsole';
import SheetController from './utils/sheetController';

const API_BASE = 'http://127.0.0.1:8000';

// 简单的图标组件
const Icon = ({ name, size = 16 }) => {
    const icons = {
        sparkles: '✨',
        plus: '+',
        send: '➤',
        file: '📄',
        table: '📊',
        check: '✓',
        zap: '⚡',
        shield: '🛡️',
        chart: '📈',
        layers: '📑',
        maximize: '⤢',
        history: '🕐',
    };
    return <span style={{ fontSize: size }}>{icons[name] || '•'}</span>;
};

function App() {
    const [activeTab, setActiveTab] = useState(null);
    const [tables, setTables] = useState([]);
    const [sheetData, setSheetData] = useState([{
        name: 'Sheet1',
        celldata: [],
        order: 0,
        row: 50,
        column: 26,
        config: {},
    }]);

    const [messages, setMessages] = useState([
        { role: 'assistant', content: '欢迎使用 AI-Sheet Pro！请上传数据文件开始分析。' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [backendStatus, setBackendStatus] = useState('检查中');

    // 🛡️ 安全模式：确认弹框状态
    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [confirmData, setConfirmData] = useState(null);
    const [saveAsName, setSaveAsName] = useState('');

    const messagesEndRef = useRef(null);

    useEffect(() => {
        checkBackend();
        loadTables();
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const checkBackend = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/health`);
            const data = await res.json();
            setBackendStatus(data.status === 'ok' ? 'Local' : '离线');
        } catch {
            setBackendStatus('离线');
        }
    };

    const loadTables = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/tables`);
            const data = await res.json();
            if (data.success) {
                const tableList = Object.entries(data.data).map(([name, info]) => ({
                    name,
                    rows: info.rows,
                    columns: info.columns
                }));
                setTables(tableList);
                if (tableList.length > 0 && !activeTab) {
                    setActiveTab(tableList[0].name);
                    loadTableData(tableList[0].name);
                }
            }
        } catch (e) {
            console.error('加载表失败', e);
        }
    };

    // =============== UI 命令执行器 ===============
    const executeUICommand = (command) => {
        console.log('[UI Command]', command);
        try {
            switch (command.action) {
                case 'setHeaderStyle':
                    return SheetController.setHeaderStyle(command.bold, command.bgColor);
                case 'freezeColumns':
                    return SheetController.freezeColumns(command.count);
                case 'freezeRows':
                    return SheetController.freezeRows(command.count);
                case 'autoFitColumnWidth':
                    return SheetController.autoFitColumnWidth();
                case 'setConditionalFormat':
                    return SheetController.setConditionalFormat(
                        command.column, command.operator, command.value,
                        command.color, command.bgColor
                    );
                case 'setBorder':
                    return SheetController.setBorder(command.type, command.outerStyle, command.innerStyle);
                case 'hideRowsWhere':
                    return SheetController.hideRowsWhere(command.column, command.contains);
                case 'showAllRows':
                    return SheetController.showAllRows();
                case 'sortByColumn':
                    return SheetController.sortByColumn(command.column, command.ascending);
                default:
                    console.warn('未知的 UI 命令:', command.action);
                    return { success: false, error: `未知命令: ${command.action}` };
            }
        } catch (e) {
            console.error('UI 命令执行失败:', e);
            return { success: false, error: e.message };
        }
    };

    // 轮询 UI 命令队列
    useEffect(() => {
        const pollUICommands = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/ui/pending`);
                const data = await res.json();
                if (data.success && data.commands && data.commands.length > 0) {
                    console.log(`[UI Executor] 收到 ${data.commands.length} 条命令`);
                    for (const cmd of data.commands) {
                        const result = executeUICommand(cmd);
                        console.log('[UI Result]', result);
                    }
                }
            } catch (e) {
                // 静默失败，避免控制台刷屏
            }
        };

        const interval = setInterval(pollUICommands, 500); // 每 500ms 检查一次
        return () => clearInterval(interval);
    }, []);
    // =============================================

    // 删除表格
    const handleDeleteTable = async (tableName, e) => {
        e.stopPropagation();
        try {
            const res = await fetch(`${API_BASE}/api/table/${tableName}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                setMessages(prev => [...prev, { role: 'assistant', content: `✓ 已删除表格 "${tableName}"` }]);
                if (activeTab === tableName) {
                    setActiveTab(null);
                    setSheetData([{ name: 'Sheet1', celldata: [], order: 0, row: 50, column: 26, config: {} }]);
                }
                await loadTables(); // 等待列表刷新
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: `✗ 删除失败: ${data.message}` }]);
            }
        } catch (err) {
            console.error('删除失败', err);
            setMessages(prev => [...prev, { role: 'assistant', content: `✗ 删除请求出错: ${err.message}` }]);
        }
    };

    // 🛡️ 安全模式：确认操作处理函数
    const handleConfirmOverwrite = async () => {
        if (!confirmData || !activeTab) return;
        try {
            const res = await fetch(`${API_BASE}/api/table/overwrite`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_table: confirmData.temp_table, target_name: activeTab })
            });
            const data = await res.json();
            if (data.success) {
                setMessages(prev => [...prev, { role: 'assistant', content: `✅ 已覆盖表格 "${activeTab}"` }]);
                setShowConfirmModal(false);
                setConfirmData(null);
                await loadTables();
                loadTableData(activeTab);
            } else {
                alert('覆盖失败: ' + data.message);
            }
        } catch (e) {
            alert('请求失败');
        }
    };

    const handleConfirmSaveAs = async () => {
        if (!confirmData || !saveAsName) return;
        try {
            const res = await fetch(`${API_BASE}/api/table/rename`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_table: confirmData.temp_table, target_name: saveAsName })
            });
            const data = await res.json();
            if (data.success) {
                setMessages(prev => [...prev, { role: 'assistant', content: `✅ 已保存为新表 "${saveAsName}"` }]);
                setShowConfirmModal(false);
                setConfirmData(null);
                await loadTables();
                setActiveTab(saveAsName); // 切换到新表
                loadTableData(saveAsName);
            } else {
                alert('保存失败: ' + data.message);
            }
        } catch (e) {
            alert('请求失败');
        }
    };

    const handleConfirmCancel = async () => {
        if (!confirmData) return;
        // 可以在这里调用后台删除临时表，也可以依赖后台定期清理
        // 简单起见，前端直接关闭，后台留着也没事（下次重启清空）
        // 或者发送 DELETE 请求
        try {
            await fetch(`${API_BASE}/api/table/${confirmData.temp_table}`, { method: 'DELETE' });
        } catch (e) { }

        setMessages(prev => [...prev, { role: 'assistant', content: `🚫 已放弃操作` }]);
        setShowConfirmModal(false);
        setConfirmData(null);
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        setMessages(prev => [...prev, { role: 'assistant', content: '⏳ 正在加载文件...', isLoading: true }]);

        try {
            const res = await fetch(`${API_BASE}/api/upload`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            setMessages(prev => {
                const filtered = prev.filter(m => !m.isLoading);
                if (data.success) {
                    return [...filtered, {
                        role: 'assistant',
                        content: `✓ 已加载 "${data.data.table_name}"，共 ${data.data.rows} 行 ${data.data.columns} 列`
                    }];
                } else {
                    return [...filtered, { role: 'assistant', content: `✗ 上传失败: ${data.message}` }];
                }
            });

            if (data.success) {
                // 刷新表格列表并自动加载刚上传的表格到预览区
                await loadTables();
                loadTableData(data.data.table_name);
            }
        } catch (err) {
            setMessages(prev => {
                const filtered = prev.filter(m => !m.isLoading);
                return [...filtered, { role: 'assistant', content: `✗ 上传错误: ${err.message}` }];
            });
        }
        e.target.value = '';
    };

    const loadTableData = async (tableName) => {
        try {
            // 用户要求显示全部数据，提高限制到 10000 行
            // 注意：FortuneSheet 处理几千行数据性能还是可以的
            const res = await fetch(`${API_BASE}/api/data/view`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ table_name: tableName, offset: 0, limit: 10000 })
            });
            const data = await res.json();

            // 只要成功就显示，哪怕是空表
            if (data.success) {
                const viewData = data.data;
                setActiveTab(tableName);

                const celldata = [];
                const columns = viewData.columns || [];
                const rows = viewData.data || [];

                if (columns.length > 0) {
                    columns.forEach((col, c) => {
                        celldata.push({ r: 0, c, v: { v: col, m: col, ct: { fa: 'General', t: 'g' } } });
                    });

                    rows.forEach((row, r) => {
                        columns.forEach((col, c) => {
                            const val = row[col];
                            if (val !== null && val !== undefined) {
                                celldata.push({ r: r + 1, c, v: { v: val, m: String(val), ct: { fa: 'General', t: 'g' } } });
                            }
                        });
                    });
                }

                setSheetData([{
                    name: tableName,
                    celldata,
                    order: 0,
                    row: Math.max(50, rows.length + 10),
                    column: Math.max(26, columns.length + 5),
                    config: {},
                }]);
            }
        } catch (e) {
            console.error('加载数据失败', e);
        }
    };

    const handleUndo = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/undo`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                setMessages(prev => [...prev, { role: 'assistant', content: `↩️ ${data.message}` }]);
                await loadTables();
                if (activeTab && data.data.includes(activeTab)) {
                    loadTableData(activeTab);
                }
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: `✗ 撤回失败: ${data.message}` }]);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleExport = () => {
        if (!activeTab) return;
        const url = `${API_BASE}/api/export/${activeTab}`;
        window.open(url, '_blank');
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue;
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setInputValue('');
        setIsLoading(true);

        setMessages(prev => [...prev, { role: 'assistant', content: '⏳ AI 正在分析处理...', isLoading: true }]);

        try {
            const res = await fetch(`${API_BASE}/api/ai/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userMessage })
            });
            const data = await res.json();

            setMessages(prev => prev.filter(m => !m.isLoading));

            if (data.success) {
                const responseType = data.data.response_type || 'answer';  // 🆕 获取响应类型
                const answer = data.data.answer || data.data.explanation || '';
                const result = data.data.result;

                let resultText = '';
                let icon = '📊';

                // ========== 根据响应类型分发处理 ==========
                switch (responseType) {
                    case 'clarify':
                        // 追问类：AI 需要更多信息
                        icon = '❓';
                        resultText = answer;
                        break;

                    case 'error':
                        // 错误类
                        icon = '❌';
                        resultText = answer || '操作失败';
                        break;

                    case 'data':
                        // 数据操作类：刷新表格和列表
                        icon = '✅';

                        // 🛡️ 安全模式拦截：如果有临时表，弹出确认框
                        if (data.data.temp_table) {
                            console.log('拦截到临时表:', data.data.temp_table);
                            setConfirmData({
                                temp_table: data.data.temp_table,
                                answer: answer
                            });
                            setSaveAsName(data.data.temp_table.replace('t_ai_temp_', '新表格_'));
                            setShowConfirmModal(true);
                            resultText = answer + ' (等待确认...)';
                        } else {
                            // 旧逻辑 / 无临时表逻辑
                            resultText = answer || '数据操作完成';
                            await loadTables();
                            if (activeTab) {
                                await loadTableData(activeTab);
                            }
                        }
                        break;

                    case 'ui':
                        // UI 命令类：已由后端处理
                        icon = '🎨';
                        resultText = answer || '样式已更新';
                        break;

                    case 'answer':
                    default:
                        // 纯回答类 + 兼容旧逻辑
                        icon = '💡';
                        if (answer) {
                            resultText = answer;
                        } else if (result === null || result === undefined) {
                            resultText = '查询完成';
                        } else if (typeof result === 'object') {
                            if (Array.isArray(result)) {
                                if (result.length === 1 && Object.keys(result[0]).length <= 3) {
                                    const entries = Object.entries(result[0]);
                                    resultText = entries.map(([k, v]) => `${k}: ${v}`).join('\n');
                                } else {
                                    resultText = `查询成功，返回 ${result.length} 条结果`;
                                    renderResult(result);
                                }
                            } else if (result.status === 'success' && result.message) {
                                // 兼容旧格式的修改回执
                                icon = '✅';
                                resultText = result.message;
                                if (activeTab) await loadTableData(activeTab);
                            } else {
                                const entries = Object.entries(result);
                                resultText = entries.map(([k, v]) => {
                                    const valStr = typeof v === 'object' && v !== null ? JSON.stringify(v) : v;
                                    return `${k}: ${valStr}`;
                                }).join('\n');
                            }
                        } else {
                            resultText = String(result);
                        }
                        break;
                }

                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `${icon} ${resultText}`,
                    responseType: responseType  // 保存类型供后续使用
                }]);
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: `✗ ${data.message}` }]);
            }
        } catch (err) {
            setMessages(prev => {
                const filtered = prev.filter(m => !m.isLoading);
                return [...filtered, { role: 'assistant', content: `✗ 请求失败: ${err.message}` }];
            });
        }
        setIsLoading(false);
    };

    const renderResult = (result) => {
        let dataRows = [];
        let columns = [];

        if (Array.isArray(result)) {
            dataRows = result;
            if (dataRows.length > 0) columns = Object.keys(dataRows[0]);
        } else if (result.data && Array.isArray(result.data)) {
            dataRows = result.data;
            columns = result.columns || (dataRows.length > 0 ? Object.keys(dataRows[0]) : []);
        } else if (typeof result === 'object') {
            dataRows = [result];
            columns = Object.keys(result);
        }

        if (columns.length === 0) return;

        const celldata = [];
        columns.forEach((col, c) => {
            celldata.push({ r: 0, c, v: { v: col, m: col, ct: { fa: 'General', t: 'g' } } });
        });
        dataRows.forEach((row, r) => {
            columns.forEach((col, c) => {
                const val = row[col];
                if (val !== null && val !== undefined) {
                    celldata.push({ r: r + 1, c, v: { v: val, m: String(val), ct: { fa: 'General', t: 'g' } } });
                }
            });
        });

        setSheetData([{
            name: 'AI 结果',
            celldata,
            order: 0,
            row: Math.max(50, dataRows.length + 10),
            column: Math.max(26, columns.length + 5),
            config: {},
        }]);
    };

    return (
        <div className="app-root">
            {/* <DebugConsole /> */}
            <div className="bg-blob bg-blob-1"></div>
            <div className="bg-blob bg-blob-2"></div>



            <header className="top-nav">
                <div className="nav-left">
                    <div className="logo">
                        <div className="logo-icon"><Icon name="sparkles" size={18} /></div>
                        <span className="logo-text">AI-Sheet Pro</span>
                    </div>
                    <nav className="nav-tabs">
                        <button className="nav-tab active">工作台</button>
                        <button className="nav-tab">数据流</button>
                        <button className="nav-tab">可视化</button>
                    </nav>
                </div>
                <div className="nav-right">
                    <input type="text" className="search-input" placeholder="寻找数据或指令..." />
                    <div className="user-avatar">U</div>
                </div>
            </header>

            <div className="main-layout">
                <aside className="sidebar">
                    <section className="sidebar-section">
                        <div className="section-header">
                            <h3>数据集</h3>
                            <label className="icon-btn" style={{ cursor: 'pointer' }}>
                                <Icon name="plus" />
                                <input
                                    type="file"
                                    onChange={handleFileUpload}
                                    accept=".xlsx,.xls,.csv"
                                    style={{ display: 'none' }}
                                />
                            </label>
                        </div>
                        <div className="file-list">
                            {tables.length === 0 ? (
                                <div className="empty-hint">点击 + 导入文件</div>
                            ) : tables.map(t => (
                                <div
                                    key={t.name}
                                    className={`file-item ${activeTab === t.name ? 'active' : ''}`}
                                    onClick={() => loadTableData(t.name)}
                                    role="button"
                                    tabIndex={0}
                                    style={{ cursor: 'pointer' }}
                                >
                                    <span className="file-dot"></span>
                                    <span className="file-name">{t.name}</span>
                                    <span className="file-meta">{t.rows}行</span>
                                    <button
                                        className="file-delete"
                                        onClick={(e) => handleDeleteTable(t.name, e)}
                                        title="删除表格"
                                        type="button"
                                    >
                                        ✕
                                    </button>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section className="sidebar-section">
                        <h3>常用分析</h3>
                        <div className="quick-actions">
                            <button className="action-btn">
                                <Icon name="chart" /> 趋势视图
                            </button>
                            <button className="action-btn">
                                <Icon name="layers" /> 多表合并
                            </button>
                        </div>
                    </section>

                    <div className="sidebar-footer">
                        <div className="privacy-badge">
                            <Icon name="shield" size={12} /> 隐私保护中
                        </div>
                        <div className="privacy-bar"><div className="privacy-fill"></div></div>
                    </div>
                </aside>

                <main className="content-area">
                    <div className="preview-panel">
                        <div className="preview-container">
                            <div className="preview-header">
                                <div className="preview-title">
                                    <span className="title-dot"></span>
                                    <span className="title-text">{activeTab || '未选择表格'}</span>
                                    <span className="title-divider"></span>
                                    <span className="title-engine">DuckDB Analytics Engine</span>
                                </div>
                                <div className="preview-controls">
                                    <button className="icon-btn" onClick={handleExport} title="导出 Excel">
                                        <Icon name="file" /> 导出
                                    </button>
                                    <button className="icon-btn"><Icon name="maximize" /></button>
                                </div>
                            </div>
                            <div className="preview-body">
                                {/* 增加时间戳 Key 以强制重新渲染组件，解决数据更新后不显示的问题 */}
                                {/* 增加 Key 强制重绘，使用数据长度作为 Key 的一部分，避免 Date.now() 导致的输入卡顿 */}
                                <Workbook key={activeTab ? `${activeTab}-${sheetData[0]?.celldata?.length || 0}` : 'empty'} data={sheetData} />
                            </div>
                        </div>
                    </div>

                    <div className="chat-panel">
                        <div className="chat-container">
                            <div className="chat-messages">
                                {messages.map((msg, i) => (
                                    <div key={i} className={`message ${msg.role} ${msg.isLoading ? 'loading' : ''}`}>
                                        <div className="message-bubble">
                                            {msg.content}
                                            {msg.role === 'assistant' && msg.content.includes('📊 结果') && (
                                                <div style={{ marginTop: 8, display: 'flex', justifyContent: 'flex-end' }}>
                                                    <button
                                                        onClick={handleUndo}
                                                        style={{
                                                            fontSize: '10px',
                                                            padding: '2px 8px',
                                                            border: '1px solid #cbd5e1',
                                                            borderRadius: '4px',
                                                            background: '#f8fafc',
                                                            cursor: 'pointer'
                                                        }}
                                                    >
                                                        ↩️ 撤回本次操作
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                                <div ref={messagesEndRef} />
                            </div>

                            <div className="chat-input-area">
                                <div className="input-controls">
                                    <label className="icon-btn" style={{ cursor: 'pointer' }}>
                                        <Icon name="plus" />
                                        <input
                                            type="file"
                                            onChange={handleFileUpload}
                                            accept=".xlsx,.xls,.csv"
                                            style={{ display: 'none' }}
                                        />
                                    </label>
                                    <button className="icon-btn">
                                        <Icon name="history" />
                                    </button>
                                </div>

                                <div className="input-wrapper">
                                    <textarea
                                        value={inputValue}
                                        onChange={(e) => setInputValue(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSendMessage())}
                                        placeholder="在此输入 AI 指令..."
                                        disabled={isLoading}
                                    />
                                    <button className="send-btn" onClick={handleSendMessage} disabled={isLoading}>
                                        {isLoading ? <span className="btn-loading"></span> : <Icon name="send" />}
                                    </button>
                                </div>

                                <div className="status-indicator">
                                    <span className={`status-dot ${backendStatus === 'Local' ? 'online' : 'offline'}`}></span>
                                    <span className="status-text">{backendStatus}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

export default App;
