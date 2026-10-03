import React from 'react';
import { Users, Home, AlertCircle, DownloadCloud } from 'lucide-react';

interface QuickScenarioBarProps {
  onSelectQuery: (query: string) => void;
  onOpenIngestModal: () => void;
}

export const QuickScenarioBar: React.FC<QuickScenarioBarProps> = ({ onSelectQuery, onOpenIngestModal }) => {
  const scenarios = [
    {
      id: 'parents',
      query: 'apa hukuman bagi seorang yang membunuh kedua orang tuanya',
      label: 'Pembunuhan Orang Tua (Pemberatan 1/3)',
      icon: Users,
      badge: 'Pidana Berat'
    },
    {
      id: 'family',
      query: 'apakah seseorang yang membunuh satu keluarga bisa didakwakan/ dihukum seumur hidup?',
      label: 'Pembunuhan Satu Keluarga & Seumur Hidup',
      icon: Home,
      badge: 'Concursus'
    },
    {
      id: 'suspect',
      query: 'bagaimana alur polisi atau pengadilan menetapkan status tersangka pada seseorang',
      label: 'Penetapan Tersangka (KUHAP jo MK 21/2014)',
      icon: AlertCircle,
      badge: 'Putusan MK'
    }
  ];

  return (
    <div className="flex items-center gap-3 px-6 py-2.5 bg-md-surface-low border-b border-md-outline-variant overflow-x-auto no-scrollbar">
      <span className="text-[11px] font-bold uppercase tracking-wider text-md-outline whitespace-nowrap">
        Skenario Kasus Uji:
      </span>
      <div className="flex items-center gap-2">
        {scenarios.map(s => {
          const Icon = s.icon;
          return (
            <button
              key={s.id}
              onClick={() => onSelectQuery(s.query)}
              className="inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full border border-md-outline-variant/60 bg-md-surface hover:bg-md-primary-container hover:text-md-primary-on-container hover:border-md-primary transition-all shadow-sm hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
            >
              <Icon className="w-3.5 h-3.5 text-md-secondary" />
              <span>{s.label}</span>
              <span className="text-[10px] bg-md-surface-container px-1.5 py-0.5 rounded-full text-md-outline">
                {s.badge}
              </span>
            </button>
          );
        })}

        <button
          onClick={onOpenIngestModal}
          className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full bg-md-secondary-container text-md-secondary-on-container border border-md-secondary/30 hover:bg-md-secondary hover:text-white transition-all shadow-sm hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
        >
          <DownloadCloud className="w-3.5 h-3.5" />
          <span>Ingest UU Baru</span>
        </button>
      </div>
    </div>
  );
};
