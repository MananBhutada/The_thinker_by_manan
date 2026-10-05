/* FounderOS request-scoped AI provider chooser. Nothing is persisted client-side. */
const FounderProvider = (() => {
  function open() {
    return new Promise(resolve => {
      const body = document.createElement("div");
      body.className = "provider-sheet";
      body.innerHTML =
        '<p class="provider-copy">Choose the engine for this request. FounderOS never saves a personal API key.</p>' +
        '<div class="provider-options">' +
          '<button type="button" class="provider-option" data-provider="free"><span class="provider-icon">✦</span><span><strong>FounderOS Free AI</strong><small>No setup. Uses the hosted FounderOS model.</small></span><b>→</b></button>' +
          '<button type="button" class="provider-option" data-provider="byok"><span class="provider-icon">⌘</span><span><strong>Use my API key</strong><small>OpenRouter, Qwen, OpenAI or another compatible provider.</small></span><b>→</b></button>' +
        '</div>' +
        '<button type="button" class="provider-cancel">Cancel</button>';

      body.querySelector('[data-provider="free"]').onclick = () => {
        App.closeModal();
        resolve({ provider:"free" });
      };

      body.querySelector('[data-provider="byok"]').onclick = () => {
        body.innerHTML =
          '<div class="provider-back" role="button" tabindex="0">← Back</div>' +
          '<p class="provider-copy">Used for this request only. Nothing is stored.</p>' +
          '<div class="field"><label>API key</label><input id="sessionApiKey" type="password" autocomplete="off" placeholder="Paste your provider key"></div>' +
          '<div class="field"><label>Model</label><input id="sessionModel" value="qwen/qwen3.8-27b:free"></div>' +
          '<div class="field"><label>Base URL</label><input id="sessionBase" value="https://openrouter.ai/api/v1"></div>' +
          '<button type="button" class="btn btn-block" id="sessionStart">Use this key</button>';
        body.querySelector(".provider-back").onclick = () => openAgain(body, resolve);
        body.querySelector("#sessionStart").onclick = () => {
          const key = body.querySelector("#sessionApiKey").value.trim();
          const model = body.querySelector("#sessionModel").value.trim();
          const base = body.querySelector("#sessionBase").value.trim();
          if (!key || !model || !base) {
            App.toast("Enter the API key, model and base URL.");
            return;
          }
          App.closeModal();
          resolve({ provider:"byok", apiKey:key, llmModel:model, llmBaseUrl:base });
        };
      };

      body.querySelector(".provider-cancel").onclick = () => {
        App.closeModal();
        resolve(null);
      };
      App.openModal(body, { title:"Power this request" });
    });
  }

  function openAgain(body, resolve) {
    App.closeModal();
    // Re-open a fresh chooser without creating a second unresolved promise.
    const fresh = open();
    fresh.then(value => resolve(value));
  }

  return { open };
})();