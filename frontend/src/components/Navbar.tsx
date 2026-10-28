import React from 'react';
import { BookOpen, Sparkles, History, Layers } from 'lucide-react';

interface NavbarProps {
  currentTab: 'create' | 'history' | 'notes';
  setCurrentTab: (tab: 'create' | 'history' | 'notes') => void;
  activeJobId: string | null;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, activeJobId }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div 
          className="flex items-center space-x-3 cursor-pointer"
          onClick={() => setCurrentTab('create')}
        >
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <BookOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">Playlist Scholar</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Agentic YouTube-to-Technical-Notes & PDF Platform</p>
          </div>
        </div>

        <nav className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentTab('create')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
              currentTab === 'create'
                ? 'bg-slate-800 text-white border border-slate-700'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Sparkles className="w-4 h-4 text-brand-400" />
            <span>Generate Notes</span>
          </button>

          {activeJobId && (
            <button
              onClick={() => setCurrentTab('notes')}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentTab === 'notes'
                  ? 'bg-slate-800 text-white border border-slate-700'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <Layers className="w-4 h-4 text-teal-400" />
              <span>Current Notes</span>
            </button>
          )}

          <button
            onClick={() => setCurrentTab('history')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
              currentTab === 'history'
                ? 'bg-slate-800 text-white border border-slate-700'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <History className="w-4 h-4 text-slate-400" />
            <span>Job History</span>
          </button>
        </nav>
      </div>
    </header>
  );
};

