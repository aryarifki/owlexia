import React from 'react';
import { Scale, BookOpen, Sun, Moon } from 'lucide-react';

interface TopAppBarProps {
  indexedCount: number;
  isDark: boolean;
  onToggleTheme: () => void;
  onOpenIngestModal: () => void;
}

export const TopAppBar: React.FC<TopAppBarProps> = ({ indexedCount, isDark, onToggleTheme, onOpenIngestModal }) => {
  return (
    <header className="flex items-center justify-between px-6 py-3.5 bg-md-surface-low border-b border-md-outline-variant z-10 transition-colors">
      <div className="flex items-center gap-3.5">
        <div className="w-11 h-11 rounded-2xl bg-md-primary-container text-md-primary flex items-center justify-center shadow-sm">
          <Scale className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-md-surface-on tracking-tight">OWLEXIA</h1>
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-md-secondary-container text-md-secondary-on-container tracking-wider">
              Peraturan.go.id
            </span>
          </div>
          <p className="text-xs text-md-outline font-medium">Sistem Intelijen & Penalaran Hukum Proaktif</p>
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        <div className="hidden sm:inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-md-surface-high border border-md-outline-variant/40">
          <span className="w-2 h-2 rounded-full bg-md-success shadow-[0_0_8px_#198754]"></span>
          <span>KUHP Baru (UU 1/2023) Aktif</span>
        </div>

        <div className="inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-md-primary-container text-md-primary-on-container">
          <BookOpen className="w-3.5 h-3.5" />
          <span>{indexedCount > 0 ? `${indexedCount} Norma Terindeks` : 'Basis Data Aktif'}</span>
        </div>

        <button
          onClick={onOpenIngestModal}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-md-surface-high border border-md-outline-variant/60 text-xs font-semibold text-md-surface-on hover:bg-md-surface-highest transition-colors shadow-xs"
          title="Ingest / Crawl UU baru dari peraturan.go.id"
        >
          <span>➕</span>
          <span className="hidden sm:inline">Ingest Regulasi</span>
        </button>

        <button
          onClick={onToggleTheme}
          className="w-9 h-9 rounded-full flex items-center justify-center text-md-surface-on hover:bg-md-surface-highest transition-colors"
          title={isDark ? "Ubah ke Mode Terang" : "Ubah ke Mode Gelap"}
          aria-label="Toggle Theme"
        >
          {isDark ? <Sun className="w-4 h-4 text-yellow-400" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
};
