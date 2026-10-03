import React, { useState, useEffect } from 'react';
import { TopAppBar } from './components/TopAppBar';
import { ChatThread } from './components/ChatThread';
import { LegalDrawer } from './components/LegalDrawer';
import { IngestModal } from './components/IngestModal';
import type { QueryApiResponse, LegalArticle } from './types/legal';
import { ArrowUp } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content?: string;
  response?: QueryApiResponse;
}

export function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [retrievedArticles, setRetrievedArticles] = useState<LegalArticle[]>([]);
  const [indexedCount, setIndexedCount] = useState<number>(0);
  const [isDark, setIsDark] = useState<boolean>(false);
  const [isIngestModalOpen, setIsIngestModalOpen] = useState<boolean>(false);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [currentContext, setCurrentContext] = useState<Record<string, any>>({});

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
      const res = await fetch('/api/regulations');
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

      if (!res.ok) throw new Error('Query request failed');
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
    } catch (err) {
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        response: {
          is_clarification_mode: false,
          message: 'Gagal terhubung ke backend OWLEXIA. Pastikan server aktif di port 8000.',
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
    <div className="flex flex-col h-screen bg-md-surface text-md-surface-on transition-colors">
      <TopAppBar
        indexedCount={indexedCount}
        isDark={isDark}
        onToggleTheme={toggleTheme}
        onOpenIngestModal={() => setIsIngestModalOpen(true)}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Main Consultation Stream */}
        <section className="flex-1 flex flex-col h-full bg-md-surface">
          <ChatThread
            messages={messages}
            isLoading={isLoading}
            onSelectOption={handleSelectOption}
          />

          {/* Docked Input Box */}
          <div className="p-4 sm:p-5 bg-md-surface-low border-t border-md-outline-variant/60">
            <div className="flex items-end gap-2 bg-md-surface border border-md-outline-variant rounded-2xl p-2 focus-within:border-md-primary focus-within:ring-2 focus-within:ring-md-primary/10 transition-all shadow-sm">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder="Tanyakan persoalan hukum di Indonesia (misal: sanksi pembunuhan, hak tersangka, perlindungan anak)..."
                className="flex-1 bg-transparent border-none outline-none text-xs sm:text-sm text-md-surface-on placeholder:text-md-outline resize-none px-2 py-1 max-h-28"
              />
              <button
                onClick={() => executeQuery(inputText)}
                disabled={!inputText.trim() || isLoading}
                className="w-9 h-9 rounded-full bg-md-primary text-md-primary-on flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-sm disabled:opacity-40 disabled:hover:scale-100 shrink-0"
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[11px] text-center text-md-outline mt-2 font-normal">
              ⚖️ Analisis yuridis normatif berdasarkan peraturan perundang-undangan resmi RI. Bukan pengganti nasihat formal advokat di pengadilan.
            </p>
          </div>
        </section>

        {/* Right: Legal Drawer */}
        <div className="hidden lg:block">
          <LegalDrawer articles={retrievedArticles} />
        </div>
      </div>

      <IngestModal
        isOpen={isIngestModalOpen}
        onClose={() => setIsIngestModalOpen(false)}
        onIngestSuccess={() => fetchRegulationsCount()}
      />
    </div>
  );
}

export default App;
