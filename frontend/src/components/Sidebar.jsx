import { Plus, MessageSquare, PanelLeftClose, Bot } from 'lucide-react';

export default function Sidebar({
  conversations,
  activeThreadId,
  onSelectConversation,
  onNewChat,
  isOpen,
  setIsOpen
}) {
  return (
    <>
      {/* Overlay to close sidebar on mobile */}
      <div 
        className={`sidebar-overlay ${isOpen ? 'active' : ''}`} 
        onClick={() => setIsOpen(false)}
      />

      <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="app-title-logo" style={{ cursor: 'pointer' }} onClick={onNewChat}>
            <div style={{
              background: 'linear-gradient(135deg, #7f00ff, #e100ff)',
              borderRadius: '8px',
              padding: '6px',
              display: 'flex',
              alignItems: 'center',
              justify: 'center'
            }}>
              <Bot size={18} color="white" />
            </div>
            <span style={{ fontSize: '16px', fontWeight: 'bold' }}>NexusGPT</span>
          </div>
          <button 
            className="toggle-sidebar-btn" 
            onClick={() => setIsOpen(false)}
            title="Close sidebar"
          >
            <PanelLeftClose size={18} />
          </button>
        </div>

        <div style={{ padding: '0 12px 8px 12px' }}>
          <button className="new-chat-btn" onClick={onNewChat}>
            <Plus size={16} />
            <span>New Chat</span>
          </button>
        </div>

        <div className="sidebar-scroll">
          {conversations.length > 0 && (
            <div className="sidebar-section-title">Conversations</div>
          )}
          
          {conversations.map((conv) => (
            <div
              key={conv.thread_id}
              className={`conversation-item ${activeThreadId === conv.thread_id ? 'active' : ''}`}
              onClick={() => {
                onSelectConversation(conv.thread_id);
                // Close sidebar on small screen after selecting
                if (window.innerWidth <= 768) {
                  setIsOpen(false);
                }
              }}
              title={conv.title || 'Untitled Conversation'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                <MessageSquare size={15} style={{ flexShrink: 0, color: '#8e8e8f' }} />
                <span className="conversation-title">
                  {conv.title || 'Untitled Conversation'}
                </span>
              </div>
            </div>
          ))}

          {conversations.length === 0 && (
            <div style={{ padding: '20px 12px', fontSize: '13px', color: '#666', textAlign: 'center' }}>
              No chat history yet
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-footer-author">
            <Bot size={14} />
            <span>NexusGPT Agentic Assistant</span>
          </div>
          <div>ReactJS + FastAPI + SQLite</div>
        </div>
      </aside>
    </>
  );
}
