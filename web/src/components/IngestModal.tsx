import React, { useState } from 'react';
import { DownloadCloud, X, CheckCircle2, AlertCircle } from 'lucide-react';

interface IngestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIngestSuccess: () => void;
}

export const IngestModal: React.FC<IngestModalProps> = ({ isOpen, onClose, onIngestSuccess }) => {
  const [url, setUrl] = useState('https://peraturan.go.id/id/uu-no-5-tahun-2026');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsLoading(true);
    setResult(null);

    try {
      const res = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ detail_url: url })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setResult({
          success: true,
          message: `Berhasil mengunduh & mengekstrak ${data.articles_extracted} pasal dari ${data.regulation_name} (${data.regulation_number}).`
        });
        onIngestSuccess();
      } else {
        setResult({
          success: false,
          message: data.detail || 'Gagal mengekstrak dokumen peraturan.'
        });
      }
    } catch (err) {
      setResult({
        success: false,
        message: 'Koneksi ke server backend gagal.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-md-surface border border-md-outline-variant/60 rounded-3xl w-full max-w-lg p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-3 border-b border-md-outline-variant/40 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-md-secondary-container text-md-secondary flex items-center justify-center">
              <DownloadCloud className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold text-md-surface-on">
              Ingest Peraturan dari Peraturan.go.id
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-md-outline hover:bg-md-surface-highest transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-md-outline leading-relaxed mb-4">
          Masukkan URL halaman detail peraturan dari portal resmi <code>peraturan.go.id</code>. 
          Sistem akan mengunduh PDF, mengekstrak hierarki Pasal dan Penjelasan, serta mengindeksnya ke dalam basis pengetahuan RAG.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-md-outline mb-1.5">
              URL Halaman Peraturan
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://peraturan.go.id/id/uu-no-5-tahun-2026"
              className="w-full px-3.5 py-2.5 rounded-xl border border-md-outline-variant bg-md-surface-low text-xs text-md-surface-on focus:border-md-primary focus:bg-md-surface outline-none transition-colors"
              required
            />
          </div>

          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-md-primary font-medium py-2">
              <div className="w-4 h-4 border-2 border-md-primary border-t-transparent rounded-full animate-spin"></div>
              <span>Mengunduh berkas PDF, mem-parsing BAB & Pasal, serta mengindeks...</span>
            </div>
          )}

          {result && (
            <div
              className={`p-3 rounded-xl text-xs flex items-start gap-2 ${
                result.success
                  ? 'bg-green-50 dark:bg-green-950/40 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-900'
                  : 'bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-900'
              }`}
            >
              {result.success ? <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" /> : <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />}
              <span>{result.message}</span>
            </div>
          )}

          <div className="flex justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full text-xs font-semibold bg-md-surface-high text-md-surface-on hover:bg-md-surface-highest transition-colors"
            >
              Tutup
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2 rounded-full text-xs font-semibold bg-md-primary text-md-primary-on hover:bg-md-primary/90 transition-all shadow-sm disabled:opacity-50"
            >
              {isLoading ? 'Memproses...' : 'Mulai Ingestion'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
