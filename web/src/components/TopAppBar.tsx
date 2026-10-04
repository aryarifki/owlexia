import React from 'react';
import { Scale, BookOpen, Sun, Moon, Plus } from 'lucide-react';

interface TopAppBarProps {
  indexedCount: number;
  isDark: boolean;
  onToggleTheme: () => void;
  onOpenIngestModal: () => void;
}

export const TopAppBar: React.FC<TopAppBarProps> = ({
  indexedCount,
  isDark,
  onToggleTheme,
  onOpenIngestModal
}) => {
  const formatCountShort = (n: number) => {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return n > 0 ? `${n}` : 'Aktif';
  };

  return (
    <header className="flex items-center justify-between px-3.5 sm:px-6 py-2.5 sm:py-3.5 bg-md-surface-low border-b border-md-outline-variant/60 z-20 transition-colors shrink-0">
      {/* Brand & Identity */}
      <div className="flex items-center gap-2.5 sm:gap-3.5">
        <div className="w-9 h-9 sm:w-11 sm:h-11 rounded-xl sm:rounded-2xl bg-md-primary-container text-md-primary flex items-center justify-center shadow-sm shrink-0">
          <Scale className="w-5 h-5 sm:w-6 sm:h-6" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 sm:gap-2">
            <h1 className="text-base sm:text-lg font-extrabold text-md-surface-on tracking-tight">
              OWLEXIA
            </h1>
            <span className="text-[9px] sm:text-[10px] font-extrabold uppercase px-1.5 sm:px-2 py-0.5 rounded-full bg-md-secondary-container text-md-secondary-on-container tracking-wider">
              Legal AI
            </span>
          </div>
          <p className="hidden sm:block text-[11px] text-md-outline font-medium">
            Penalaran Hukum Positif Berbasis Regulasi Resmi RI
          </p>
        </div>
      </div>

      {/* Action Controls & Badges */}
      <div className="flex items-center gap-1.5 sm:gap-2.5">
        {/* Status Indicator */}
        <div className="hidden md:inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-md-surface-high border border-md-outline-variant/40">
          <span className="w-2 h-2 rounded-full bg-md-success shadow-[0_0_8px_#198754]"></span>
          <span>KUHP 1/2023 & MK 21/2014</span>
        </div>

        {/* Article Count Badge */}
        <div className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 sm:px-3 py-1.5 rounded-full bg-md-primary-container text-md-primary-on-container">
          <BookOpen className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">
            {indexedCount > 0 ? `${indexedCount.toLocaleString('id-ID')} Norma` : 'Basis Data Aktif'}
          </span>
          <span className="sm:hidden font-bold">
            {formatCountShort(indexedCount)} Norma
          </span>
        </div>

        {/* Ingest Button */}
        <button
          onClick={onOpenIngestModal}
          className="inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-full bg-md-surface-high border border-md-outline-variant/60 text-xs font-semibold text-md-surface-on hover:bg-md-surface-highest active:scale-95 transition-all shadow-xs"
          title="Ingest regulasi baru dari peraturan.go.id"
        >
          <Plus className="w-3.5 h-3.5 text-md-primary" />
          <span className="hidden sm:inline">Ingest UU</span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          className="w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center text-md-surface-on hover:bg-md-surface-highest active:scale-90 transition-all"
          title={isDark ? "Ubah ke Mode Terang" : "Ubah ke Mode Gelap"}
          aria-label="Toggle Theme"
        >
          {isDark ? <Sun className="w-4 h-4 text-yellow-400" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
};
