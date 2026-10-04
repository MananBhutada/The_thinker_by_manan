/* Session/request-scoped AI provider chooser. No API key is persisted. */
const FounderProvider = (() => {
  function open() {
    return new Promise(resolve => {
      const body=document.createElement('div');
      body.innerHTML='<p class="provider-copy">Choose how to power this request. Your API key is used only for this request and is never saved by FounderOS.</p><div class="provider-options"><button type="button" class="provider-option" data-provider="byok"><strong>Use my API key</strong><span>OpenRouter, Qwen, OpenAI or another OpenAI-compatible provider.</span></button><button type="button" class="provider-option" data-provider="free"><strong>Use FounderOS Free AI</strong><span>Use the hosted free model directly. No key required.</span></button></div>';
      body.querySelectorAll('[data-provider]').forEach(b=>b.onclick=()=>{
        if(b.dataset.provider==='free'){ App.closeModal(); resolve({provider:'free'}); return; }
        body.innerHTML='<p class="provider-copy">Nothing is stored. Paste your provider details for this request.</p><div class="field"><label>API key</label><input id="sessionApiKey" type="password" autocomplete="off" placeholder="sk-…"></div><div class="field"><label>Model</label><input id="sessionModel" value="qwen/qwen3.8-27b:free"></div><div class="field"><label>Base URL</label><input id="sessionBase" value="https://openrouter.ai/api/v1"></div><button class="btn btn-block" id="sessionStart">Continue</button>';
        body.querySelector('#sessionStart').onclick=()=>{
          const key=body.querySelector('#sessionApiKey').value.trim(), model=body.querySelector('#sessionModel').value.trim(), base=body.querySelector('#sessionBase').value.trim();
          if(!key||!model||!base)return;
          App.closeModal(); resolve({provider:'byok',apiKey:key,llmModel:model,llmBaseUrl:base});
        };
      });
      App.openModal(body,{title:'Power this request'});
    });
  }
  return {open};
})();