import React, { useRef, useEffect } from 'react';
import { Paperclip, ArrowUp, X, FileText, Globe, Key, Brain } from 'lucide-react';
import MessageItem from './MessageItem';

const SUGGESTIONS = [
  {
    title: 'Search Web',
    desc: "What's the current price of Bitcoin today?",
    icon: Globe,
    text: "What's the current price of Bitcoin today?",
  },
  {
    title: 'RAG Document Search',
    desc: 'Analyze my uploaded document text',
    icon: FileText,
    text: 'What are the main key points in the uploaded document?',
  },
  {
    title: 'System Memory',
    desc: 'Ask me to remember details about you',
    icon: Brain,
    text: 'Remember that my name is Saurav and I like Python coding.',
  },
  {
    title: 'Calculations & Math',
    desc: 'Perform calculations with math tools',
    icon: Key,
    text: 'Calculate the value of 1493 * 239 plus 8847.',
  },
];

export default function ChatArea({
  messages,
  inputText,
  setInputText,
  onSendMessage,
  isLoading,
  selectedFile,
  setSelectedFile,
  fileUploading,
}) {
  const chatBottomRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Adjust textarea height automatically
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '24px'; // Base min-height
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight - 16, 200)}px`;
    }
  }, [inputText]);

  const handleKeyDown = (e) => {
    // Send on Enter, allow shift-Enter for new line
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputText.trim() || selectedFile) {
      onSendMessage(inputText, selectedFile);
      setInputText('');
      setSelectedFile(null);
      if (textareaRef.current) {
        textareaRef.current.style.height = '24px';
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  return (
    <div className="main-panel">
      {/* Scrollable Message List */}
      <div className="chat-scroll-container">
        {messages.length === 0 ? (
          <div className="welcome-splash">
            <div className="welcome-logo">
              <Brain size={32} />
            </div>
            <h1 className="welcome-title">How can I help you today?</h1>
            <p className="welcome-subtitle">
              Ask NexusGPT a question, upload documents for RAG indexing, search the web, or save preferences to memory.
            </p>
            
            <div className="suggestions-grid">
              {SUGGESTIONS.map((sug, i) => {
                const Icon = sug.icon;
                return (
                  <button
                    key={i}
                    className="suggestion-card"
                    onClick={() => setInputText(sug.text)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <Icon size={14} style={{ color: '#a855f7' }} />
                      <div className="suggestion-card-header">{sug.title}</div>
                    </div>
                    <div className="suggestion-card-desc">{sug.desc}</div>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="chat-inner-container">
            {messages.map((msg) => (
              <MessageItem key={msg.id} message={msg} />
            ))}
            
            {isLoading && (
              <div className="message-row assistant">
                <div className="message-avatar assistant">
                  <Brain size={18} />
                </div>
                <div className="message-wrapper">
                  <div className="typing-indicator" title="NexusGPT is thinking...">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={chatBottomRef} />
          </div>
        )}
      </div>

      {/* Input Form Panel */}
      <div className="chat-input-panel">
        <form onSubmit={handleSubmit} className="chat-input-container">
          <div className="chat-input-wrapper">
            {/* Attached file visual feedback */}
            {selectedFile && (
              <div className="attached-file-badge">
                <FileText size={14} style={{ color: '#a855f7' }} />
                <span className="attached-file-name">{selectedFile.name}</span>
                {fileUploading ? (
                  <span style={{ fontSize: '10px', color: '#8e8e8f' }}>(uploading...)</span>
                ) : (
                  <button
                    type="button"
                    className="attached-file-remove"
                    onClick={() => setSelectedFile(null)}
                    title="Remove file"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            )}

            <div className="chat-input-row">
              {/* File Upload Hidden Input Trigger */}
              <label className="action-btn" title="Upload document for RAG search" style={{ cursor: 'pointer' }}>
                <input
                  type="file"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  accept=".txt,.pdf,.docx"
                  disabled={fileUploading}
                />
                <Paperclip size={18} />
              </label>

              {/* Multiline Textarea Input */}
              <textarea
                ref={textareaRef}
                className="chat-input-textarea"
                placeholder="Message NexusGPT..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={fileUploading}
              />

              <div className="chat-input-actions">
                <button
                  type="submit"
                  className="action-btn send"
                  disabled={(!inputText.trim() && !selectedFile) || fileUploading || isLoading}
                  title="Send message"
                >
                  <ArrowUp size={18} />
                </button>
              </div>
            </div>
          </div>
          
          <div className="disclaimer-text">
            NexusGPT can make mistakes. Verify important info.
          </div>
        </form>
      </div>
    </div>
  );
}
