import {
  A2UIClient,
  A2UIRenderer,
  type TimelineItem,
  themeStyleSheet,
} from '@googlemaps/a2ui/lit';
import {useEffect, useRef, useState} from 'react';
import './App.css';

const H3_RESOLUTIONS = [
  { res: 0, label: 'Res 0 - 4,250,547 km2' },
  { res: 1, label: 'Res 1 - 607,221 km2' },
  { res: 2, label: 'Res 2 - 86,746 km2' },
  { res: 3, label: 'Res 3 - 12,392 km2' },
  { res: 4, label: 'Res 4 - 1,770 km2' },
  { res: 5, label: 'Res 5 - 253 km2' },
  { res: 6, label: 'Res 6 - 36.1 km2' },
  { res: 7, label: 'Res 7 - 5.16 km2' },
  { res: 8, label: 'Res 8 - 0.737 km2' },
  { res: 9, label: 'Res 9 - 0.105 km2' },
  { res: 10, label: 'Res 10 - 0.015 km2' },
  { res: 11, label: 'Res 11 - 0.0021 km2' },
  { res: 12, label: 'Res 12 - 0.00031 km2' },
  { res: 13, label: 'Res 13 - 0.000044 km2' },
  { res: 14, label: 'Res 14 - 0.0000063 km2' },
  { res: 15, label: 'Res 15 - 0.0000009 km2' },
];

/**
 * Main Application component that demonstrates A2UI integration in a React environment.
 * It manages a chat interface with a timeline of text messages and A2UI interactive surfaces.
 */
