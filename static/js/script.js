(function () {
  var overlays = document.querySelectorAll('.modal-overlay');

  var siteHeader = document.querySelector('.site-header');
  var siteHeaderParent = siteHeader.parentNode;
  var siteHeaderNextSibling = siteHeader.nextSibling;

  function navLinksFor(overlayId) {
    return document.querySelectorAll('[data-open-modal="' + overlayId + '"]');
  }

  function openModal(overlay) {
    overlays.forEach(function (other) {
      if (other !== overlay && other.classList.contains('active')) closeModal(other);
    });
    overlay.classList.add('active');
    document.body.classList.add(overlay.id + '-active');
    document.body.style.overflow = 'hidden';
    navLinksFor(overlay.id).forEach(function (link) { link.classList.add('current'); });
    if (overlay.hasAttribute('data-light-modal')) {
      document.body.classList.add('light-modal-active');
      document.body.appendChild(siteHeader);
    }
  }

  function closeModal(overlay) {
    overlay.classList.remove('active');
    document.body.classList.remove(overlay.id + '-active');
    document.body.style.overflow = '';
    navLinksFor(overlay.id).forEach(function (link) { link.classList.remove('current'); });
    if (overlay.hasAttribute('data-light-modal')) {
      document.body.classList.remove('light-modal-active');
      siteHeaderParent.insertBefore(siteHeader, siteHeaderNextSibling);
    }
  }

  document.querySelectorAll('[data-open-modal]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var overlay = document.getElementById(btn.getAttribute('data-open-modal'));
      if (overlay) openModal(overlay);
    });
  });

  overlays.forEach(function (overlay) {
    overlay.querySelectorAll('.modal-close').forEach(function (btn) {
      btn.addEventListener('click', function () { closeModal(overlay); });
    });
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal(overlay);
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    overlays.forEach(function (overlay) {
      if (overlay.classList.contains('active')) closeModal(overlay);
    });
  });

  var menuToggle = document.getElementById('menu-toggle');
  var siteNav = document.getElementById('site-nav');

  menuToggle.addEventListener('click', function () {
    var isOpen = siteNav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  siteNav.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      siteNav.classList.remove('open');
      menuToggle.setAttribute('aria-expanded', 'false');
    });
  });

  var waitlistForm = document.getElementById('waitlist-form');
  var waitlistHeaderText = document.getElementById('waitlist-header-text');
  waitlistForm.addEventListener('submit', function (e) {
    e.preventDefault();
    waitlistHeaderText.style.display = 'none';
    var success = document.createElement('div');
    success.className = 'form-success';
    success.innerHTML =
      '<svg class="success-check-icon" width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">' +
      '<circle class="success-circle" cx="30" cy="30" r="26"/>' +
      '<path class="success-tick" d="M18 31 L26 39 L42 21" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>' +
      '</svg>' +
      '<p>You\'re on the list! We\'ll email you the moment Dott Health launches.</p>';
    waitlistForm.replaceWith(success);
  });
})();
