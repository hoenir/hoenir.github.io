// Mobile menu toggle
document.querySelectorAll('.site-header .menu').forEach(function (button) {
  var header = button.closest('.site-header');
  button.addEventListener('click', function () {
    var open = header.classList.toggle('nav-open');
    button.setAttribute('aria-expanded', open);
  });
});

// Lighten the hero overlay once the featured image has loaded
document.querySelectorAll('.featured-image').forEach(function (hero) {
  var match = getComputedStyle(hero).backgroundImage.match(/url\(["']?(.*?)["']?\)/);
  var overlay = hero.parentNode.querySelector('.overlay');
  if (!match || !overlay) return;
  var img = new Image();
  img.onload = function () { overlay.classList.add('is-loaded'); };
  img.src = match[1];
});

// Share dialog: open from the Share button, close on backdrop click or after picking an option
document.querySelectorAll('[data-share-open]').forEach(function (button) {
  var dialog = button.nextElementSibling;
  if (!dialog || typeof dialog.showModal !== 'function') return;

  button.addEventListener('click', function () {
    dialog.showModal();
  });

  dialog.addEventListener('click', function (e) {
    var r = dialog.getBoundingClientRect();
    var outside = e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    if (e.target === dialog && outside) dialog.close();
  });

  dialog.querySelectorAll('.share-options a').forEach(function (link) {
    link.addEventListener('click', function () {
      dialog.close();
    });
  });
});
