
import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';

const ConsoleContainer = styled.div`
  position: fixed;
  top: 70px;
  right: 20px;
  width: 400px;
  height: 500px;
  background: rgba(30, 30, 30, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  z-index: 9999;
  font-family: 'Consolas', 'Monaco', monospace;
  border: 1px solid #444;
  pointer-events: auto;
`;

const Header = styled.div`
  padding: 10px;
  background: #2d2d2d;
  border-bottom: 1px solid #444;
  color: #ddd;
  font-size: 14px;
  font-weight: bold;
  display: flex;
  justify-content: space-between;
  border-radius: 8px 8px 0 0;
  cursor: grab;
`;

const LogList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  &::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 4px;
  }
`;

const LogEntry = styled.div`
  margin-bottom: 8px;
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
  font-size: 12px;
`;

const MetaLine = styled.div`
  display: flex;
  gap: 8px;
  color: #888;
  margin-bottom: 4px;
`;

const TypeBadge = styled.span`
  color: ${props => {
        switch (props.type) {
            case 'AI_REQ': return '#4caf50';
            case 'AI_RES': return '#2196f3';
            case 'SQL': return '#ff9800';
            case 'ERROR': return '#f44336';
            default: return '#ddd';
        }
    }};
  font-weight: bold;
`;

const Content = styled.div`
  color: #ccc;
  white-space: pre-wrap;
  word-break: break-all;
`;

const DetailView = styled.pre`
  background: #111;
  padding: 8px;
  border-radius: 4px;
  color: #8be9fd;
  font-size: 11px;
  margin-top: 4px;
  overflow-x: auto;
  max-height: 200px;
  display: ${props => props.expanded ? 'block' : 'none'};
`;

const ToggleBtn = styled.button`
  background: none;
  border: none;
  color: #666;
  font-size: 10px;
  cursor: pointer;
  padding: 0;
  margin-top: 4px;
  &:hover { color: #999; }
`;

const API_BASE = 'http://127.0.0.1:8000';

const LogItem = ({ log }) => {
    const [expanded, setExpanded] = useState(false);

    const hasDetails = log.details !== null && log.details !== undefined;

    return (
        <LogEntry>
            <MetaLine>
                <span>{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                <TypeBadge type={log.type}>{log.type}</TypeBadge>
            </MetaLine>
            <Content>{log.content}</Content>
            {hasDetails && (
                <>
                    <ToggleBtn onClick={() => setExpanded(!expanded)}>
                        {expanded ? '▼ Hide Details' : '▶ Show Details'}
                    </ToggleBtn>
                    <DetailView expanded={expanded}>
                        {typeof log.details === 'object'
                            ? JSON.stringify(log.details, null, 2)
                            : String(log.details)
                        }
                    </DetailView>
                </>
            )}
        </LogEntry>
    );
};

const DebugConsole = () => {
    const [logs, setLogs] = useState([]);
    const lastIdRef = useRef(null);
    const listRef = useRef(null);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const url = lastIdRef.current
                    ? `${API_BASE}/api/logs?since_id=${lastIdRef.current}`
                    : `${API_BASE}/api/logs`;

                const res = await fetch(url);
                const json = await res.json();

                if (json.success && json.data.length > 0) {
                    setLogs(prev => {
                        const newLogs = json.data;
                        const combined = [...prev, ...newLogs];
                        return combined.slice(-200);
                    });

                    lastIdRef.current = json.data[json.data.length - 1].id;

                    if (listRef.current) {
                        listRef.current.scrollTop = listRef.current.scrollHeight;
                    }
                }
            } catch (err) {
                console.error("Log poll failed", err);
            }
        };

        const interval = setInterval(fetchLogs, 1000);
        fetchLogs();

        return () => clearInterval(interval);
    }, []);

    return (
        <ConsoleContainer>
            <Header>
                <span>🤖 System Monitor</span>
                <span style={{ fontSize: '10px', opacity: 0.7 }}>Live polling...</span>
            </Header>
            <LogList ref={listRef}>
                {logs.map(log => (
                    <LogItem key={log.id} log={log} />
                ))}
                <div style={{ float: "left", clear: "both" }} />
            </LogList>
        </ConsoleContainer>
    );
};

export default DebugConsole;
