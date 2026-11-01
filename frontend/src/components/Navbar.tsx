import React, { useState, useEffect } from 'react';
import {
  Sun,
  Moon,
  Sparkles,
  Layers,
  History,
  FileText,
  Search,
  PlusCircle
} from 'lucide-react';

export type AppModule = 'research' | 'youtube';
export type YouTubeNavTab = 'create' | 'progress' | 'notes' | 'history';
export type ResearchNavTab = 'landing' | 'progress' | 'results' | 'history';

interface NavbarProps {
  currentModule: AppModule;
  setCurrentModule: (mod: AppModule) => void;
  // YouTube module navigation
  ytTab: YouTubeNavTab;
  setYtTab: (tab: YouTubeNavTab) => void;
  activeYtJobId: string | null;
  hasActiveYtRunning?: boolean;
  // Research module navigation
  researchTab: ResearchNavTab;
  setResearchTab: (tab: ResearchNavTab) => void;
  activeResearchJobId: string | null;
  hasActiveResearchRunning?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentModule,
  setCurrentModule,
  ytTab,
  setYtTab,
  activeYtJobId,
  hasActiveYtRunning = false,
  researchTab,
  setResearchTab,
  activeResearchJobId,
  hasActiveResearchRunning = false,
}) => {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('synthara_theme') || localStorage.getItem('playlist_scholar_theme');
      if (savedTheme) {
        return savedTheme === 'dark';
      }
      return document.documentElement.classList.contains('dark');
    }
    return true;
  });

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('synthara_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('synthara_theme', 'light');
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode((prev) => !prev);
  };

  return (
    <header className="sticky top-0 left-0 w-full z-50 bg-surface/90 backdrop-blur-md border-b border-outline-variant/30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        {/* Main Header Bar */}
        <div className="h-16 flex items-center justify-between gap-4">
          {/* Brand — Synthara */}
          <div
            className="flex items-center gap-3 cursor-pointer group select-none shrink-0"
            onClick={() => {
              if (currentModule === 'youtube') setYtTab('create');
              else setResearchTab('landing');
            }}
          >
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20 group-hover:bg-primary/15 smooth-transition">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 22 12 12 22 2 12" />
                <circle cx="12" cy="12" r="2.5" fill="currentColor" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="font-geist text-xl sm:text-[22px] text-on-surface font-semibold tracking-tight leading-none">
                Synthara
              </span>
              <span className="text-[11px] text-on-surface-variant/80 font-sans tracking-normal hidden md:block">
                Research &amp; Learning Workspace
              </span>
            </div>
          </div>

          {/* Primary Module Selector */}
          <div className="flex items-center p-1 bg-surface-container rounded-xl border border-outline-variant/30">
            <button
              onClick={() => setCurrentModule('research')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium smooth-transition ${
                currentModule === 'research'
                  ? 'bg-surface text-on-surface shadow-xs font-semibold'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <span>Research</span>
              {hasActiveResearchRunning && (
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping" />
              )}
            </button>

            <button
              onClick={() => setCurrentModule('youtube')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium smooth-transition ${
                currentModule === 'youtube'
                  ? 'bg-surface text-on-surface shadow-xs font-semibold'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <span>YouTube Notes</span>
              {hasActiveYtRunning && (
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping" />
              )}
            </button>
          </div>

          {/* Right Controls: Theme Toggle */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={toggleTheme}
              id="theme-toggle-btn"
              aria-label={isDarkMode ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
              title={isDarkMode ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
              className="w-9 h-9 rounded-xl bg-surface-container hover:bg-surface-high border border-outline-variant/30 flex items-center justify-center text-on-surface-variant hover:text-on-surface smooth-transition"
            >
              {isDarkMode ? (
                <Sun className="w-4 h-4 text-secondary" />
              ) : (
                <Moon className="w-4 h-4 text-primary" />
              )}
            </button>
          </div>
        </div>

        {/* Sub-Navigation Bar for active module */}
        <div className="h-10 flex items-center justify-between border-t border-outline-variant/20 text-xs">
          {currentModule === 'youtube' ? (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setYtTab('create')}
                className={`px-3 py-1 rounded-md font-medium smooth-transition flex items-center gap-1.5 ${
                  ytTab === 'create'
                    ? 'text-primary font-semibold bg-primary/10'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <span>Notes Generator</span>
              </button>

              {activeYtJobId && (
                <button
                  onClick={() => setYtTab('progress')}
                  className={`px-3 py-1 rounded-md font-medium smooth-transition flex items-center gap-1.5 ${
                    ytTab === 'progress'
                      ? 'text-primary font-semibold bg-primary/10'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <span>Active Pipeline</span>
                  {hasActiveYtRunning && (
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                  )}
                </button>
              )}

              {activeYtJobId && (
                <button
                  onClick={() => setYtTab('notes')}
                  className={`px-3 py-1 rounded-md font-medium smooth-transition flex items-center gap-1.5 ${
                    ytTab === 'notes'
                      ? 'text-primary font-semibold bg-primary/10'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <span>Study Notes</span>
                </button>
              )}

              <button
                onClick={() => setYtTab('history')}
                className={`px-3 py-1 rounded-md font-medium smooth-transition flex items-center gap-1.5 ${
                  ytTab === 'history'
                    ? 'text-primary font-semibold bg-primary/10'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <span>History</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setResearchTab('landing')}
                className={`px-3 py-1 rounded-md font-medium smooth-transition flex items-center gap-1.5 ${
                  researchTab === 'landing'
                    ? 'text-primary font-semibold bg-primary/10'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <span>New Research</span>
              </button>

              {activeResearchJobId && (
                <button
                  onClick={() => setResearchTab('progress')}
                  className={`px-3 py-1 rounded-md font-medium smooth-transition flex items-center gap-1.5 ${
                    researchTab === 'progress'
                      ? 'text-primary font-semibold bg-primary/10'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <span>Progress</span>
                  {hasActiveResearchRunning && (
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                  )}
                </button>
              )}

              {activeResearchJobId && (
                <button
                  onClick={() => setResearchTab('results')}
                  className={`px-3 py-1 rounded-md font-medium smooth-transition flex items-center gap-1.5 ${
                    researchTab === 'results'
                      ? 'text-primary font-semibold bg-primary/10'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <span>Article</span>
                </button>
              )}

              <button
                onClick={() => setResearchTab('history')}
                className={`px-3 py-1 rounded-md font-medium smooth-transition flex items-center gap-1.5 ${
                  researchTab === 'history'
                    ? 'text-primary font-semibold bg-primary/10'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <span>Archive</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
