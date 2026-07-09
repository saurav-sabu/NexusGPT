import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ModelSelector from './components/ModelSelector';
import ChatArea from './components/ChatArea';
import { 
  getConversations, 
  getHistory, 
  sendMessage, 
  uploadFile 
} from './utils/api';
import { Menu, Bot } from 'lucide-react';

// Client-side simple UUID generator (RFC4122 compliant)
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [activeThreadId, setActiveThreadId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash');
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // File Upload State
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileUploading, setFileUploading] = useState(false);

  // Layout State
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);

  // Initialize and load conversations
  useEffect(() => {
    loadConversations();

    // Auto toggle sidebar based on screen size changes
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setSidebarOpen(true);
      } else {
        setSidebarOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadConversations = async () => {
    try {
      const data = await getConversations();
      // Sort conversations so that the newest updated are at the top
      const sorted = data.sort((a, b) => {
        return new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at);
      });
      setConversations(sorted);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const handleSelectConversation = async (threadId) => {
    setActiveThreadId(threadId);
    setIsLoading(true);
    setMessages([]);
    setSelectedFile(null);
    try {
      const history = await getHistory(threadId);
      setMessages(history);
    } catch (err) {
      console.error('Failed to load history:', err);
      // Add error message to local view
      setMessages([
        {
          id: 'error-' + Date.now(),
          role: 'assistant',
          content: '⚠️ Failed to load chat history. Please verify the backend service status.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setActiveThreadId(null);
    setMessages([]);
    setSelectedFile(null);
    setInputText('');
    if (window.innerWidth <= 768) {
      setSidebarOpen(false);
    }
  };

  const handleSendMessage = async (text, file) => {
    const threadIdToUse = activeThreadId || generateUUID();
    const promptText = text.trim();

    // Local user message object
    const userMsg = {
      id: generateUUID(),
      role: 'user',
      content: promptText || (file ? `Uploaded document: ${file.name}` : ''),
      created_at: new Date().toISOString(),
    };

    // Update messages local array immediately to keep UI highly responsive
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // 1. Upload File if selected
      if (file) {
        setFileUploading(true);
        try {
          await uploadFile(file, threadIdToUse);
          
          // Inject a temporary local confirmation message that document was processed
          setMessages((prev) => [
            ...prev,
            {
              id: 'sys-' + Date.now(),
              role: 'assistant',
              content: `📎 *Document "${file.name}" uploaded successfully!* It has been parsed and indexed. You can now ask questions about its content.`,
              created_at: new Date().toISOString(),
            },
          ]);
        } catch (uploadErr) {
          setMessages((prev) => [
            ...prev,
            {
              id: 'err-' + Date.now(),
              role: 'assistant',
              content: `❌ *Upload failed for "${file.name}":* ${uploadErr.message}.`,
              created_at: new Date().toISOString(),
            },
          ]);
          setIsLoading(false);
          setFileUploading(false);
          return;
        }
        setFileUploading(false);
      }

      // If user only uploaded a file without asking a question, stop here
      if (!promptText && file) {
        setIsLoading(false);
        setActiveThreadId(threadIdToUse);
        await loadConversations();
        return;
      }

      // Set thread ID in case it was a new chat
      setActiveThreadId(threadIdToUse);

      // 2. Send Message to Agent
      const result = await sendMessage(promptText, threadIdToUse, selectedModel);

      // Appending final chatbot response
      const assistantMsg = {
        id: generateUUID(),
        role: 'assistant',
        content: result.response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Refresh sidebar list
      await loadConversations();
    } catch (err) {
      console.error('Failed to send message:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: 'err-' + Date.now(),
          role: 'assistant',
          content: `⚠️ *Connection Error:* Could not communicate with the NexusGPT agent backend.\n\nDetail: ${err.message}`,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Drawer */}
      <Sidebar
        conversations={conversations}
        activeThreadId={activeThreadId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
      />

      {/* Main Content Workspace */}
      <div className="main-panel">
        <header className="header-bar">
          <div className="header-left">
            {!sidebarOpen && (
              <button 
                className="toggle-sidebar-btn" 
                onClick={() => setSidebarOpen(true)}
                title="Open sidebar"
              >
                <Menu size={18} />
              </button>
            )}
            {sidebarOpen && window.innerWidth <= 768 && <div style={{ width: '34px' }} />}
            
            {/* Short header title for active chat */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bot size={18} style={{ color: '#a855f7' }} />
              <span style={{ fontWeight: '500', fontSize: '15px' }}>NexusGPT Workspace</span>
            </div>
          </div>

          <ModelSelector
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
          />
        </header>

        {/* Messaging Area */}
        <ChatArea
          messages={messages}
          inputText={inputText}
          setInputText={setInputText}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
          fileUploading={fileUploading}
        />
      </div>
    </div>
  );
}
