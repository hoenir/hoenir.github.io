// Paper pages: citation/figure previews, reference backlinks, TOC highlighting, cite dialog.
(function () {
  var body = document.querySelector('.paper-body');
  if (!body) return;

  function targetOf(link) {
    return document.getElementById(decodeURIComponent(link.hash.slice(1)));
  }

  // Backlinks: under each reference, link to the sections where it is cited
  var citesByRef = {};
  body.querySelectorAll('a[role="doc-biblioref"]').forEach(function (a, i) {
    a.id = 'cite-' + (i + 1);
    var key = decodeURIComponent(a.hash.slice(1));
    (citesByRef[key] = citesByRef[key] || []).push(a);
  });
  Object.keys(citesByRef).forEach(function (key) {
    var entry = document.getElementById(key);
    if (!entry) return;
    var seen = {};
    var line = document.createElement('p');
    line.className = 'backlinks';
    line.append('Cited in ');
    citesByRef[key].forEach(function (a) {
      var section = a.closest('section');
      var heading = section && section.querySelector('h2');
      var label = heading ? heading.textContent : 'text';
      if (seen[label]) return;
      seen[label] = true;
      if (Object.keys(seen).length > 1) line.append(', ');
      var back = document.createElement('a');
      back.href = '#' + a.id;
      back.textContent = label;
      line.append(back);
    });
    entry.append(line);
  });

  // Previews: hover (mouse), focus (keyboard) or first tap (touch) shows the reference or figure
  var pop = document.createElement('div');
  pop.className = 'paper-popover';
  pop.setAttribute('role', 'tooltip');
  pop.hidden = true;
  document.body.append(pop);

  var current = null, showTimer, hideTimer, input = 'mouse';
  document.addEventListener('pointerdown', function (e) { input = e.pointerType; }, true);
  document.addEventListener('keydown', function (e) {
    input = 'keyboard';
    if (e.key === 'Escape') hide();
  }, true);

  function preview(link) {
    var target = targetOf(link);
    if (!target) return null;
    var box = document.createElement('div');
    if (target.tagName === 'FIGURE') {
      var img = target.querySelector('img').cloneNode();
      img.removeAttribute('id');
      box.append(img);
      var caption = target.querySelector('figcaption');
      if (caption) box.append(caption.cloneNode(true));
    } else {
      var entry = target.cloneNode(true);
      entry.removeAttribute('id');
      var backlinks = entry.querySelector('.backlinks');
      if (backlinks) backlinks.remove();
      box.append(entry);
    }
    var jump = document.createElement('a');
    jump.className = 'popover-jump';
    jump.href = link.hash;
    jump.textContent = target.tagName === 'FIGURE' ? 'Go to figure ↓' : 'Go to reference ↓';
    jump.addEventListener('click', hide);
    box.append(jump);
    return box;
  }

  function show(link) {
    clearTimeout(hideTimer);
    var content = preview(link);
    if (!content) return;
    pop.replaceChildren(content);
    pop.hidden = false;
    current = link;
    var r = link.getBoundingClientRect();
    var w = pop.offsetWidth, h = pop.offsetHeight;
    var x = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), window.innerWidth - w - 8);
    var y = r.bottom + 8;
    if (y + h > window.innerHeight - 8 && r.top - h - 8 > 8) y = r.top - h - 8;
    pop.style.left = (x + window.scrollX) + 'px';
    pop.style.top = (y + window.scrollY) + 'px';
  }

  function hide() {
    pop.hidden = true;
    current = null;
  }

  function hideSoon() {
    clearTimeout(showTimer);
    hideTimer = setTimeout(hide, 250);
  }

  body.querySelectorAll('a[role="doc-biblioref"], a[href^="#fig-"]').forEach(function (link) {
    link.addEventListener('mouseenter', function () {
      if (input !== 'mouse') return;
      clearTimeout(hideTimer);
      showTimer = setTimeout(function () { show(link); }, 150);
    });
    link.addEventListener('mouseleave', hideSoon);
    link.addEventListener('focus', function () { if (input === 'keyboard') show(link); });
    link.addEventListener('blur', hideSoon);
    link.addEventListener('click', function (e) {
      // On touch, the first tap previews; tapping the same citation again follows the link
      if ((input === 'touch' || input === 'pen') && current !== link) {
        e.preventDefault();
        show(link);
      } else {
        hide();
      }
    });
  });
  pop.addEventListener('mouseenter', function () { clearTimeout(hideTimer); });
  pop.addEventListener('mouseleave', hideSoon);
  document.addEventListener('click', function (e) {
    if (current && !pop.contains(e.target) && e.target.closest('a') !== current) hide();
  });

  // Figures open full size in a new tab
  body.querySelectorAll('figure img').forEach(function (img) {
    img.addEventListener('click', function () { window.open(img.currentSrc || img.src, '_blank', 'noopener'); });
  });

  // Highlight the current section in the table of contents
  var sections = [document.getElementById('abstract')].concat([].slice.call(body.querySelectorAll('section[id]')))
    .filter(function (s) { return s && !s.closest('.backmatter') && s.querySelector('h2'); });
  var tocLinks = document.querySelectorAll('.paper-toc a');
  var ticking = false;
  function updateToc() {
    ticking = false;
    var active = sections[0];
    sections.forEach(function (s) {
      if (s.getBoundingClientRect().top < window.innerHeight * 0.3) active = s;
    });
    tocLinks.forEach(function (a) {
      a.classList.toggle('is-active', active && a.hash === '#' + active.id);
    });
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(updateToc); }
  }, { passive: true });
  updateToc();

  // Cite dialog with copy buttons
  var citeDialog = document.querySelector('.cite-dialog');
  var citeButton = document.querySelector('[data-cite-open]');
  if (citeDialog && citeButton && typeof citeDialog.showModal === 'function') {
    citeButton.addEventListener('click', function () { citeDialog.showModal(); });
    citeDialog.addEventListener('click', function (e) {
      var r = citeDialog.getBoundingClientRect();
      var outside = e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
      if (e.target === citeDialog && outside) citeDialog.close();
    });
  }
  document.querySelectorAll('[data-copy]').forEach(function (button) {
    button.addEventListener('click', function () {
      var text = document.getElementById(button.getAttribute('data-copy')).innerText.trim();
      navigator.clipboard.writeText(text).then(function () {
        button.textContent = 'Copied';
        setTimeout(function () { button.textContent = 'Copy'; }, 1500);
      });
    });
  });
})();
