(() => {
  const OPTIONS = ['English text', 'English text', 'English text', 'English text', 'English text', 'English text'];
  const EFFECTS = [
    { variant: 'pointer', title: 'English text', note: 'English text 1 English text', seed: 'preview-10', picked: 0 },
    { variant: 'sticks', title: 'English text', note: 'English text 2 English text', seed: 'preview-6', picked: 1 },
    { variant: 'dice', title: 'English text', note: 'English text 3 English text', seed: 'preview-1', picked: 2 },
    { variant: 'cards', title: 'English text', note: 'English text 4 English text', seed: 'preview-0', picked: 3 },
    { variant: 'tickets', title: 'English text', note: 'English text 5 English text', seed: 'preview-3', picked: 4 },
    { variant: 'ink', title: 'English text', note: 'English text 6 English text', seed: 'preview-13', picked: 5 }
  ];

  function renderEffect(effect, mount) {
    mount.replaceChildren(Brief.renderBrief({
      tone: 'random',
      modeName: 'English text',
      percent: 100,
      title: effect.title,
      options: OPTIONS,
      wheelResult: OPTIONS[effect.picked],
      randomSeed: effect.seed
    }));
  }

  function createEffect(effect) {
    const section = document.createElement('section');
    section.className = 'preview-effect';
    section.dataset.variant = effect.variant;

    const bar = document.createElement('div');
    bar.className = 'preview-effect-bar';

    const title = document.createElement('div');
    title.className = 'preview-effect-title';
    title.innerHTML = '<h2></h2><span></span>';
    title.querySelector('h2').textContent = effect.title;
    title.querySelector('span').textContent = effect.note;

    const replay = document.createElement('button');
    replay.type = 'button';
    replay.className = 'preview-replay';
    replay.textContent = '↻';
    replay.title = 'English text';
    replay.setAttribute('aria-label', 'English text' + effect.title);

    const mount = document.createElement('div');
    mount.className = 'preview-mount';
    mount.dataset.previewVariant = effect.variant;

    replay.addEventListener('click', () => renderEffect(effect, mount));
    bar.append(title, replay);
    section.append(bar, mount);
    renderEffect(effect, mount);
    return section;
  }

  document.querySelectorAll('.preview-skin').forEach(button => {
    button.addEventListener('click', () => {
      document.documentElement.dataset.skin = button.dataset.skin;
      document.querySelectorAll('.preview-skin').forEach(item => {
        item.classList.toggle('is-active', item === button);
      });
    });
  });

  const grid = document.getElementById('previewGrid');
  EFFECTS.forEach(effect => grid.appendChild(createEffect(effect)));
})();
