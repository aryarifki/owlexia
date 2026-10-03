import React from 'react';
import { BookMarked } from 'lucide-react';
import type { LegalArticle } from '../types/legal';

interface LegalDrawerProps {
  articles: LegalArticle[];
}

export const LegalDrawer: React.FC<LegalDrawerProps> = ({ articles }) => {
  return (
    <aside className="w-96 bg-md-surface-low border-l border-md-outline-variant flex flex-col h-full overflow-hidden transition-colors">
      <div className="flex items-center justify-between px-5 py-4 bg-md-surface-container border-b border-md-outline-variant/60">
        <div className="flex items-center gap-2">
          <BookMarked className="w-4 h-4 text-md-primary" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-md-surface-on">
            Inspektur Regulasi Resmi
          </h2>
        </div>
        <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-md-surface-highest text-md-primary">
          {articles.length} Dokumen
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {articles.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center p-6 text-md-outline">
            <span className="text-4xl mb-3 opacity-60">📜</span>
            <p className="text-xs font-bold text-md-surface-on mb-1">Belum ada pasal yang dirujuk</p>
            <p className="text-[11px] leading-relaxed">
              Ketik pertanyaan atau klik skenario uji untuk melihat pasal-pasal resmi yang menjadi rujukan yuridis.
            </p>
          </div>
        ) : (
          articles.map((art) => {
            const isBerlaku = art.status === "BERLAKU";
            const isDiuji = art.status === "DIUJI_MK";
            return (
              <div
                key={art.id}
                className="bg-md-surface border border-md-outline-variant/60 hover:border-md-primary rounded-xl p-3.5 shadow-sm transition-all hover:translate-y-[-2px]"
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <h3 className="text-xs font-bold text-md-surface-on">
                    Pasal {art.article_number}
                  </h3>
                  <span
                    className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                      isBerlaku
                        ? 'bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300'
                        : isDiuji
                        ? 'bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300'
                        : 'bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300'
                    }`}
                  >
                    {art.status}
                  </span>
                </div>

                <p className="text-[11px] text-md-outline mb-2 font-medium">
                  {art.regulation_name} ({art.regulation_number})
                  {art.chapter && ` · ${art.chapter}`}
                </p>

                <div className="text-xs text-md-surface-on bg-md-surface-low p-2.5 rounded-lg border-l-2 border-md-primary leading-relaxed font-normal">
                  {art.content}
                </div>

                {art.explanation && (
                  <div className="mt-2 text-[11px] text-md-outline leading-tight">
                    <strong className="text-md-surface-on">Penjelasan:</strong> {art.explanation}
                  </div>
                )}

                {art.notes && (
                  <div className="mt-2 text-[11px] text-md-secondary leading-tight bg-md-secondary-container/30 p-1.5 rounded">
                    <strong>Catatan Yuridis:</strong> {art.notes}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
