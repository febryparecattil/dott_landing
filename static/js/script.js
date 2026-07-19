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
    if (overlay.id === 'register-overlay') resetRegisterModal();
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
    if (overlay.id === 'register-overlay') return; // Register must not close on backdrop click
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
  var waitlistSubmitButton = waitlistForm.querySelector('button[type="submit"]');
  var originalSubmitLabel = waitlistSubmitButton.textContent;

  waitlistForm.addEventListener('submit', function (e) {
    e.preventDefault();

    var formData = new FormData(waitlistForm);
    var payload = {
      name: formData.get('name') || '',
      email: formData.get('email') || '',
      phone: formData.get('phone') || ''
    };

    waitlistSubmitButton.disabled = true;
    waitlistSubmitButton.textContent = 'Submitting...';

    fetch('/join-waitlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok) throw new Error(data.message || 'Submission failed');
          return data;
        });
      })
      .then(function (data) {
        waitlistHeaderText.style.display = 'none';
        var success = document.createElement('div');
        success.className = 'form-success';
        success.innerHTML =
          '<svg class="success-check-icon" width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">' +
          '<circle class="success-circle" cx="30" cy="30" r="26"/>' +
          '<path class="success-tick" d="M18 31 L26 39 L42 21" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>' +
          '</svg>' +
          '<p>' + (data.message || 'You\'re on the list! We\'ll email you the moment Dott Health launches.') + '</p>';
        waitlistForm.replaceWith(success);
      })
      .catch(function (error) {
        waitlistSubmitButton.disabled = false;
        waitlistSubmitButton.textContent = originalSubmitLabel;
        var errorNote = document.createElement('p');
        errorNote.className = 'modal-note';
        errorNote.textContent = error.message || 'Unable to submit right now. Please try again.';
        waitlistForm.appendChild(errorNote);
      });
  });

  var registerBody = document.getElementById('register-body');
  var registerFadeTop = registerBody.querySelector('.register-body-fade-top');

  function updateRegisterFades() {
    var atTop = registerBody.scrollTop <= 0;
    registerFadeTop.classList.toggle('visible', !atTop);
  }
  registerBody.addEventListener('scroll', updateRegisterFades);
  if (window.ResizeObserver) {
    new ResizeObserver(updateRegisterFades).observe(registerBody.querySelector('#register-form-wrap'));
  }

  var registerHeaderText = document.getElementById('register-header-copy');
  var registerFormWrap = document.getElementById('register-form-wrap');
  var registerSuccess = document.getElementById('register-success');
  var professionOptions = document.getElementById('profession-options');
  var registerExpand = document.getElementById('register-expand');
  var registerForm = document.getElementById('register-form');
  var regMobileInput = document.getElementById('reg-mobile');
  var doctorFields = document.getElementById('doctor-only-fields');
  var nurseFields = document.getElementById('nurse-only-fields');

  var requiredByProfession = {
    doctor: ['reg-license', 'reg-qualification'],
    nurse: ['reg-license-nurse'],
  };

  regMobileInput.addEventListener('input', function () {
    regMobileInput.value = regMobileInput.value.replace(/\D/g, '').slice(0, 10);
  });

  function setRequiredFields(profession) {
    Object.keys(requiredByProfession).forEach(function (key) {
      var isActive = key === profession;
      requiredByProfession[key].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.required = isActive;
      });
    });
  }

  professionOptions.querySelectorAll('.profession-option').forEach(function (btn) {
    btn.addEventListener('click', function () {
      professionOptions.querySelectorAll('.profession-option').forEach(function (b) {
        b.classList.remove('selected');
      });
      btn.classList.add('selected');
      var profession = btn.getAttribute('data-profession');
      doctorFields.hidden = profession !== 'doctor';
      nurseFields.hidden = profession !== 'nurse';
      setRequiredFields(profession);
      registerExpand.classList.add('expanded');
    });
  });

  function positionDropdownPanel(trigger, panel) {
    var scrollAncestor = trigger.closest('.register-body') || document.body;
    var triggerRect = trigger.getBoundingClientRect();
    var boundsRect = scrollAncestor.getBoundingClientRect();
    var margin = 8;
    var spaceBelow = boundsRect.bottom - triggerRect.bottom - margin;
    var spaceAbove = triggerRect.top - boundsRect.top - margin;
    var defaultMaxHeight = 240;
    var panelHeight = panel.scrollHeight;
    var flip = panelHeight > spaceBelow && spaceAbove > spaceBelow;
    panel.classList.toggle('flip-up', flip);
    var available = flip ? spaceAbove : spaceBelow;
    panel.style.maxHeight = Math.max(120, Math.min(defaultMaxHeight, available)) + 'px';
  }

  var multiSelects = [];
  document.querySelectorAll('.multi-select').forEach(function (root) {
    var trigger = root.querySelector('.multi-select-trigger');
    var triggerText = trigger.querySelector('.multi-select-trigger-text');
    var panel = root.querySelector('.multi-select-panel');
    var hiddenInput = root.querySelector('input[type="hidden"]');
    var placeholderText = triggerText.textContent;

    trigger.addEventListener('click', function () {
      var willOpen = panel.hidden;
      document.querySelectorAll('.single-select .multi-select-panel, .multi-select .multi-select-panel').forEach(function (p) {
        p.hidden = true;
      });
      panel.hidden = !willOpen;
      if (willOpen) positionDropdownPanel(trigger, panel);
    });
    document.addEventListener('click', function (e) {
      if (!root.contains(e.target)) panel.hidden = true;
    });
    var maxVisibleItems = 2;
    panel.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
      cb.addEventListener('change', function () {
        var selected = Array.prototype.slice
          .call(panel.querySelectorAll('input[type="checkbox"]:checked'))
          .map(function (c) { return c.value; });
        hiddenInput.value = selected.join(',');
        if (selected.length === 0) {
          triggerText.textContent = placeholderText;
          trigger.setAttribute('data-placeholder', 'true');
          trigger.removeAttribute('title');
        } else {
          var visible = selected.slice(0, maxVisibleItems).join(', ');
          var remaining = selected.length - maxVisibleItems;
          triggerText.textContent = remaining > 0 ? visible + ' +' + remaining : visible;
          trigger.setAttribute('title', selected.join(', '));
          trigger.removeAttribute('data-placeholder');
        }
      });
    });

    multiSelects.push({
      panel: panel,
      trigger: trigger,
      triggerText: triggerText,
      hiddenInput: hiddenInput,
      placeholderText: placeholderText,
    });
  });

  var singleSelects = [];
  document.querySelectorAll('.single-select').forEach(function (root) {
    var trigger = root.querySelector('.multi-select-trigger');
    var triggerText = trigger.querySelector('.multi-select-trigger-text');
    var panel = root.querySelector('.multi-select-panel');
    var hiddenInput = root.querySelector('input[type="hidden"]');
    var placeholderText = triggerText.textContent;

    trigger.addEventListener('click', function () {
      var willOpen = panel.hidden;
      document.querySelectorAll('.single-select .multi-select-panel, .multi-select .multi-select-panel').forEach(function (p) {
        p.hidden = true;
      });
      panel.hidden = !willOpen;
      if (willOpen) positionDropdownPanel(trigger, panel);
    });
    document.addEventListener('click', function (e) {
      if (!root.contains(e.target)) panel.hidden = true;
    });
    panel.querySelectorAll('.multi-select-item').forEach(function (item) {
      item.addEventListener('click', function () {
        panel.querySelectorAll('.multi-select-item').forEach(function (i) { i.classList.remove('selected'); });
        item.classList.add('selected');
        hiddenInput.value = item.getAttribute('data-value');
        triggerText.textContent = item.textContent;
        trigger.removeAttribute('data-placeholder');
        panel.hidden = true;
      });
    });

    singleSelects.push({
      panel: panel,
      trigger: trigger,
      triggerText: triggerText,
      hiddenInput: hiddenInput,
      placeholderText: placeholderText,
    });
  });

  registerForm.addEventListener('submit', function (e) {
    e.preventDefault();
    registerHeaderText.style.display = 'none';
    registerFormWrap.hidden = true;
    registerSuccess.hidden = false;
  });

  function resetRegisterModal() {
    setTimeout(function () {
      registerSuccess.hidden = true;
      registerFormWrap.hidden = false;
      registerHeaderText.style.display = '';
      registerForm.reset();
      professionOptions.querySelectorAll('.profession-option').forEach(function (b) {
        b.classList.remove('selected');
      });
      registerExpand.classList.remove('expanded');
      doctorFields.hidden = true;
      nurseFields.hidden = true;
      multiSelects.forEach(function (m) {
        m.hiddenInput.value = '';
        m.triggerText.textContent = m.placeholderText;
        m.trigger.setAttribute('data-placeholder', 'true');
        m.trigger.removeAttribute('title');
        m.panel.querySelectorAll('input[type="checkbox"]').forEach(function (cb) { cb.checked = false; });
        m.panel.hidden = true;
      });
      singleSelects.forEach(function (s) {
        s.hiddenInput.value = '';
        s.triggerText.textContent = s.placeholderText;
        s.trigger.setAttribute('data-placeholder', 'true');
        s.panel.querySelectorAll('.multi-select-item.selected').forEach(function (i) { i.classList.remove('selected'); });
        s.panel.hidden = true;
      });
    }, 200);
  }
})();
