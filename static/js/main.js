/* ============================================================
   SentimentAI – main.js
   Handles: tab switching, text/file analysis, results rendering,
   history sidebar, toast notifications, donut chart, gauge.
   ============================================================ */

'use strict';

// ── Translations (injected by Jinja2 in index.html) ──────────
const T = (() => {
  try { return JSON.parse(window.APP_T || '{}'); } catch { return {}; }
})();
const UI_LANG = window.APP_LANG || 'fr';

// ── Sentiment config ──────────────────────────────────────────
const SENTIMENT_CONFIG = {
  positif:  { emoji: '😊', label: T.sentiment_pos || 'Positif',  cls: 'badge-pos', color: '#34d399' },
  negatif:  { emoji: '😞', label: T.sentiment_neg || 'Négatif',  cls: 'badge-neg', color: '#fb7185' },
  neutre:   { emoji: '😐', label: T.sentiment_neu || 'Neutre',   cls: 'badge-neu', color: '#22d3ee' },
};

// ── DOM refs ──────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// Tabs
const tabBtns   = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-panel');

// Text tab
const textInput    = $('text-input');
const charCount    = $('char-count');
const modelSelect  = $('model-select');
const langSelect   = $('lang-select');
const analyzeBtn   = $('analyze-btn');
const analyzeBtnTx = $('analyze-btn-text');
const clearBtn     = $('clear-btn');
const exampleBtns  = document.querySelectorAll('.example-btn');

// File tab
const fileInput       = $('file-input');
const dropZone        = $('drop-zone');
const dropLabel       = $('drop-label');
const analyzeFileBtn  = $('analyze-file-btn');
const fileModelSelect = $('file-model-select');
const fileLangSelect  = $('file-lang-select');

// Results
const resultsPanel    = $('results-panel');
const sentimentBadge  = $('sentiment-badge');
const sentimentEmoji  = $('sentiment-emoji');
const sentimentLabel  = $('sentiment-label');
const resultModelBadge= $('result-model-badge');
const scorePosEl      = $('score-pos');
const scoreNeuEl      = $('score-neu');
const scoreNegEl      = $('score-neg');
const scoreCompound   = $('score-compound');
const compoundNeedle  = $('compound-needle');
const donutCenterVal  = $('donut-center-val');
const sentenceSection = $('sentence-analysis');
const mostPosText     = $('most-pos-text');
const mostNegText     = $('most-neg-text');
const mostPosScore    = $('most-pos-score');
const mostNegScore    = $('most-neg-score');
const wordcloudSection= $('wordcloud-section');
const wordcloudImg    = $('wordcloud-img');

// Sidebar
const statTotal       = $('stat-total');
const statPos         = $('stat-pos');
const statNeu         = $('stat-neu');
const statNeg         = $('stat-neg');
const historyList     = $('history-list');
const clearHistoryBtn = $('clear-history-btn');

// Toast
const toast = $('toast');

// ── Chart.js donut ────────────────────────────────────────────
let donutChart = null;

function buildDonut() {
  const ctx = document.getElementById('donut-chart');
  if (!ctx) return;
  donutChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Positif', 'Neutre', 'Négatif'],
      datasets: [{
        data: [0, 1, 0],
        backgroundColor: ['#34d399', '#22d3ee', '#fb7185'],
        borderColor: '#1e293b',
        borderWidth: 3,
        hoverOffset: 4,
      }],
    },
    options: {
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      animation: { duration: 600, easing: 'easeOutQuart' },
    },
  });
}

function updateDonut(pos, neu, neg, compound) {
  if (!donutChart) return;
  donutChart.data.datasets[0].data = [pos, neu, neg];
  donutChart.update();
  if (donutCenterVal) donutCenterVal.textContent = compound >= 0 ? `+${compound}` : `${compound}`;
}

// ── Tab switching ─────────────────────────────────────────────
tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    tabBtns.forEach(b => {
      b.classList.toggle('bg-navy-700', b === btn);
      b.classList.toggle('text-white', b === btn);
      b.classList.toggle('text-slate-400', b !== btn);
    });
    tabPanels.forEach(p => p.classList.toggle('hidden', p.id !== `tab-${target}`));
  });
});

// ── Character count ───────────────────────────────────────────
textInput?.addEventListener('input', () => {
  if (charCount) charCount.textContent = textInput.value.length;
  // Auto-detect language after 40 chars
  if (textInput.value.length > 40) detectLangDebounced();
});

// ── Example texts ─────────────────────────────────────────────
exampleBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    if (textInput) {
      textInput.value = btn.dataset.text;
      if (charCount) charCount.textContent = textInput.value.length;
    }
  });
});

