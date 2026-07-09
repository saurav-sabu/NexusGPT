import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, Bot, User } from 'lucide-react';

function CodeBlock({ language, value }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code: ', err);
    }
  };

  return (
    <div className="code-container">
      <div className="code-header">
        <span className="code-lang">{language || 'code'}</span>
        <button className="code-copy-btn" onClick={handleCopy} title="Copy code snippet">
          {copied ? <Check size={13} /> : <Copy size={13} />}
          <span>{copied ? 'Copied!' : 'Copy code'}</span>
        </button>
      </div>
      <pre className="code-pre">
        <code>{value}</code>
      </pre>
    </div>
  );
}

export default function MessageItem({ message }) {
  const { role, content, created_at } = message;
  const isUser = role === 'user';
  const [msgCopied, setMsgCopied] = useState(false);

  const handleCopyMessage = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setMsgCopied(true);
      setTimeout(() => setMsgCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy message: ', err);
    }
  };

  // Custom components for ReactMarkdown to intercept code blocks
  const markdownComponents = {
    code({ node, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      const isBlock = match || String(children).includes('\n');
      
      if (isBlock) {
        return (
          <CodeBlock
            language={match ? match[1] : 'code'}
            value={String(children).replace(/\n$/, '')}
          />
        );
      }
      
      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="message-avatar assistant" title="NexusGPT Assistant">
          <Bot size={18} />
        </div>
      )}
      
      <div className="message-wrapper">
        <div className="message-content">
          {isUser ? (
            // User messages are plain text with simple layout
            <div style={{ whiteSpace: 'pre-wrap' }}>{content}</div>
          ) : (
            // Assistant messages support full GFM markdown rendering
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]} 
              components={markdownComponents}
            >
              {content}
            </ReactMarkdown>
          )}
        </div>
        
        <div className="message-meta">
          <span>
            {created_at 
              ? new Date(created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
              : 'Just now'
            }
          </span>
          {!isUser && (
            <button 
              className="message-action-btn" 
              onClick={handleCopyMessage}
              title="Copy response text"
            >
              {msgCopied ? <Check size={12} /> : <Copy size={12} />}
            </button>
          )}
        </div>
      </div>

      {isUser && (
        <div className="message-avatar user" title="You">
          <User size={18} />
        </div>
      )}
    </div>
  );
}
