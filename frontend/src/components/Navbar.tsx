import React, { useState, useEffect } from 'react';
import { BookOpen, Sparkles, Layers, History, Sun, Moon } from 'lucide-react';

export type NavTabType = 'create' | 'progress' | 'notes' | 'history';

interface NavbarProps {
  currentTab: NavTabType;
  setCurrentTab: (tab: NavTabType) => void;
  activeJobId: string | null;
  hasActiveJobRunning?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  activeJobId,
  hasActiveJobRunning = false,
}) => {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('playlist_scholar_theme');
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
      localStorage.setItem('playlist_scholar_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('playlist_scholar_theme', 'light');
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode((prev) => !prev);
  };

  return (
    <header className="sticky top-0 left-0 w-full z-50 bg-surface/85 backdrop-blur-md border-b border-outline-variant/20">
      <div className="h-14 max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between gap-4">
        {/* Brand */}
        <div
          className="flex items-center gap-2.5 cursor-pointer group select-none"
          onClick={() => setCurrentTab('create')}
        >
          <div className="w-7 h-7 rounded-xl bg-surface-container flex items-center justify-center text-primary border border-outline-variant/30">
            <BookOpen className="w-4 h-4 text-primary" />
          </div>
          <span className="font-geist text-sm sm:text-base text-on-surface font-semibold tracking-tight">
            Playlist Scholar
          </span>
        </div>

        {/* Clean Segmented Navigation */}
        <nav className="flex items-center p-0.5 bg-surface-container-low rounded-xl border border-outline-variant/30">
          <button
            onClick={() => setCurrentTab('create')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium smooth-transition ${
              currentTab === 'create'
                ? 'bg-surface-container-highest text-on-surface font-semibold shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span>Generate</span>
          </button>

          {activeJobId && (
            <button
              onClick={() => setCurrentTab('progress')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium smooth-transition ${
                currentTab === 'progress'
                  ? 'bg-surface-container-highest text-on-surface font-semibold shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <span>Execution</span>
              {hasActiveJobRunning && (
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
              )}
            </button>
          )}

          {activeJobId && (
            <button
              onClick={() => setCurrentTab('notes')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium smooth-transition ${
                currentTab === 'notes'
                  ? 'bg-surface-container-highest text-on-surface font-semibold shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <Layers className="w-3.5 h-3.5 text-primary" />
              <span>Notes</span>
            </button>
          )}

          <button
            onClick={() => setCurrentTab('history')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium smooth-transition ${
              currentTab === 'history'
                ? 'bg-surface-container-highest text-on-surface font-semibold shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <History className="w-3.5 h-3.5 text-outline" />
            <span>History</span>
          </button>
        </nav>

        {/* Right Controls */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            id="theme-toggle-btn"
            aria-label={isDarkMode ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            title={isDarkMode ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            className="w-8 h-8 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 flex items-center justify-center text-on-surface-variant hover:text-on-surface smooth-transition"
          >
            {isDarkMode ? (
              <Sun className="w-4 h-4 text-tertiary" />
            ) : (
              <Moon className="w-4 h-4 text-primary" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