// ── Clear ─────────────────────────────────────────────────────
clearBtn?.addEventListener('click', () => {
  if (textInput) { textInput.value = ''; if (charCount) charCount.textContent = 0; }
  resultsPanel?.classList.add('hidden');
});

// ── Language auto-detect ──────────────────────────────────────
let _langTimer = null;
function detectLangDebounced() {
  clearTimeout(_langTimer);
  _langTimer = setTimeout(async () => {
    const text = textInput?.value?.trim();
    if (!text || text.length < 40) return;
    try {
      const res = await fetch('/api/detect-lang', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (data.lang && langSelect && data.supported) {
        langSelect.value = data.lang;
      }
    } catch { /* silent */ }
  }, 700);
}

// ── Text analysis ─────────────────────────────────────────────
analyzeBtn?.addEventListener('click', () => runTextAnalysis());

async function runTextAnalysis() {
  const text = textInput?.value?.trim();
  if (!text) { showToast(T.toast_no_text || 'Veuillez entrer du texte.', 'warn'); return; }

  setAnalyzeBtnLoading(true);
  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        lang: langSelect?.value || 'fr',
        model: modelSelect?.value || 'vader',
        wordcloud: true,
      }),
    });
    const data = await res.json();
    if (data.error) {
      if (data.error === "transformers_disabled_on_free_plan") {
        showToast("⚠️ Transformers est désactivé sur Render Free (RAM insuffisante). Utilisez VADER.", "warn");
        return;
      }
      showToast(T.toast_error || 'Erreur.', 'error');
      return;
    }
    renderResults(data);
    loadHistory();
  } catch (e) {
    showToast(T.toast_error || 'Erreur.', 'error');
  } finally {
    setAnalyzeBtnLoading(false);
  }
}

function setAnalyzeBtnLoading(loading) {
  if (!analyzeBtn) return;
  analyzeBtn.disabled = loading;
  if (analyzeBtnTx) {
    analyzeBtnTx.textContent = loading
      ? (T.toast_analyzing || 'Analyse…')
      : (T.analyze_btn || 'Analyser');
  }
}

// ── File analysis ─────────────────────────────────────────────
let selectedFile = null;

fileInput?.addEventListener('change', e => {
  selectedFile = e.target.files[0] || null;
  if (dropLabel) dropLabel.textContent = selectedFile ? selectedFile.name : (T.file_upload_label || 'Glissez un fichier .txt');
  if (analyzeFileBtn) analyzeFileBtn.disabled = !selectedFile;
});

// Drag & drop
dropZone?.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('border-cyan-500'); });
dropZone?.addEventListener('dragleave', () => dropZone.classList.remove('border-cyan-500'));
dropZone?.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('border-cyan-500');
  const file = e.dataTransfer?.files[0];
  if (file) {
    selectedFile = file;
    if (dropLabel) dropLabel.textContent = file.name;
    if (analyzeFileBtn) analyzeFileBtn.disabled = false;
  }
});

analyzeFileBtn?.addEventListener('click', async () => {
  if (!selectedFile) return;
  analyzeFileBtn.disabled = true;
  const fd = new FormData();
  fd.append('file', selectedFile);
  fd.append('lang', fileLangSelect?.value || 'fr');
  fd.append('model', fileModelSelect?.value || 'vader');
  try {
    const res = await fetch('/api/analyze-file', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.error) {
      if (data.error === "transformers_disabled_on_free_plan") {
        showToast("⚠️ Transformers est désactivé sur Render Free. Utilisez VADER.", "warn");
        return;
      }
      showToast(T.toast_error || 'Erreur.', 'error');
      return;
    }
    renderResults(data);
    // Switch to text tab to show results
    tabBtns[0]?.click();
    loadHistory();
  } catch {
    showToast(T.toast_error || 'Erreur.', 'error');
  } finally {
    analyzeFileBtn.disabled = false;
  }
});

