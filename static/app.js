/**
 * ADIL AI - Interactive Web Application Logic
 * Material 3 Expressive & Hallmark Anti-Slop Implementation
 */

// Global State
let currentQuery = "";
let currentContext = {};
let isProcessing = false;

// DOM Elements
const chatThread = document.getElementById("chatThread");
const queryForm = document.getElementById("queryForm");
const queryInput = document.getElementById("queryInput");
const submitBtn = document.getElementById("submitBtn");
const drawerBody = document.getElementById("drawerBody");
const drawerItemCount = document.getElementById("drawerItemCount");
const indexedCountLabel = document.getElementById("indexedCountLabel");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const openIngestModalBtn = document.getElementById("openIngestModalBtn");
const closeIngestModalBtn = document.getElementById("closeIngestModalBtn");
const cancelIngestBtn = document.getElementById("cancelIngestBtn");
const startIngestBtn = document.getElementById("startIngestBtn");
const ingestModal = document.getElementById("ingestModal");
const ingestUrlInput = document.getElementById("ingestUrlInput");
const ingestProgress = document.getElementById("ingestProgress");
const ingestResultBanner = document.getElementById("ingestResultBanner");

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  loadRegulationsCount();
  setupEventListeners();
  setupTheme();
});

function setupTheme() {
  const savedTheme = localStorage.getItem("adil_theme") || "light";
  if (savedTheme === "dark") {
    document.body.classList.remove("theme-light");
    document.body.classList.add("theme-dark");
  }
}

function setupEventListeners() {
  // Theme Toggle
  themeToggleBtn.addEventListener("click", () => {
    if (document.body.classList.contains("theme-dark")) {
      document.body.classList.remove("theme-dark");
      document.body.classList.add("theme-light");
      localStorage.setItem("adil_theme", "light");
    } else {
      document.body.classList.remove("theme-light");
      document.body.classList.add("theme-dark");
      localStorage.setItem("adil_theme", "dark");
    }
  });

  // Query Form Submit
  queryForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (query && !isProcessing) {
      handleUserQuery(query);
    }
  });

  // Auto-resize query textarea
  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      queryForm.dispatchEvent(new Event("submit"));
    }
  });

  // Quick Scenario Chips
  document.querySelectorAll(".chip-button[data-query]").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      queryInput.value = q;
      handleUserQuery(q);
    });
  });

  // Ingest Modal Triggers
  if (openIngestModalBtn) {
    openIngestModalBtn.addEventListener("click", () => {
      ingestModal.classList.add("active");
      ingestResultBanner.style.display = "none";
      ingestProgress.classList.remove("active");
    });
  }

  const closeModal = () => ingestModal.classList.remove("active");
  if (closeIngestModalBtn) closeIngestModalBtn.addEventListener("click", closeModal);
  if (cancelIngestBtn) cancelIngestBtn.addEventListener("click", closeModal);

  if (startIngestBtn) {
    startIngestBtn.addEventListener("click", handleLiveIngest);
  }
}

// Fetch total count of indexed legal articles
async function loadRegulationsCount() {
  try {
    const res = await fetch("/api/regulations");
    if (res.ok) {
      const data = await res.json();
      indexedCountLabel.textContent = `${data.total_articles} Norma Pasal Terindeks`;
    }
  } catch (err) {
    indexedCountLabel.textContent = "Basis Regulasi Aktif";
  }
}

// Process User Query
async function handleUserQuery(query, context = {}, forceAssessment = false) {
  isProcessing = true;
  currentQuery = query;
  currentContext = context;
  submitBtn.disabled = true;

  if (!forceAssessment) {
    appendUserMessage(query);
    queryInput.value = "";
  }

  const loadingCard = appendLoadingCard();
  scrollToBottom();

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        case_context: context,
        force_assessment: forceAssessment
      })
    });

    loadingCard.remove();

    if (!res.ok) {
      appendErrorMessage("Terjadi kesalahan saat memproses pertanyaan hukum.");
      return;
    }

    const data = await res.json();

    if (data.is_clarification_mode) {
      appendClarificationCard(data);
    } else if (data.assessment) {
      appendAssessmentCard(data.assessment);
      updateLegalDrawer(data.retrieved_articles);
    }

  } catch (err) {
    loadingCard.remove();
    appendErrorMessage("Gagal terhubung ke server Legal AI Agent.");
  } finally {
    isProcessing = false;
    submitBtn.disabled = false;
    scrollToBottom();
  }
}

// Append User Message
function appendUserMessage(text) {
  const card = document.createElement("div");
  card.className = "message-card user-card";
  card.textContent = text;
  chatThread.appendChild(card);
}

// Append Loading State
function appendLoadingCard() {
  const card = document.createElement("div");
  card.className = "message-card system-card";
  card.innerHTML = `
    <div class="card-header">
      <div class="card-avatar">⚖️</div>
      <div style="display:flex; align-items:center; gap:0.5rem;">
        <span class="loading-spinner"></span>
        <span class="card-title">Menganalisis unsur delik & menelusuri regulasi resmi...</span>
      </div>
    </div>
  `;
  chatThread.appendChild(card);
  return card;
}

