/* ============================================================
   API — English textEnglish textbase URL English text
   English text/api/modes /api/chat /api/decision /api/archive
        /api/stats /api/config /api/preferences
   ============================================================ */

const API = (() => {
  const BASE = '';  // same-origin API

  async function request(path, options = {}) {
    const opts = {
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      ...options
    };
    if (opts.body && typeof opts.body !== 'string') {
      opts.body = JSON.stringify(opts.body);
    }
    let res;
    try {
      res = await fetch(BASE + path, opts);
    } catch (e) {
      throw new ApiError('network', e.message);
    }
    if (res.status === 204) return null;
    let data = null;
    const text = await res.text();
    if (text) {
      try { data = JSON.parse(text); }
      catch (e) { data = text; }
    }
    if (!res.ok) {
      const msg = (data && (data.detail || data.message)) || res.statusText;
      throw new ApiError(res.status, msg);
    }
    return data;
  }

  class ApiError extends Error {
    constructor(status, message) {
      super(message);
      this.status = status;
      this.name = 'ApiError';
    }
  }

  return {
    ApiError,

    /** GET /api/modes — 6 English text */
    getModes() {
      return request('/api/modes');
    },

    /**
     * POST /api/chat
     * @param {string} question English text
     * @param {string} mode English text id
     * @returns {Promise<{mode, autoRecognized?, brief, result, decisionId?}>}
     */
    chat(question, mode, extra) {
      const body = { question, mode };
      if (extra && typeof extra === 'object') Object.assign(body, extra);
      return request('/api/chat', {
        method: 'POST',
        body
      });
    },

    /** POST /api/decision — English text */
    saveDecision(decision) {
      return request('/api/decision', {
        method: 'POST',
        body: decision
      });
    },

    /** GET /api/decision/:id */
    getDecision(id) {
      return request('/api/decision/' + encodeURIComponent(id));
    },

    /** PATCH /api/decision/:id — English textexecuted/regret English text */
    updateDecision(id, patches) {
      return request('/api/decision/' + encodeURIComponent(id), {
        method: 'PATCH',
        body: patches
      });
    },

    /** DELETE /api/decision/:id */
    deleteDecision(id) {
      return request('/api/decision/' + encodeURIComponent(id), {
        method: 'DELETE'
      });
    },

    /**
     * GET /api/archive?page=&pageSize=
     * @returns {Promise<{items, page, pageSize, total}>}
     */
    getArchive(page = 1, pageSize = 20) {
      const q = new URLSearchParams({ page, pageSize });
      return request('/api/archive?' + q.toString());
    },

    /** GET /api/stats */
    getStats() {
      return request('/api/stats');
    },

    /** Founder Graph */
    getGraph() { return request('/api/graph'); },
    extractGraph(text, provider) {
      const body = { text, provider: provider.provider };
      if (provider.provider === 'byok') Object.assign(body, { apiKey: provider.apiKey, llmModel: provider.llmModel, llmBaseUrl: provider.llmBaseUrl });
      return request('/api/graph/extract', { method: 'POST', body });
    },

    /** GET /api/config — LLM + English text */
    getConfig() {
      return request('/api/config');
    },

    /** POST /api/config */
    saveConfig(config) {
      return request('/api/config', {
        method: 'POST',
        body: config
      });
    },

    /** GET /api/preferences — English textEnglish text/English text/English text/English text */
    getPreferences() {
      return request('/api/preferences');
    },

    /** POST /api/preferences */
    savePreferences(prefs) {
      return request('/api/preferences', {
        method: 'POST',
        body: prefs
      });
    }
  };
})();


/* ============================================================
   MODES — 6 English textEnglish text + tone + English text key
   English text SVG English textsealSVG(modeId) English text <svg> English text
   ============================================================ */

const MODES = (() => {
  // English text + English text tone English text + i18n English text key
  const REGISTRY = [
    { id: 'auto',     char: 'A', tone: 'auto',     color: 'var(--aqua)',   hex: '#317d78', nameKey: 'mode.auto',     descKey: 'mode.auto.desc' },
    { id: 'founder',  char: 'F', tone: 'founder',  color: 'var(--lapis)',  hex: '#365385', nameKey: 'mode.founder',  descKey: 'mode.founder.desc' },
    { id: 'product',  char: 'P', tone: 'product',  color: 'var(--moss)',   hex: '#486a55', nameKey: 'mode.product',  descKey: 'mode.product.desc' },
    { id: 'people',   char: 'H', tone: 'people',   color: 'var(--plum)',   hex: '#69526f', nameKey: 'mode.people',   descKey: 'mode.people.desc' },
    { id: 'money',    char: '$', tone: 'money',    color: 'var(--ochre)',  hex: '#9b7636', nameKey: 'mode.money',    descKey: 'mode.money.desc' },
    { id: 'growth',   char: 'G', tone: 'growth',   color: 'var(--aqua)',   hex: '#317d78', nameKey: 'mode.growth',   descKey: 'mode.growth.desc' },
    { id: 'conflict', char: 'C', tone: 'conflict', color: 'var(--cinnabar)', hex: '#b45a42', nameKey: 'mode.conflict', descKey: 'mode.conflict.desc' }
  ];  const BY_ID = Object.fromEntries(REGISTRY.map(m => [m.id, m]));

  /**
   * English text SVGEnglish text + English text + English text
   * @param {string} modeId
   * @param {object} opt { size, rounded, hollow }
   */
  function sealSVG(modeId, opt = {}) {
    const m = BY_ID[modeId];
    if (!m) return '';
    const size = opt.size || 24;
    const r = opt.rounded != null ? opt.rounded : 4;
    const fill = opt.hollow ? 'none' : m.hex;
    const stroke = opt.hollow ? m.hex : 'none';
    const textColor = opt.hollow ? m.hex : '#ffffff';
    // English textEnglish text + English text
    return `<svg class="seal" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
      <rect x="1.5" y="1.5" width="21" height="21" rx="${r}" fill="${fill}" stroke="${stroke}" stroke-width="1.2"/>
      <rect x="3.5" y="3.5" width="17" height="17" rx="${Math.max(r - 1, 2)}" fill="none" stroke="rgba(255,255,255,0.28)" stroke-width="0.8"/>
      <text x="12" y="16.5" font-family="'Songti SC','Noto Serif SC','STSong',serif" font-size="13" font-weight="700" fill="${textColor}" text-anchor="middle" dominant-baseline="middle">${m.char}</text>
    </svg>`;
  }

  function list() { return REGISTRY.slice(); }
  function get(id) { return BY_ID[id]; }
  function toneColor(tone) {
    const m = REGISTRY.find(x => x.tone === tone);
    return m ? m.hex : '#317d78';
  }

  return { REGISTRY, BY_ID, sealSVG, list, get, toneColor };
})();