// ── Render results ────────────────────────────────────────────
function renderResults(data) {
  const cfg = SENTIMENT_CONFIG[data.sentiment] || SENTIMENT_CONFIG.neutre;
  const scores = data.scores || {};
  const compound = scores.compound ?? 0;

  // Badge
  if (sentimentBadge) {
    sentimentBadge.className = `sentiment-badge ${cfg.cls} mb-6`;
  }
  if (sentimentEmoji) sentimentEmoji.textContent = cfg.emoji;
  if (sentimentLabel) {
    sentimentLabel.textContent = cfg.label;
    sentimentLabel.style.color = cfg.color;
  }
  if (resultModelBadge) resultModelBadge.textContent = data.model?.toUpperCase() || '';

  // Scores
  if (scorePosEl) scorePosEl.textContent = (scores.pos ?? 0).toFixed(4);
  if (scoreNeuEl) scoreNeuEl.textContent = (scores.neu ?? 0).toFixed(4);
  if (scoreNegEl) scoreNegEl.textContent = (scores.neg ?? 0).toFixed(4);
  if (scoreCompound) scoreCompound.textContent = compound >= 0 ? `+${compound.toFixed(4)}` : compound.toFixed(4);

  // Needle position: compound in [-1,1] → left 0%…100%
  if (compoundNeedle) {
    const pct = ((compound + 1) / 2) * 100;
    compoundNeedle.style.left = `${Math.min(100, Math.max(0, pct))}%`;
  }

  // Donut
  updateDonut(scores.pos ?? 0, scores.neu ?? 0, scores.neg ?? 0, compound);

  // Sentence analysis
  const sa = data.sentence_analysis || [];
  if (sentenceSection) {
    sentenceSection.classList.toggle('hidden', sa.length === 0);
    if (sa.length > 0) {
      const sorted = [...sa].sort((a, b) => b.compound - a.compound);
      const mostPos = sorted[0];
      const mostNeg = sorted[sorted.length - 1];
      if (mostPosText) mostPosText.textContent = `"${mostPos.text}"`;
      if (mostPosScore) mostPosScore.textContent = `compound: ${mostPos.compound}`;
      if (mostNegText) mostNegText.textContent = `"${mostNeg.text}"`;
      if (mostNegScore) mostNegScore.textContent = `compound: ${mostNeg.compound}`;
    }
  }

  // Word cloud
  if (wordcloudSection && wordcloudImg) {
    if (data.wordcloud) {
      wordcloudImg.src = `data:image/png;base64,${data.wordcloud}`;
      wordcloudSection.classList.remove('hidden');
    } else {
      wordcloudSection.classList.add('hidden');
    }
  }

  // Highlight HTML (show below results if present)
  const highlightEl = document.getElementById('highlight-container');
  if (highlightEl && data.highlight_html) {
    highlightEl.innerHTML = data.highlight_html;
    highlightEl.classList.remove('hidden');
  }

  // Show panel
  resultsPanel?.classList.remove('hidden');
  resultsPanel?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── History ───────────────────────────────────────────────────
async function loadHistory() {
  try {
    const res = await fetch('/api/history');
    const history = await res.json();
    renderHistory(history);
  } catch { /* silent */ }
}

function renderHistory(history) {
  if (!historyList) return;
  if (!history.length) {
    historyList.innerHTML = '<p class="text-xs text-slate-600 font-mono text-center py-4">Aucune analyse pour le moment</p>';
    updateStats(history);
    return;
  }
  historyList.innerHTML = [...history].reverse().map(item => {
    const dot = item.sentiment === 'positif' ? 'dot-pos' : item.sentiment === 'negatif' ? 'dot-neg' : 'dot-neu';
    const compound = typeof item.compound === 'number'
      ? (item.compound >= 0 ? `+${item.compound.toFixed(3)}` : item.compound.toFixed(3))
      : '—';
    return `
      <div class="history-item">
        <span class="history-dot ${dot}"></span>
        <div class="flex-1 min-w-0">
          <p class="text-slate-300 truncate text-xs leading-tight">${escHtml(item.text)}</p>
          <p class="text-slate-600 font-mono text-[10px] mt-0.5">${item.timestamp} · ${item.language || ''} · <span class="text-cyan-500/70">${compound}</span></p>
        </div>
      </div>
    `;
  }).join('');
  updateStats(history);
}

function updateStats(history) {
  const total = history.length;
  const pos = history.filter(h => h.sentiment === 'positif').length;
  const neg = history.filter(h => h.sentiment === 'negatif').length;
  const neu = history.filter(h => h.sentiment === 'neutre').length;
  if (statTotal) statTotal.textContent = total;
  if (statPos)   statPos.textContent   = pos;
  if (statNeg)   statNeg.textContent   = neg;
  if (statNeu)   statNeu.textContent   = neu;
}

clearHistoryBtn?.addEventListener('click', async () => {
  await fetch('/api/history', { method: 'DELETE' });
  loadHistory();
  showToast(T.toast_history_cleared || 'Historique effacé.');
});

// ── Toast ─────────────────────────────────────────────────────
let _toastTimer = null;
function showToast(msg, type = 'info') {
  if (!toast) return;
  toast.textContent = msg;
  const colors = { info: '', warn: 'text-amber-400', error: 'text-rose-400' };
  toast.className = `fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl text-sm font-medium
    shadow-2xl border border-navy-700 bg-navy-900 transition-all duration-300 ${colors[type] || ''}`;
  toast.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
}

// ── Utilities ─────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Init ──────────────────────────────────────────────────────
buildDonut();
loadHistory();