// Append Error Message
function appendErrorMessage(msg) {
  const card = document.createElement("div");
  card.className = "message-card system-card";
  card.style.borderColor = "var(--md-sys-color-error)";
  card.innerHTML = `
    <div class="card-header">
      <div class="card-avatar" style="background:#ffdad6; color:#93000a;">⚠️</div>
      <h3 class="card-title" style="color:#ba1a1a;">Pemberitahuan Sistem</h3>
    </div>
    <div class="card-body">${msg}</div>
  `;
  chatThread.appendChild(card);
}

// Append Proactive Clarification Card
function appendClarificationCard(data) {
  const card = document.createElement("div");
  card.className = "message-card system-card";
  
  let questionsHtml = "";
  data.clarification_questions.forEach((q, qIdx) => {
    let optionsHtml = "";
    q.options.forEach((opt, optIdx) => {
      optionsHtml += `
        <button class="option-card-btn" data-qid="${q.id}" data-optidx="${optIdx}">
          <span class="option-label">${opt.label}</span>
          <span class="option-implication">${opt.legal_implication}</span>
        </button>
      `;
    });

    questionsHtml += `
      <div class="question-block">
        <h4 class="question-prompt">${qIdx + 1}. ${q.question}</h4>
        <p class="question-context">${q.context_why_needed}</p>
        <div class="options-grid">${optionsHtml}</div>
      </div>
    `;
  });

  card.innerHTML = `
    <div class="clarification-card">
      <div class="clarification-header">
        <span style="font-size:1.3rem;">🔍</span>
        <h3 class="clarification-title">Mode Kehati-hatian & Klarifikasi Proaktif</h3>
      </div>
      <p class="clarification-intro">${data.message.replace(/\n/g, '<br>')}</p>
      ${questionsHtml}
    </div>
  `;

  chatThread.appendChild(card);

  // Bind click handlers to option buttons
  card.querySelectorAll(".option-card-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const qid = btn.getAttribute("data-qid");
      const optIdx = parseInt(btn.getAttribute("data-optidx"));
      
      // Highlight selection
      btn.parentElement.querySelectorAll(".option-card-btn").forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");

      // Set context
      if (qid === "q_perencanaan") {
        currentContext["direncanakan"] = (optIdx === 0);
      } else if (qid === "q_kejiwaan") {
        currentContext["gangguan_kejiwaan"] = (optIdx === 1);
      } else if (qid === "q_waktu_kejadian") {
        currentContext["rezim_kuhp"] = (optIdx === 0) ? "KUHP_LAMA_WVS" : "KUHP_BARU_UU_1_2023";
      } else if (qid === "q_prosedur_tersangka") {
        currentContext["alat_bukti_cukup"] = (optIdx === 1);
        currentContext["sudah_diperiksa_calon"] = (optIdx === 1);
      }

      // Check if all questions have been answered or trigger assessment
      setTimeout(() => {
        handleUserQuery(currentQuery, currentContext, true);
      }, 300);
    });
  });
}

