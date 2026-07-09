import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, Sparkles, Cpu, Zap } from 'lucide-react';

const MODELS = [
  {
    id: 'gemini-2.5-flash',
    name: 'Gemini 2.5 Flash',
    desc: 'Fast, balanced, and general-purpose intelligence',
    icon: Sparkles,
  },
  {
    id: 'gemini-2.5-pro',
    name: 'Gemini 2.5 Pro',
    desc: 'Deep reasoning, coding, and complex analysis',
    icon: Cpu,
  },
  {
    id: 'gemini-2.5-flash-lite',
    name: 'Gemini 2.5 Flash Lite',
    desc: 'Ultra-fast responses for lightweight tasks',
    icon: Zap,
  },
  {
    id: 'gemini-1.5-flash',
    name: 'Gemini 1.5 Flash',
    desc: 'Standard performance from previous generation',
    icon: Sparkles,
  },
  {
    id: 'gemini-1.5-pro',
    name: 'Gemini 1.5 Pro',
    desc: 'High capability from previous generation',
    icon: Cpu,
  },
];

export default function ModelSelector({ selectedModel, onSelectModel }) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const activeModel = MODELS.find((m) => m.id === selectedModel) || MODELS[0];
  const ActiveIcon = activeModel.icon;

  return (
    <div className="model-selector-container" ref={containerRef}>
      <button 
        className="model-dropdown-trigger" 
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <ActiveIcon size={16} style={{ color: activeModel.id.includes('pro') ? '#c084fc' : '#60a5fa' }} />
        <span>{activeModel.name}</span>
        <ChevronDown size={14} />
      </button>

      {isOpen && (
        <div className="model-dropdown-menu">
          {MODELS.map((model) => {
            const ModelIcon = model.icon;
            const isActive = model.id === selectedModel;
            return (
              <div
                key={model.id}
                className={`model-option ${isActive ? 'active' : ''}`}
                onClick={() => {
                  onSelectModel(model.id);
                  setIsOpen(false);
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ModelIcon size={14} style={{ color: model.id.includes('pro') ? '#c084fc' : '#60a5fa' }} />
                  <span className="model-option-name">{model.name}</span>
                </div>
                <span className="model-option-desc">{model.desc}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
