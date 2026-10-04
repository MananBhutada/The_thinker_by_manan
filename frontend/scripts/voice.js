/* ============================================================
   Voice — English textSTT+ English textTTSEnglish text SpeechSynthesis
   English text
     - STTEnglish text/English textEnglish text textarea
     - TTSEnglish text replyEnglish text + English text
     - English textEnglish text/English text/English text/English text
   English textI18N, Appprefs / toast
   English text
     - STT English text Web Speech API SpeechRecognitionChrome/Edge English text
     - TTS English text SpeechSynthesisWindows English text SAPIEnglish text
   ============================================================ */

const Voice = (() => {
  const $ = (id) => document.getElementById(id);

  /* ---------- STT ---------- */
  let recognition = null;
  let recognizing = false;
  let sttTarget = null; // English text textarea

  function sttSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  // English text i18n English text BCP-47SpeechRecognition English text
  function bcp47(lang) {
    switch (lang) {
      case 'zh-CN': return 'zh-CN';
      case 'yue':   return 'zh-HK';   // English text fallback English text
      case 'en':    return 'en-US';
      case 'fr':    return 'fr-FR';
      case 'ja':    return 'ja-JP';
      case 'es':    return 'es-ES';
      default:      return 'zh-CN';
    }
  }

  function ensureRecognition() {
    if (recognition) return recognition;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = bcp47(I18N.getLocale());
    recognition.onresult = (e) => {
      if (!sttTarget) return;
      let final = '';
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) final += r[0].transcript;
        else interim += r[0].transcript;
      }
      if (final) sttTarget.value = (sttTarget.value ? sttTarget.value + ' ' : '') + final.trim();
      else if (interim) sttTarget.dataset.interim = interim;
    };
    recognition.onerror = (e) => {
      recognizing = false;
      setMicState(false);
      if (e.error === 'not-allowed') App.toast(I18N.t('chat.mic.notSupported'));
      else if (e.error !== 'aborted' && e.error !== 'no-speech') App.toast(I18N.t('chat.mic.notSupported'));
    };
    recognition.onend = () => {
      recognizing = false;
      setMicState(false);
      if (sttTarget && sttTarget.dataset.interim) {
        delete sttTarget.dataset.interim;
      }
    };
    return recognition;
  }

  function setMicState(on) {
    const btn = $('micBtn');
    if (!btn) return;
    btn.classList.toggle('listening', on);
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    btn.setAttribute('aria-label', I18N.t(on ? 'chat.mic.listening' : 'chat.mic'));
  }

  function toggleStt(textareaEl) {
    if (!sttSupported()) {
      App.toast(I18N.t('chat.mic.notSupported'));
      return;
    }
    if (recognizing) {
      try { recognition.stop(); } catch (_) {}
      recognizing = false;
      setMicState(false);
      return;
    }
    sttTarget = textareaEl;
    const r = ensureRecognition();
    if (!r) {
      App.toast(I18N.t('chat.mic.notSupported'));
      return;
    }
    r.lang = bcp47(I18N.getLocale());
    try {
      r.start();
      recognizing = true;
      setMicState(true);
    } catch (_) {
      recognizing = false;
      setMicState(false);
    }
  }

  /* ---------- TTS ----------
   * English textEnglish text edge-ttsEnglish text /api/tts/speak English text MP3English text SpeechSynthesis
   * edge English textEnglish text/English textEnglish text/English text
   */

  let edgeUnavailable = false;  // English textEnglish text
  let edgeAudio = null;         // English text Audio English textedge English text

  function browserTtsSupported() {
    return !!window.speechSynthesis && typeof window.speechSynthesis.speak === 'function';
  }

  function ttsSupported() {
    return true;  // edge English text browser English textedge English text
  }

  function edgeTtsUrl(text, opts = {}) {
    const prefs = App.prefs || {};
    const params = new URLSearchParams();
    params.set('text', text);
    const voice = opts.voice || prefs.tts_voice_uri || 'zh-CN-XiaoxiaoNeural';
    params.set('voice', voice);
    const rate = (opts.rate != null ? opts.rate : prefs.tts_rate) || 0.95;
    const pitch = (opts.pitch != null ? opts.pitch : prefs.tts_pitch) || 1.05;
    params.set('rate', String(rate));
    params.set('pitch', String(pitch));
    return '/api/tts/speak?' + params.toString();
  }

  function stop() {
    // English text edge
    if (edgeAudio) {
      try { edgeAudio.pause(); edgeAudio.src = ''; } catch (_) {}
      edgeAudio = null;
    }
    // English text
    if (browserTtsSupported()) {
      try { window.speechSynthesis.cancel(); } catch (_) {}
    }
  }

  function isSpeaking() {
    if (edgeAudio && !edgeAudio.paused && !edgeAudio.ended) return true;
    if (browserTtsSupported() && window.speechSynthesis.speaking) return true;
    return false;
  }

  function _speakBrowser(text, opts = {}) {
    if (!browserTtsSupported()) return;
    try { window.speechSynthesis.cancel(); } catch (_) {}
    const u = new SpeechSynthesisUtterance(text);
    const prefs = App.prefs || {};
    u.rate = typeof prefs.tts_rate === 'number' ? prefs.tts_rate : 0.95;
    u.pitch = typeof prefs.tts_pitch === 'number' ? prefs.tts_pitch : 1.05;
    u.lang = bcp47(prefs.language || 'zh-CN');
    // English text voiceEnglish textedge English text
    if (opts.onend) u.onend = opts.onend;
    if (opts.onstart) u.onstart = opts.onstart;
    if (opts.onerror) u.onerror = opts.onerror;
    window.speechSynthesis.speak(u);
  }

  // English text edge-tts English textEnglish text Promise English text
  function _speakEdge(text, opts = {}) {
    return new Promise((resolve, reject) => {
      if (edgeUnavailable) return reject(new Error('edge unavailable'));
      stop();
      const audio = new Audio();
      audio.src = edgeTtsUrl(text, opts);
      audio.preload = 'auto';
      let settled = false;
      const done = (err) => {
        if (settled) return;
        settled = true;
        if (err) reject(err);
        else resolve();
      };
      audio.addEventListener('canplaythrough', () => {
        try { audio.play().catch(done); } catch (e) { done(e); }
      }, { once: true });
      audio.addEventListener('play', () => {
        if (opts.onstart) opts.onstart();
      }, { once: true });
      audio.addEventListener('ended', () => {
        edgeAudio = null;
        if (opts.onend) opts.onend();
        done();
      }, { once: true });
      audio.addEventListener('error', (e) => {
        edgeAudio = null;
        // English text/English textEnglish text edge English textEnglish text
        edgeUnavailable = true;
        done(e.error || new Error('edge tts error'));
      }, { once: true });
      edgeAudio = audio;
      audio.load();
      // 5 English text canplaythrough English text
      setTimeout(() => {
        if (!settled && (audio.readyState < 2)) {
          try { audio.pause(); } catch (_) {}
          edgeUnavailable = true;
          done(new Error('edge tts timeout'));
        }
      }, 5000);
    });
  }

  async function speak(text, opts = {}) {
    if (!text) return;
    try {
      await _speakEdge(text, opts);
    } catch (e) {
      // edge English text
      _speakBrowser(text, opts);
    }
  }

  // English textEnglish text
  function makeSpeakButton(text) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'icon-button speak-button';
    btn.setAttribute('aria-label', I18N.t('chat.speak'));
    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>';
    let speaking = false;
    const onStart = () => {
      speaking = true;
      btn.classList.add('speaking');
      btn.setAttribute('aria-label', I18N.t('chat.speak.stop'));
    };
    const onEnd = () => {
      speaking = false;
      btn.classList.remove('speaking');
      btn.setAttribute('aria-label', I18N.t('chat.speak'));
    };
    btn.addEventListener('click', () => {
      if (speaking) {
        stop();
        onEnd();
      } else {
        speak(text, { onstart: onStart, onend: onEnd });
      }
    });
    return btn;
  }

  // English textEnglish textEnglish text
  let voicesCache = null;
  async function getEdgeVoices(lang) {
    if (voicesCache) return voicesCache;
    try {
      const url = lang ? `/api/tts/voices?lang=${encodeURIComponent(lang)}` : '/api/tts/voices';
      const resp = await fetch(url);
      const data = await resp.json();
      voicesCache = data.voices || [];
    } catch (e) {
      voicesCache = [];
    }
    return voicesCache;
  }

  function resetEdgeAvailability() {
    edgeUnavailable = false;
  }

  return {
    sttSupported,
    ttsSupported,
    toggleStt,
    speak,
    stop,
    isSpeaking,
    makeSpeakButton,
    getEdgeVoices,
    resetEdgeAvailability,
    edgeTtsUrl,
  };
})();