function App() {
  // --- UI State ---
  // const [isChatOpen, setIsChatOpen] = useState(true);
  // Disabled setIsChatOpen because the close button was commented out for Chrome Extension compatibility,
  // preventing TS6133 'declared but never read' error during production build.
  const [isChatOpen] = useState(true);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [input, setInput] = useState('');
  const [isRequesting, setIsRequesting] = useState(false);
  const [importJson, setImportJson] = useState('');
  const importDialogRef = useRef<HTMLDialogElement>(null);
  const [lastResponseJson, setLastResponseJson] = useState('');
  // Agent mode state disabled - uses standard backend default agent
  // const [agentMode, setAgentMode] = useState<'default' | 'grounding' | 'template'>('default');
  const [h3Resolution, setH3Resolution] = useState<number>(9);

  // --- A2UI Integration Refs ---
  // A2UIClient handles communication with the A2A agent
  // Difference from original: Defaults to local FastAPI backend endpoint http://localhost:8000/a2a/app
  // (original default was http://localhost:10002)
  const serverUrl =
    import.meta.env.VITE_A2A_SERVER_URL ||
    (import.meta as any).env.SERVER_URL ||
    "http://localhost:8000/a2a/app";
  const clientRef = useRef(new A2UIClient(serverUrl));
  // A2UIRenderer manages the local state of A2UI surfaces and message processing
  const rendererRef = useRef(new A2UIRenderer());

  // Handle scrolling properly.
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
  };
  useEffect(() => {
    scrollToBottom();
  }, [timeline]);

  useEffect(() => {
    if (!document.adoptedStyleSheets.includes(themeStyleSheet)) {
      document.adoptedStyleSheets = [
        ...document.adoptedStyleSheets,
        themeStyleSheet,
      ];
    }
  }, []);

  const handleImport = () => {
    try {
      const messages = JSON.parse(importJson);
      rendererRef.current = new A2UIRenderer();
      rendererRef.current.processResponse(
        messages.map((msg: any) => ({type: 'a2ui', message: msg})),
      );
      setTimeline([...rendererRef.current.timeline]);
      importDialogRef.current?.close();
      setImportJson('');
    } catch (e) {
      alert('Failed to parse JSON: ' + e);
    }
  };

  /**
   * Handles sending a text message from the user.
   * Updates the UI timeline and processes the agent's response.
   */
  const handleSend = async () => {
    if (!input.trim() || isRequesting) return;

    const messageText = input.trim();
    setInput('');
    setIsRequesting(true);

    // 1. Add the user's message to the local renderer's timeline
    rendererRef.current.addUserMessage(messageText);
    setTimeline([...rendererRef.current.timeline]);

    // 2. Prepend resolution prefix (agent routing prefixes disabled)
    // if (agentMode === 'grounding') {
    //   payload = `[GROUNDING][RES:${h3Resolution}] ${messageText}`;
    // } else if (agentMode === 'template') {
    //   payload = `[TEMPLATE][RES:${h3Resolution}] ${messageText}`;
    // } else {
    //   payload = `[RES:${h3Resolution}] ${messageText}`;
    // }
    const payload = `[RES:${h3Resolution}] ${messageText}`;

    try {
      // 3. Send the message to the A2A agent via A2UIClient
      const response = await clientRef.current.send(payload);

      // 4. Process the response (which may contain text and/or A2UI data)
      rendererRef.current.processResponse(response);

      // Update last response JSON
      const uiMessages = response
        .filter((p: any) => p.type === 'a2ui')
        .map((p: any) => p.message);
      if (uiMessages.length > 0) {
        setLastResponseJson(JSON.stringify(uiMessages, null, 2));
      }

      // 5. Synchronize the React state with the renderer's updated timeline
      setTimeline([...rendererRef.current.timeline]);
    } catch (error) {
      console.error('Failed to send message:', error);
      rendererRef.current.processResponse([
        {
          type: 'text',
          text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      ]);
      setTimeline([...rendererRef.current.timeline]);
    } finally {
      setIsRequesting(false);
    }
  };

  return (
    <div className="app-container">
      {/* --- Main Content Panel --- */}
      {/* Difference from original:
          Replaced placeholder `<h1>Main content</h1>` with a full-screen Google Maps Embed iframe
          (defaults to Shinjuku, Tokyo, Japan). To revert to original placeholder, replace with:
          <main className="main-panel">
            {!isChatOpen && (<button className="toggle-chat-btn" onClick={() => setIsChatOpen(true)}>Open Chat</button>)}
            <div className="main-panel-content"><h1>Main content</h1></div>
          </main>
      */}
      {/* --- Main Content Panel ---
      <main className="main-panel">
        {!isChatOpen && (
          <button className="toggle-chat-btn" onClick={() => setIsChatOpen(true)}>
            Open Chat
          </button>
        )}
        <div className="main-panel-content">
          <h1>Main content</h1>
        </div>
      </main>
      */}

      {/* --- Side Chat Panel --- */}
      <aside className={`chat-panel ${isChatOpen ? 'open' : 'closed'}`}>
        <div className="chat-header">
    {/* Difference from original: Changed header title from "Chat" to "GeoAgent" */}
          <h2>GeoAgent</h2>

          {/* Hidden close button to prevent closing the chat layout inside the Chrome side panel
          <button
            className="close-chat-btn"
            onClick={() => setIsChatOpen(false)}>
            ×
          </button>
          */}
        </div>

        {/* --- Message Timeline --- */}
        <div className="chat-messages">
          <maui-providers>
            {timeline.length === 0 && (
              <p style={{opacity: 0.5, textAlign: 'center', marginTop: '50px'}}>
                No messages yet.
              </p>
            )}
            {timeline.map((item, idx) => {
              if (item.type === 'user') {
                return (
                  <div key={idx} className="user-message">
                    {item.text}
                  </div>
                );
              } else if (item.type === 'action') {
                return (
                  <div key={idx} className="action-message">
                    <strong>A2UI Action: {item.action}</strong>
                    <pre>{item.text}</pre>
                  </div>
                );
              } else if (item.type === 'text') {
                return (
                  <div key={idx} className="bot-message">
                    {item.text}
                  </div>
                );
              } else if (item.type === 'surface') {
                // Render an A2UI Surface containing multiple UI components
                const surface = rendererRef.current.getSurface(item.surfaceId);
                if (!surface) return null;
                return (
                  <div key={item.surfaceId} className="surface-message">
                    {/* @ts-ignore */}
                    <a2ui-surface
                      surface={surface}
                    ></a2ui-surface>
                  </div>
                );
              }
              return null;
            })}
            {isRequesting && <div className="loading-spinner">Thinking...</div>}
            <div ref={messagesEndRef} />
          </maui-providers>
        </div>

        {/* --- Chat Input Area --- */}
        <div className="chat-input-area">
          <textarea
            className="chat-textarea"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={isRequesting}></textarea>
          <div className="chat-actions">
            <div className="agent-selector-wrapper">
              {/* Agent mode selector disabled
              <select
                className="agent-mode-select"
                value={agentMode}
                onChange={(e) => setAgentMode(e.target.value as any)}
                disabled={isRequesting}
                aria-label="Select Agent Mode">
                <option value="default">Default Agent</option>
                <option value="grounding">Grounding Agent</option>
                <option value="template">Template Agent</option>
              </select>
              */}
              <select
                className="resolution-select"
                value={h3Resolution}
                onChange={(e) => setH3Resolution(Number(e.target.value))}
                disabled={isRequesting}
                aria-label="Select H3 Resolution">
                {H3_RESOLUTIONS.map(({ res, label }) => (
                  <option key={res} value={res}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="chat-actions-right">
              {lastResponseJson && <ResponseViewer json={lastResponseJson} />}
              <button
                className="import-btn-input"
                onClick={() => importDialogRef.current?.showModal()}>
                Import JSON
              </button>
              <button
                className="send-button"
                onClick={handleSend}
                disabled={isRequesting || !input.trim()}>
                {isRequesting ? '...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      </aside>

      <dialog
        ref={importDialogRef}
        onClick={(e) => {
          if (e.target === importDialogRef.current)
            importDialogRef.current.close();
        }}
        style={{
          border: 'none',
          borderRadius: '16px',
          padding: '0',
          width: '90%',
          maxWidth: '600px',
        }}>
        <div
          className="dialog-content"
          style={{
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            color: 'var(--text-h)',
            padding: '24px',
            borderRadius: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}>
          <h2 style={{margin: 0, fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-h)'}}>
            Import A2UI JSON
          </h2>
          <textarea
            placeholder='[ { "surfaceUpdate": { ... } }, ... ]'
            value={importJson}
            onChange={(e) => setImportJson(e.target.value)}
            style={{
              width: '100%',
              minHeight: '200px',
              fontFamily: 'monospace',
              boxSizing: 'border-box',
              padding: '12px',
              background: 'var(--code-bg)',
              color: 'var(--text-h)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
            }}></textarea>
          <div
            className="dialog-footer"
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '12px',
              marginTop: '12px',
            }}>
            <button
              className="dialog-btn-secondary"
              onClick={() => importDialogRef.current?.close()}>
              Cancel
            </button>
            <button
              className="dialog-btn-primary"
              onClick={handleImport}>
              Render A2UI
            </button>
          </div>
        </div>
      </dialog>
    </div>
  );
}

function ResponseViewer({json}: {json: string}) {
  const [copied, setCopied] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(json);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <button
        className="view-response-btn"
        onClick={() => dialogRef.current?.showModal()}>
        View Last Response
      </button>

      <dialog
        ref={dialogRef}
        onClick={(e) => {
          if (e.target === dialogRef.current) dialogRef.current.close();
        }}
        style={{
          border: 'none',
          borderRadius: '16px',
          padding: '0',
          width: '90%',
          maxWidth: '600px',
        }}>
        <div
          className="dialog-content"
          style={{
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            color: 'var(--text-h)',
            padding: '24px',
            borderRadius: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}>
          <h2 style={{margin: 0, fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-h)'}}>
            Last A2UI Response
          </h2>
          <pre
            style={{
              background: 'var(--code-bg)',
              color: 'var(--text-h)',
              border: '1px solid var(--border)',
              padding: '12px',
              borderRadius: '8px',
              overflowX: 'auto',
              maxHeight: '300px',
              whiteSpace: 'pre-wrap',
            }}>
            {json || 'No response yet.'}
          </pre>
          <div
            className="dialog-footer"
            style={{display: 'flex', justifyContent: 'flex-end', gap: '12px'}}>
            <button
              className="dialog-btn-secondary"
              onClick={() => dialogRef.current?.close()}>
              Close
            </button>
            <button
              className="dialog-btn-primary"
              onClick={handleCopy}
              style={{
                background: copied ? '#137333' : undefined,
                borderColor: copied ? '#137333' : undefined,
              }}>
              {copied ? 'Copied!' : 'Copy JSON'}
            </button>
          </div>
        </div>
      </dialog>
    </>
  );
}

export default App;
