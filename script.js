(() => {
  const photos = [...document.querySelectorAll(
    'main img, article img, .drive-figure img, .evidence-photo img'
  )].filter(img => !img.closest('nav, button, [role="button"], .evidence-player')
    && !img.matches('[width="1"], [height="1"]'));
  if (photos.length) {
    const dialog = document.createElement('dialog');
    dialog.className = 'photo-viewer';
    dialog.setAttribute('aria-label', 'Enlarged photo');
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'photo-viewer-close';
    close.textContent = 'Close';
    const full = document.createElement('img');
    dialog.append(close, full);
    document.body.append(dialog);
    let trigger;
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener('close', () => {
      full.removeAttribute('src');
      trigger?.focus();
    });
    photos.forEach(img => {
      const source = img.currentSrc || img.src;
      if (!source) return;
      let link = img.closest('a');
      if (!link) {
        link = document.createElement('a');
        link.href = source;
        img.before(link);
        link.append(img);
      } else if (!/\\.(?:avif|gif|jpe?g|png|webp)(?:[?#]|$)/i.test(link.href)) {
        return;
      }
      link.classList.add('photo-zoom');
      link.setAttribute('aria-label', img.alt ? 'Enlarge photo: ' + img.alt : 'Enlarge photo');
      link.addEventListener('click', event => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey
            || event.button !== 0 || typeof dialog.showModal !== 'function') return;
        event.preventDefault();
        trigger = link;
        full.alt = img.alt;
        full.src = link.href;
        dialog.showModal();
        close.focus();
      });
    });
  }
  document.querySelectorAll('.evidence-player').forEach(player => {
    const video = player.querySelector('video');
    const button = player.querySelector('.evidence-play');
    if (!video || !button) return;
    button.hidden = false;
    button.addEventListener('click', async () => {
      try { await video.play(); } catch { video.controls = true; }
    });
    video.addEventListener('play', () => { button.hidden = true; });
    video.addEventListener('pause', () => { button.hidden = false; });
    video.addEventListener('ended', () => { button.hidden = false; });
  });
  const toggle = document.querySelector('.menu');
  const nav = document.querySelector('#nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('open', open);
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
      nav.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }));
  }
  const page = location.pathname.split('/').filter(Boolean).pop() || 'index.html';
  const main = new Set(['index.html','about.html','observations.html','goals.html',
    'reflections.html','standards.html','teaching.html','references.html']);
  let section = main.has(page) ? page : '';
  if (/^goal-\d+\.html$/.test(page)) section = 'goals.html';
  if (/^standard-\d+\.html$/.test(page)) section = 'standards.html';
  if (/^reflection-week-\d+\.html$/.test(page)) section = 'reflections.html';
  if (!section && /^(?:doc|file|slides|sheet)-/.test(page)) {
    const back = document.querySelector('footer .footinner a[href]');
    const target = back?.getAttribute('href') || '';
    if (main.has(target) && target !== 'index.html') section = target;
  }
  nav?.querySelectorAll('a').forEach(link => {
    if (link.getAttribute('href') === section) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  // Compact expandable contents menu for long goal or standard webpages.
  if (/^(?:goal|standard)-\d+\.html$/.test(page)) {
    const article = document.querySelector('.native-reflection');
    const headings = [...(article?.querySelectorAll('.reflection-prose h3') || [])]
      .filter(h => h.textContent.trim());
    if (article && headings.length >= 4) {
      const used = new Set([...document.querySelectorAll('[id]')].map(el => el.id));
      const toc = document.createElement('details');
      toc.className = 'page-contents';
      const summary = document.createElement('summary');
      summary.textContent = 'On this page';
      toc.appendChild(summary);
      const links = document.createElement('nav');
      links.setAttribute('aria-label', 'Contents');
      headings.forEach(heading => {
        if (!heading.id) {
          const stem = heading.textContent.toLowerCase().normalize('NFKD')
            .replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '') || 'section';
          let id = stem, count = 2;
          while (used.has(id)) id = stem + '-' + count++;
          heading.id = id;
          used.add(id);
        }
        const link = document.createElement('a');
        link.href = '#' + heading.id;
        link.textContent = heading.textContent.trim();
        links.appendChild(link);
      });
      toc.appendChild(links);
      article.parentNode.insertBefore(toc, article);
    }
  }
})();