// Append Full IRAC Assessment Card
function appendAssessmentCard(assessment) {
  const card = document.createElement("div");
  card.className = "message-card system-card";

  // Procedural steps list
  let stepsHtml = "";
  if (assessment.procedural_steps && assessment.procedural_steps.length > 0) {
    const listItems = assessment.procedural_steps.map(s => `
      <li class="procedural-item">
        <span class="procedural-check">✔</span>
        <span>${s}</span>
      </li>
    `).join("");
    stepsHtml = `
      <div class="section-box" style="margin-top:0.75rem;">
        <span class="irac-badge badge-rules">ALUR PROSEDURAL RESMI</span>
        <ul class="procedural-list">${listItems}</ul>
      </div>
    `;
  }

  // Aggravating factors
  let aggHtml = "";
  if (assessment.aggravating_factors && assessment.aggravating_factors.length > 0) {
    const aggItems = assessment.aggravating_factors.map(f => `<li>• ${f}</li>`).join("");
    aggHtml = `
      <div class="section-box" style="margin-top:0.5rem; background:var(--md-sys-color-warning-container); color:#5c3800;">
        <strong>⚠️ Faktor Memberatkan Pidana:</strong>
        <ul style="list-style:none; padding-left:0.5rem; margin-top:0.25rem; font-size:0.85rem;">${aggItems}</ul>
      </div>
    `;
  }

  // Convert markdown to clean html paragraphs
  const appHtml = assessment.application_analysis
    .replace(/### (.*?)\n/g, '<h4 style="margin:0.6rem 0 0.2rem 0; font-size:0.95rem;">$1</h4>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '<br><br>');

  card.innerHTML = `
    <div class="card-header">
      <div class="card-avatar">⚖️</div>
      <div>
        <h3 class="card-title">Kajian Yuridis Formal (Metode IRAC)</h3>
        <span class="card-timestamp">${assessment.case_summary}</span>
      </div>
    </div>
    
    <div class="card-body assessment-container">
      
      <!-- Issue -->
      <div class="section-box">
        <span class="irac-badge badge-issue">ISU HUKUM (ISSUE)</span>
        <p style="font-weight:600; margin-top:0.2rem;">${assessment.issue}</p>
      </div>

      <!-- Application -->
      <div class="section-box">
        <span class="irac-badge badge-app">SUBSUMPSI & PENERAPAN HUKUM (APPLICATION)</span>
        <div style="font-size:0.88rem; line-height:1.6; margin-top:0.35rem;">
          ${appHtml}
        </div>
      </div>

      ${stepsHtml}
      ${aggHtml}

      <!-- Conclusion -->
      <div class="conclusion-box">
        <span class="irac-badge badge-conclusion" style="background:#ffffff; color:#0f5132;">KESIMPULAN YURIDIS (CONCLUSION)</span>
        <p style="margin-top:0.4rem; line-height:1.5;">${assessment.conclusion}</p>
        <p style="font-size:0.75rem; color:var(--md-sys-color-outline); margin-top:0.6rem; font-weight:normal;">
          ⚖️ Disclaimer: ${assessment.legal_disclaimer}
        </p>
      </div>

    </div>
  `;

  chatThread.appendChild(card);
}

// Update Legal Drawer with Retrieved Statutory Articles
function updateLegalDrawer(articles) {
  if (!articles || articles.length === 0) {
    drawerItemCount.textContent = "0 Dokumen";
    drawerBody.innerHTML = `
      <div class="drawer-empty-state">
        <div class="empty-illustration">📜</div>
        <p class="empty-title">Tidak ada pasal terkait</p>
      </div>
    `;
    return;
  }

  drawerItemCount.textContent = `${articles.length} Pasal Terkait`;
  drawerBody.innerHTML = "";

  articles.forEach(art => {
    const card = document.createElement("div");
    card.className = "article-card";

    let badgeClass = "status-badge-berlaku";
    if (art.status === "DIUJI_MK") badgeClass = "status-badge-diuji";
    if (art.status === "DICABUT_SELURUHNYA") badgeClass = "status-badge-dicabut";

    card.innerHTML = `
      <div class="article-header">
        <h4 class="article-title">Pasal ${art.article_number}</h4>
        <span class="article-badge-status ${badgeClass}">${art.status}</span>
      </div>
      <div class="article-meta">
        ${art.regulation_name} (${art.regulation_number})
        ${art.chapter ? `· ${art.chapter}` : ''}
      </div>
      <div class="article-content">${art.content}</div>
      ${art.explanation ? `<div class="article-explanation"><strong>Penjelasan:</strong> ${art.explanation}</div>` : ''}
      ${art.notes ? `<div class="article-explanation" style="color:var(--md-sys-color-secondary);"><strong>Catatan Khusus:</strong> ${art.notes}</div>` : ''}
    `;

    drawerBody.appendChild(card);
  });
}

// Live Ingestion from peraturan.go.id
async function handleLiveIngest() {
  const url = ingestUrlInput.value.trim();
  if (!url) return;

  startIngestBtn.disabled = true;
  ingestProgress.classList.add("active");
  ingestResultBanner.style.display = "none";

  try {
    const res = await fetch("/api/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ detail_url: url })
    });

    const data = await res.json();
    ingestProgress.classList.remove("active");

    if (res.ok && data.success) {
      ingestResultBanner.style.display = "block";
      ingestResultBanner.style.backgroundColor = "var(--md-sys-color-success-container)";
      ingestResultBanner.style.color = "var(--md-sys-color-success)";
      ingestResultBanner.innerHTML = `
        <strong>✔ Berhasil Di-ingest!</strong><br>
        ${data.regulation_name}<br>
        Diekstrak: <strong>${data.articles_extracted} pasal</strong>
      `;
      loadRegulationsCount();
    } else {
      ingestResultBanner.style.display = "block";
      ingestResultBanner.style.backgroundColor = "var(--md-sys-color-error-container)";
      ingestResultBanner.style.color = "var(--md-sys-color-error)";
      ingestResultBanner.textContent = data.detail || "Gagal mengunduh atau memproses peraturan.";
    }
  } catch (err) {
    ingestProgress.classList.remove("active");
    ingestResultBanner.style.display = "block";
    ingestResultBanner.style.backgroundColor = "var(--md-sys-color-error-container)";
    ingestResultBanner.style.color = "var(--md-sys-color-error)";
    ingestResultBanner.textContent = "Koneksi ke endpoint ingestion gagal.";
  } finally {
    startIngestBtn.disabled = false;
  }
}

function scrollToBottom() {
  chatThread.scrollTop = chatThread.scrollHeight;
}
