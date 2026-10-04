import React, { useState, useEffect, useRef } from 'react';
import { TopAppBar } from './components/TopAppBar';
import { ChatThread } from './components/ChatThread';
import { LegalDrawer } from './components/LegalDrawer';
import { IngestModal } from './components/IngestModal';
import type { QueryApiResponse, LegalArticle } from './types/legal';
import { ArrowUp, BookOpen, X } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content?: string;
  response?: QueryApiResponse;
}

const QUICK_CHIPS = [
  {
    id: 'parents',
    query: 'apa hukuman bagi seorang yang membunuh kedua orang tuanya',
    label: 'Pembunuhan Orang Tua',
    icon: '⚖️'
  },
  {
    id: 'family',
    query: 'apakah seseorang yang membunuh satu keluarga bisa didakwakan/ dihukum seumur hidup?',
    label: 'Pembunuhan Satu Keluarga',
    icon: '🏠'
  },
  {
    id: 'suspect',
    query: 'bagaimana alur polisi atau pengadilan menetapkan status tersangka pada seseorang',
    label: 'Alur Penetapan Tersangka',
    icon: '🏛️'
  },
  {
    id: 'dkj',
    query: 'Bagaimana kedudukan dan fungsi Daerah Khusus Jakarta berdasarkan UU No. 2 Tahun 2024?',
    label: 'UU DKJ Jakarta 2/2024',
    icon: '🏙️'
  }
];

