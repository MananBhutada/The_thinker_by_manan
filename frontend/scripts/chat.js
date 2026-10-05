/* ============================================================
   Chat — English text
   English textEnglish text / English text / English text API / English text
   English textAPI, Brief, MODES, I18N, Apptoast
   ============================================================ */

const Chat = (() => {
  let currentMode = 'founder';
  let busy = false;
  let lastQuestion = '';
  let pendingImage = null; // data URL

  const $ = (id) => document.getElementById(id);

  function clearImage() {
    pendingImage = null;
    const imageInput = $('imageInput');
    const imagePreview = $('imagePreview');
    const imagePreviewImg = $('imagePreviewImg');
    if (imageInput) imageInput.value = '';
    if (imagePreview) imagePreview.hidden = true;
    if (imagePreviewImg) imagePreviewImg.src = '';
  }

  function init() {
    // English text
    document.querySelectorAll('#modeSelector .mode-card').forEach(card => {
      card.addEventListener('click', () => {
        if (busy) return;
        setMode(card.getAttribute('data-mode'));
      });
    });

    // English text
    document.querySelectorAll('#quickExamples .quick-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        if (busy) return;
        $('inputText').value = chip.textContent;
        send();
      });
    });

    // English text
    $('sendBtn').addEventListener('click', send);
    const ta = $('inputText');
    ta.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
      }
    });
    ta.addEventListener('input', () => autoGrow(ta));

    // English text
    const micBtn = $('micBtn');
    if (micBtn) {
      micBtn.addEventListener('click', () => Voice.toggleStt(ta));
      if (!Voice.sttSupported()) micBtn.style.display = 'none';
    }

    // English text
    const imageBtn = $('imageBtn');
    const imageInput = $('imageInput');
    const imagePreview = $('imagePreview');
    const imagePreviewImg = $('imagePreviewImg');
    const imageRemove = $('imageRemove');
    if (imageBtn && imageInput) {
      imageBtn.addEventListener('click', () => imageInput.click());
      imageInput.addEventListener('change', (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;
        if (!file.type.startsWith('image/')) {
          App.toast(I18N.t('common.error'));
          return;
        }
        if (file.size > 5 * 1024 * 1024) {
          App.toast('English text 5MB');
          imageInput.value = '';
          return;
        }
        const reader = new FileReader();
        reader.onload = (ev) => {
          pendingImage = ev.target.result;
          imagePreviewImg.src = pendingImage;
          imagePreview.hidden = false;
        };
        reader.readAsDataURL(file);
      });
      if (imageRemove) {
        imageRemove.addEventListener('click', clearImage);
      }
    }

    // English text
    $('newChatBtn').addEventListener('click', () => {
      if (busy) return;
      reset();
    });

    // English text / English text
    window.addEventListener('bjj:resubmit', (e) => {
      ta.value = lastQuestion + ' ' + e.detail;
      send();
    });
    window.addEventListener('bjj:dialogue-complete', async (e) => {
      const current = App.currentDecision;
      if (!current || !e.detail || !e.detail.answer) return;
      const history = Array.isArray(current.dialogueHistory) ? current.dialogueHistory.slice() : [];
      history.push({ question: e.detail.question || lastQuestion, answer: e.detail.answer });
      try {
        const updated = await API.updateDecision(current.id, { dialogueHistory: history });
        App.currentDecision = { ...current, ...updated };
      } catch (_) {
        App.toast(I18N.t('common.error'));
      }
    });
  }

  function setMode(modeId) {
    if (!MODES.get(modeId)) return;
    currentMode = modeId;
    document.querySelectorAll('#modeSelector .mode-card').forEach(c => {
      const active = c.getAttribute('data-mode') === modeId;
      c.classList.toggle('active', active);
      c.setAttribute('aria-checked', active ? 'true' : 'false');
    });
    if (navigator.vibrate) navigator.vibrate(10);
  }

  function getMode() { return currentMode; }

  function autoGrow(ta) {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 180) + 'px';
  }

  async function send() {
    if (busy) return;
    const text = $('inputText').value.trim();
    if (!text && !pendingImage) return;
    const provider = await FounderProvider.open();
    if (!provider) return;

    busy = true;
    lastQuestion = text || '';
    const imgToSend = pendingImage;
    $('sendBtn').disabled = true;
    $('inputText').value = '';
    autoGrow($('inputText'));
    clearImage();

    // English textEnglish text
    appendMessage('user', text || '', imgToSend);
    // English text
    const thinking = appendThinking();

    try {
      const extra = {
        provider: provider.provider
      };
      if (provider.provider === 'byok') {
        extra.apiKey = provider.apiKey;
        extra.llmModel = provider.llmModel;
        extra.llmBaseUrl = provider.llmBaseUrl;
      }
      if (imgToSend) extra.image = imgToSend;
      const resp = await API.chat(text, currentMode, extra);
      thinking.remove();
      // auto English text
      const recognizedMode = resp.autoRecognized && resp.autoRecognized.mode;
      if (currentMode === 'auto' && recognizedMode && recognizedMode !== 'auto') {
        const m = MODES.get(recognizedMode);
        if (m) appendAutoHint(I18N.t('auto.recognized', { mode: I18N.t(m.nameKey) }));
      }
      // English text
      const card = Brief.fromResponse(resp);
      // English text
      if (Voice.ttsSupported() && resp.reply) {
        const speakBtn = Voice.makeSpeakButton(resp.reply);
        speakBtn.classList.add('brief-action-btn');
        card.insertBefore(speakBtn, card.firstChild);
      }
      appendCard(card);

      // English textEnglish text decisionId English text executed/regret
      if (resp.decisionId) {
        App.currentDecision = { id: resp.decisionId, mode: resp.mode };
      }

      // English textEnglish text
      if (Voice.ttsSupported() && resp.reply && App.prefs && App.prefs.auto_speak) {
        Voice.speak(resp.reply);
      }
    } catch (e) {
      thinking.remove();
      if (e && e.status === 402) {
        App.showKeyBanner && App.showKeyBanner();
        App.toast(I18N.t('api.keyRequired'));
      } else {
        appendError(e);
      }
    } finally {
      busy = false;
      $('sendBtn').disabled = false;
    }
  }

  function appendMessage(role, text, imageSrc) {
    const wrap = document.createElement('div');
    wrap.className = 'message ' + role;
    const bubble = document.createElement('div');
    bubble.className = 'bubble ' + role;
    if (imageSrc) {
      const img = document.createElement('img');
      img.src = imageSrc;
      img.className = 'bubble-image';
      img.alt = '';
      bubble.appendChild(img);
    }
    if (text) {
      const textNode = document.createElement('div');
      textNode.className = 'bubble-text';
      textNode.textContent = text;
      bubble.appendChild(textNode);
    }
    wrap.appendChild(bubble);
    getContainer().appendChild(wrap);
    scrollBottom();
  }

  function appendThinking() {
    const wrap = document.createElement('div');
    wrap.className = 'message ai';
    const t = document.createElement('div');
    t.className = 'thinking';
    t.innerHTML = '<span>' + I18N.t('common.thinking') + '</span><span class="loading-dots"><span></span><span></span><span></span></span>';
    wrap.appendChild(t);
    getContainer().appendChild(wrap);
    scrollBottom();
    return wrap;
  }

  function appendCard(node) {
    const wrap = document.createElement('div');
    wrap.className = 'message ai';
    wrap.appendChild(node);
    getContainer().appendChild(wrap);
    scrollBottom();
  }

  function appendAutoHint(text) {
    const wrap = document.createElement('div');
    wrap.className = 'auto-hint';
    wrap.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/><circle cx="12" cy="12" r="4"/></svg><span></span>';
    wrap.querySelector('span').textContent = text;
    getContainer().appendChild(wrap);
    scrollBottom();
  }

  function appendError(e) {
    const wrap = document.createElement('div');
    wrap.className = 'message ai';
    const t = document.createElement('div');
    t.className = 'thinking';
    t.style.color = 'var(--cinnabar)';
    let msg = I18N.t('common.error');
    if (e && e.status === 'network') {
      msg = I18N.t('common.networkError');
    } else if (e && e.message) {
      msg = String(e.message).slice(0, 420);
    }
    t.textContent = msg;
    wrap.appendChild(t);
    getContainer().appendChild(wrap);
    scrollBottom();
    App.toast(msg);
  }

  function getContainer() {
    return $('chatContainer');
  }

  function scrollBottom() {
    const sc = $('chatScroll');
    requestAnimationFrame(() => { sc.scrollTop = sc.scrollHeight; });
  }

  function reset() {
    getContainer().innerHTML = '';
    App.currentDecision = null;
    setMode('founder');
  }

  return { init, setMode, getMode, reset };
})();
