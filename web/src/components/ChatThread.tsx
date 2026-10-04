import React from 'react';
import { HelpCircle, CheckCircle2, AlertTriangle, ArrowRight, Scale } from 'lucide-react';
import type { QueryApiResponse } from '../types/legal';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content?: string;
  response?: QueryApiResponse;
}

interface ChatThreadProps {
  messages: Message[];
  isLoading: boolean;
  onSelectOption: (qid: string, optIdx: number) => void;
}

export const ChatThread: React.FC<ChatThreadProps> = ({ messages, isLoading, onSelectOption }) => {
  const bottomRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-4 sm:py-6 pb-36 sm:pb-44 flex flex-col gap-4 sm:gap-6 scroll-smooth">
      {/* Welcome Card if no messages yet */}
      {messages.length === 0 && (
        <div className="bg-md-surface-container border border-md-outline-variant/50 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-md-primary-container text-md-primary flex items-center justify-center font-bold">
              ⚖️
            </div>
            <div>
              <h2 className="text-base font-bold text-md-surface-on">Ruang Konsultasi Hukum Proaktif</h2>
              <p className="text-xs text-md-outline">Resmi · Berbasis Regulasi Positif Republik Indonesia</p>
            </div>
          </div>
          <p className="text-sm text-md-surface-on leading-relaxed mb-4">
            Selamat datang di <strong>OWLEXIA</strong>. Sistem ini mengadopsi prinsip <strong>kehati-hatian hukum</strong>: kami mendalami fakta secara cermat dan tidak serta-merta mengambil keputusan definitif jika kronologi peristiwa belum lengkap.
          </p>
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-md-surface-high text-md-primary">✔ Dualisme KUHP WvS & UU 1/2023</span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-md-surface-high text-md-primary">✔ Sinergi Putusan MK 21/2014</span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-md-surface-high text-md-primary">✔ Analisis IRAC (Unsur Delik)</span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-md-surface-high text-md-primary">✔ Integrasi Langsung Peraturan.go.id</span>
          </div>
          <p className="text-xs text-md-outline font-medium">
            Ketik pertanyaan atau uraian kasus hukum Anda di bawah ini secara bebas dan terperinci.
          </p>
        </div>
      )}

      {/* Message Stream */}
      {messages.map((msg) => {
        if (msg.role === 'user') {
          return (
            <div key={msg.id} className="self-end max-w-[85%] bg-md-primary text-md-primary-on px-5 py-3.5 rounded-expressive-user shadow-md text-sm font-medium leading-relaxed">
              {msg.content}
            </div>
          );
        }

        const data = msg.response;
        if (!data) return null;

        // If in Clarification Mode
        if (data.is_clarification_mode) {
          return (
            <div key={msg.id} className="self-start max-w-[95%] w-full bg-md-surface-low border border-yellow-500/40 rounded-expressive-ai p-5 shadow-sm">
              <div className="flex items-center gap-2 text-yellow-700 dark:text-yellow-400 font-bold mb-2">
                <HelpCircle className="w-5 h-5" />
                <h3 className="text-sm tracking-wide uppercase font-extrabold">Mode Kehati-hatian & Klarifikasi Proaktif</h3>
              </div>
              <p className="text-xs text-md-surface-on mb-4 leading-relaxed font-normal whitespace-pre-line bg-yellow-50/70 dark:bg-yellow-950/20 p-3 rounded-xl border border-yellow-200/50 dark:border-yellow-900/30">
                {data.message}
              </p>

              <div className="space-y-4">
                {data.clarification_questions.map((q, qIdx) => (
                  <div key={q.id} className="bg-md-surface border border-md-outline-variant/60 rounded-xl p-4 shadow-sm">
                    <h4 className="text-sm font-bold text-md-surface-on mb-1">
                      {qIdx + 1}. {q.question}
                    </h4>
                    <p className="text-xs text-md-outline mb-3 leading-normal">
                      {q.context_why_needed}
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {q.options.map((opt, optIdx) => (
                        <button
                          key={optIdx}
                          onClick={() => onSelectOption(q.id, optIdx)}
                          className="flex flex-col text-left p-3 rounded-lg border border-md-outline-variant hover:border-md-primary hover:bg-md-primary-container/40 transition-all hover:scale-[1.01] active:scale-[0.99] group cursor-pointer"
                        >
                          <span className="text-xs font-bold text-md-surface-on group-hover:text-md-primary flex items-center justify-between mb-1">
                            {opt.label}
                            <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </span>
                          <span className="text-[11px] text-md-outline leading-tight">
                            {opt.legal_implication}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        }

        // If Assessment is Ready
        if (data.assessment) {
          const assess = data.assessment;
          return (
            <div key={msg.id} className="self-start max-w-[95%] w-full bg-md-surface-low border border-md-outline-variant/50 rounded-expressive-ai p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-3 border-b border-md-outline-variant/40 pb-3">
                <div className="w-9 h-9 rounded-full bg-md-primary-container text-md-primary flex items-center justify-center font-bold">
                  ⚖️
                </div>
                <div>
                  <h3 className="text-sm font-bold text-md-surface-on">Kajian Yuridis Formal (Metode IRAC)</h3>
                  <span className="text-xs text-md-outline">{assess.case_summary}</span>
                </div>
              </div>

              {/* Issue */}
              <div className="bg-md-surface border border-md-outline-variant/40 rounded-xl p-3.5">
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-md-secondary-container text-md-secondary-on-container">
                  Isu Hukum (Issue)
                </span>
                <p className="text-sm font-semibold text-md-surface-on mt-1.5 leading-snug">
                  {assess.issue}
                </p>
              </div>

              {/* Application / Subsumpsi */}
              <div className="bg-md-surface border border-md-outline-variant/40 rounded-xl p-4">
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-md-primary-container text-md-primary-on-container">
                  Subsumpsi & Penerapan Hukum (Application)
                </span>
                <div className="text-xs text-md-surface-on mt-2.5 space-y-2 leading-relaxed whitespace-pre-line font-normal">
                  {assess.application_analysis}
                </div>
              </div>

              {/* Procedural Steps if available */}
              {assess.procedural_steps && assess.procedural_steps.length > 0 && (() => {
                const isSuspectCase = 
                  assess.procedural_steps.some(step => /tersangka|praperadilan|sprindik|penyidikan|terlapor/i.test(step)) ||
                  /tersangka|praperadilan/i.test(assess.issue || '') ||
                  /tersangka|praperadilan/i.test(assess.case_summary || '');
                const proceduralTitle = isSuspectCase 
                  ? "Alur Prosedural Penetapan Tersangka yang Sah" 
                  : "Tahapan & Alur Prosedural Hukum";

                return (
                  <div className="bg-md-surface border border-md-outline-variant/40 rounded-xl p-4">
                    <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-md-primary-container text-md-primary-on-container">
                      {proceduralTitle}
                    </span>
                    <ul className="mt-2.5 space-y-1.5">
                      {assess.procedural_steps.map((step, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs bg-md-surface-low p-2 rounded-lg text-md-surface-on">
                          <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })()}

              {/* Aggravating factors if available */}
              {assess.aggravating_factors && assess.aggravating_factors.length > 0 && (
                <div className="bg-red-50/70 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40 rounded-xl p-3.5 text-red-900 dark:text-red-200">
                  <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-red-200 dark:bg-red-900 text-red-800 dark:text-red-100">
                    Faktor Memberatkan Pidana
                  </span>
                  <ul className="mt-2 space-y-1 text-xs">
                    {assess.aggravating_factors.map((f, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-red-600 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Conclusion */}
              <div className="bg-md-primary-container border-2 border-md-primary rounded-xl p-4.5 text-md-primary-on-container shadow-sm">
                <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-white dark:bg-md-surface text-md-primary tracking-wider">
                  Kesimpulan Yuridis (Conclusion)
                </span>
                <p className="text-sm font-bold mt-2 leading-relaxed">
                  {assess.conclusion}
                </p>
                <p className="text-[11px] text-md-outline mt-3 pt-2 border-t border-md-primary/20 font-normal">
                  ⚖️ {assess.legal_disclaimer}
                </p>
              </div>

            </div>
          );
        }

        // Conversational / Informational / Database Overview Message
        if (data.message) {
          return (
            <div key={msg.id} className="self-start max-w-[95%] w-full bg-md-surface-low border border-md-outline-variant/50 rounded-expressive-ai p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-3 border-b border-md-outline-variant/40 pb-3">
                <div className="w-9 h-9 rounded-full bg-md-primary-container text-md-primary flex items-center justify-center font-bold">
                  <Scale className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-md-surface-on">OWLEXIA Intelligence</h3>
                  <span className="text-xs text-md-outline">Informasi Regulasi & Basis Data Hukum</span>
                </div>
              </div>

              <div className="text-xs sm:text-sm text-md-surface-on leading-relaxed whitespace-pre-line font-normal">
                {data.message}
              </div>
            </div>
          );
        }

        return null;
      })}

      {/* Loading Card */}
      {isLoading && (
        <div className="self-start max-w-[85%] bg-md-surface-low border border-md-outline-variant/40 rounded-expressive-ai p-4 flex items-center gap-3 shadow-sm">
          <div className="w-4 h-4 border-2 border-md-primary border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs font-medium text-md-surface-on">
            Menganalisis unsur delik & menelusuri regulasi resmi peraturan.go.id...
          </span>
        </div>
      )}

      {/* Auto-scroll anchor */}
      <div ref={bottomRef} className="h-4 shrink-0" />
    </div>
  );
};