export function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [retrievedArticles, setRetrievedArticles] = useState<LegalArticle[]>([]);
  const [indexedCount, setIndexedCount] = useState<number>(0);
  const [isDark, setIsDark] = useState<boolean>(false);
  const [isIngestModalOpen, setIsIngestModalOpen] = useState<boolean>(false);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState<boolean>(false);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [currentContext, setCurrentContext] = useState<Record<string, any>>({});

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem('owlexia-theme') || localStorage.getItem('adil-theme') || 'light';
    const isDarkMode = savedTheme === 'dark';
    setIsDark(isDarkMode);
    document.documentElement.setAttribute('data-theme', savedTheme);
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    fetchRegulationsCount();
  }, []);

  // Auto-resize textarea as user types
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 130)}px`;
    }
  }, [inputText]);

  const toggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    const themeStr = nextDark ? 'dark' : 'light';
    localStorage.setItem('owlexia-theme', themeStr);
    document.documentElement.setAttribute('data-theme', themeStr);
    if (nextDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const fetchRegulationsCount = async () => {
    try {
      const res = await fetch('/api/regulations?limit=1');
      if (res.ok) {
        const data = await res.json();
        setIndexedCount(data.total_articles);
      }
    } catch (e) {
      // Backend may be starting
    }
  };

  const executeQuery = async (queryText: string, context: Record<string, any> = {}, forceAssessment = false) => {
    if (!queryText.trim() || isLoading) return;

    setIsLoading(true);
    setCurrentQuery(queryText);
    setCurrentContext(context);

    if (!forceAssessment) {
      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: queryText
      };
      setMessages((prev) => [...prev, userMsg]);
      setInputText('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          case_context: context,
          force_assessment: forceAssessment
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || `Server merespons dengan status ${res.status}`);
      }
      const data: QueryApiResponse = await res.json();

      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        response: data
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (data.retrieved_articles && data.retrieved_articles.length > 0) {
        setRetrievedArticles(data.retrieved_articles);
      }
    } catch (err: any) {
      const isNetworkErr = !err?.message || err.message === 'Failed to fetch' || err.message.includes('NetworkError');
      const errorText = isNetworkErr
        ? 'Gagal terhubung ke backend OWLEXIA. Server sedang dimulai ulang atau tidak dapat dijangkau di port 8000. Silakan tunggu beberapa detik dan coba kembali.'
        : `Gagal memproses pertanyaan: ${err.message}`;

      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        response: {
          is_clarification_mode: false,
          message: errorText,
          completeness_score: 0,
          missing_elements: [],
          clarification_questions: [],
          assessment: null,
          retrieved_articles: []
        }
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectOption = (qid: string, optIdx: number) => {
    const updated = { ...currentContext };
    if (qid === 'q_perencanaan') {
      updated['direncanakan'] = optIdx === 0;
    } else if (qid === 'q_kejiwaan') {
      updated['gangguan_kejiwaan'] = optIdx === 1;
    } else if (qid === 'q_waktu_kejadian') {
      updated['rezim_kuhp'] = optIdx === 0 ? 'KUHP_LAMA_WVS' : 'KUHP_BARU_UU_1_2023';
    } else if (qid === 'q_prosedur_tersangka') {
      updated['alat_bukti_cukup'] = optIdx === 1;
      updated['sudah_diperiksa_calon'] = optIdx === 1;
    }

    executeQuery(currentQuery, updated, true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      executeQuery(inputText);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-md-surface text-md-surface-on transition-colors overflow-hidden">
      {/* Top App Bar */}
      <TopAppBar
        indexedCount={indexedCount}
        isDark={isDark}
        onToggleTheme={toggleTheme}
        onOpenIngestModal={() => setIsIngestModalOpen(true)}
      />

      <div className="flex-1 flex overflow-hidden relative">
        {/* Main Consultation Stream */}
        <section className="flex-1 flex flex-col h-full bg-md-surface relative overflow-hidden">
          {/* Mobile Reference Badge button when articles exist */}
          {retrievedArticles.length > 0 && (
            <div className="lg:hidden absolute top-2 right-3 z-10">
              <button
                onClick={() => setIsMobileDrawerOpen(true)}
                className="inline-flex items-center gap-1.5 text-[11px] font-bold px-3 py-1.5 rounded-full bg-md-primary-container text-md-primary-on-container shadow-md border border-md-primary/20 hover:scale-105 active:scale-95 transition-all"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>{retrievedArticles.length} Norma Rujukan</span>
              </button>
            </div>
          )}

          {/* Chat Messages Thread */}
          <ChatThread
            messages={messages}
            isLoading={isLoading}
            onSelectOption={handleSelectOption}
          />

          {/* Floating Expressive Chat Island (Melayang di atas konten) */}
          <div className="absolute bottom-2.5 sm:bottom-5 left-0 right-0 px-3 sm:px-6 pointer-events-none z-30 flex flex-col items-center">
            <div className="w-full max-w-3xl pointer-events-auto flex flex-col items-center">
              
              {/* Quick Topic Chips (Bisa digeser horizontal) */}
              <div className="w-full flex items-center gap-1.5 overflow-x-auto no-scrollbar mb-2 px-1 py-0.5 justify-start sm:justify-center">
                {QUICK_CHIPS.map((chip) => (
                  <button
                    key={chip.id}
                    onClick={() => executeQuery(chip.query)}
                    className="inline-flex items-center gap-1.5 text-[11px] sm:text-xs font-semibold px-3 py-1.5 rounded-full bg-md-surface-container/90 dark:bg-md-surface-container-high/90 backdrop-blur-md border border-md-outline-variant/60 text-md-surface-on hover:border-md-primary hover:bg-md-primary-container/40 transition-all shadow-sm active:scale-95 shrink-0"
                  >
                    <span>{chip.icon}</span>
                    <span>{chip.label}</span>
                  </button>
                ))}
              </div>

              {/* Floating Pill Input Box */}
              <div className="w-full bg-md-surface-container/90 dark:bg-md-surface-container-high/95 backdrop-blur-2xl border border-md-outline-variant/60 rounded-[30px] sm:rounded-full p-2 sm:p-2.5 shadow-xl shadow-black/8 dark:shadow-black/35 focus-within:border-md-primary/70 focus-within:ring-4 focus-within:ring-md-primary/10 transition-all duration-300">
                <div className="flex items-end gap-2 px-1.5">
                  <textarea
                    ref={textareaRef}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    placeholder="Tanyakan persoalan hukum di Indonesia..."
                    className="flex-1 bg-transparent border-none outline-none text-base sm:text-sm text-md-surface-on placeholder:text-md-outline resize-none px-2 py-2 leading-relaxed min-h-[44px] max-h-32"
                  />
                  <button
                    onClick={() => executeQuery(inputText)}
                    disabled={!inputText.trim() || isLoading}
                    className="w-11 h-11 rounded-full bg-md-primary text-md-primary-on flex items-center justify-center hover:scale-105 active:scale-90 transition-all shadow-md shadow-md-primary/25 disabled:opacity-40 disabled:hover:scale-100 disabled:shadow-none shrink-0 mb-0.5"
                    aria-label="Kirim Pertanyaan"
                  >
                    <ArrowUp className="w-5 h-5 stroke-[2.5]" />
                  </button>
                </div>
              </div>

              {/* Legal Disclaimer */}
              <p className="text-[10px] sm:text-[11px] text-center text-md-outline/80 mt-1.5 px-4 font-normal">
                ⚖️ Analisis yuridis normatif berdasarkan peraturan perundang-undangan resmi RI.
              </p>
            </div>
          </div>
        </section>

        {/* Desktop Legal Drawer */}
        <div className="hidden lg:block">
          <LegalDrawer articles={retrievedArticles} />
        </div>

        {/* Mobile Modal Drawer (Bottom Sheet on Mobile) */}
        {isMobileDrawerOpen && (
          <div className="lg:hidden fixed inset-0 z-50 flex flex-col justify-end bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
            <div className="bg-md-surface-container rounded-t-3xl max-h-[85vh] flex flex-col shadow-2xl border-t border-md-outline-variant/60 animate-in slide-in-from-bottom duration-300">
              <div className="flex items-center justify-between p-4 border-b border-md-outline-variant/50">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-md-primary" />
                  <h3 className="text-sm font-bold text-md-surface-on">
                    Pasal & Regulasi Terkait ({retrievedArticles.length})
                  </h3>
                </div>
                <button
                  onClick={() => setIsMobileDrawerOpen(false)}
                  className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-md-surface-high text-md-surface-on"
                  aria-label="Tutup"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4">
                <LegalDrawer articles={retrievedArticles} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Ingestion Modal */}
      <IngestModal
        isOpen={isIngestModalOpen}
        onClose={() => setIsIngestModalOpen(false)}
        onIngestSuccess={() => fetchRegulationsCount()}
      />
    </div>
  );
}

export default App;
