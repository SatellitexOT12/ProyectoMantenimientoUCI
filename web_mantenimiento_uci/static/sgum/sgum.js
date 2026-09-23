/* SGUM-UCI · comportamientos comunes del sistema de diseño «Plano de la UCI».
   Se carga en master.html y login.html (defer). No depende de jQuery.
   API pública: window.SGUM = { toast, showToast, dismiss, loading }.
   Atributos que activan comportamiento (ver .impeccable/agents/foundation-handoff.md):
     data-sg-dismiss            cierra su .sg-alert / .sg-toast
     data-sg-autodismiss="ms"   se cierra solo
     data-sg-loading            formulario: al enviar, el botón de envío pasa a «cargando»
       data-loading-label="…"     texto del botón mientras carga
     data-sg-validate           formulario: valida campos required con mensajes en español dentro de la celda
     data-sg-clear              enlace «limpiar búsqueda» que conserva los demás parámetros
     data-sg-select-all         casilla de cabecera de tabla que marca/desmarca las filas
     data-sg-selected-count     elemento que muestra cuántas filas hay marcadas                */
(function () {
  'use strict';
  if (window.SGUM) { return; }

  var ICONS = { info: 'info', ok: 'check', warn: 'alert', danger: 'alert' };
  var REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function icon(name) {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'sg-icon');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    var use = document.createElementNS(ns, 'use');
    use.setAttribute('href', '#i-' + name);
    svg.appendChild(use);
    return svg;
  }

  /* ---------- Cerrar avisos y toasts ---------- */
  function dismiss(el) {
    if (!el || el.__leaving) { return; }
    el.__leaving = true;
    el.classList.add('is-leaving');
    var remove = function () { if (el.parentNode) { el.parentNode.removeChild(el); } };
    if (REDUCED) { remove(); } else { setTimeout(remove, 220); }
  }

  function autoDismiss(el, ms) {
    if (!ms || ms <= 0) { return; }
    var timer = setTimeout(function () { dismiss(el); }, ms);
    var pause = function () { clearTimeout(timer); };
    var resume = function () { timer = setTimeout(function () { dismiss(el); }, 2000); };
    el.addEventListener('mouseenter', pause);
    el.addEventListener('focusin', pause);
    el.addEventListener('mouseleave', resume);
    el.addEventListener('focusout', resume);
  }

  /* ---------- Toasts ---------- */
  function region() {
    var r = document.getElementById('sg-toasts');
    if (!r) {
      r = document.createElement('div');
      r.id = 'sg-toasts';
      r.className = 'sg-toasts';
      r.setAttribute('role', 'region');
      r.setAttribute('aria-label', 'Avisos');
      document.body.appendChild(r);
    }
    return r;
  }

  /* SGUM.toast('Seleccione al menos una incidencia.', { kind: 'warn', timeout: 6000 })
     kind: 'info' | 'ok' | 'warn' | 'danger'. Errores y advertencias duran más y se leen como alerta. */
  function toast(message, opts) {
    opts = opts || {};
    var kind = opts.kind || 'info';
    var el = document.createElement('div');
    el.className = 'sg-toast sg-toast--' + kind;
    el.setAttribute('role', kind === 'danger' || kind === 'warn' ? 'alert' : 'status');
    el.appendChild(icon(ICONS[kind] || 'info'));
    var body = document.createElement('div');
    body.className = 'sg-toast__body';
    body.textContent = message;
    el.appendChild(body);
    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'btn-close sg-alert__close';
    close.setAttribute('aria-label', 'Cerrar aviso');
    close.addEventListener('click', function () { dismiss(el); });
    el.appendChild(close);
    region().appendChild(el);
    autoDismiss(el, opts.timeout != null ? opts.timeout : (kind === 'danger' || kind === 'warn' ? 8000 : 5000));
    return el;
  }

  /* Muestra un toast declarado en la página con partials/toast.html */
  function showToast(id, timeout) {
    var el = document.getElementById(id);
    if (!el) { return; }
    el.hidden = false;
    el.__leaving = false;
    el.classList.remove('is-leaving');
    region().appendChild(el);
    autoDismiss(el, timeout != null ? timeout : 6000);
  }

  /* Compatibilidad con las páginas antiguas: mostrarToast() abre #toastSeleccionar */
  window.mostrarToast = function () {
    var el = document.getElementById('toastSeleccionar');
    if (!el) { return; }
    if (el.classList.contains('sg-toast')) { showToast('toastSeleccionar'); }
    else if (window.bootstrap && window.bootstrap.Toast) { window.bootstrap.Toast.getOrCreateInstance(el).show(); }
  };

  /* ---------- Estado «cargando» de un botón de envío ---------- */
  function loading(btn, on, label) {
    if (!btn) { return; }
    if (on) {
      if (!btn.hasAttribute('data-label-original')) { btn.setAttribute('data-label-original', btn.innerHTML); }
      btn.classList.add('is-loading');
      btn.setAttribute('aria-busy', 'true');
      var l = label || btn.getAttribute('data-loading-label');
      if (l) { btn.textContent = l; }
    } else {
      btn.classList.remove('is-loading');
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
      if (btn.hasAttribute('data-label-original')) {
        btn.innerHTML = btn.getAttribute('data-label-original');
        btn.removeAttribute('data-label-original');
      }
    }
  }

  window.SGUM = { toast: toast, showToast: showToast, dismiss: dismiss, loading: loading };

  /* ---------- Validación con mensajes en español (data-sg-validate) ---------- */
  function fieldOf(input) { return input.closest('.sg-field'); }

  function setFieldError(input, message) {
    var cell = fieldOf(input);
    input.setAttribute('aria-invalid', 'true');
    if (!cell) { return; }
    cell.classList.add('is-error');
    var msg = cell.querySelector('.sg-field__msg[data-sg-generated]');
    if (!msg) {
      msg = document.createElement('p');
      msg.className = 'sg-field__msg';
      msg.setAttribute('data-sg-generated', '');
      msg.setAttribute('role', 'alert');
      msg.appendChild(icon('alert'));
      msg.appendChild(document.createElement('span'));
      msg.id = (input.id || 'campo') + '-msg';
      cell.appendChild(msg);
      input.setAttribute('aria-describedby', msg.id);
    }
    msg.lastChild.textContent = message;
  }

  function clearFieldError(input) {
    input.removeAttribute('aria-invalid');
    var cell = fieldOf(input);
    if (!cell) { return; }
    var msg = cell.querySelector('.sg-field__msg[data-sg-generated]');
    if (msg) { msg.parentNode.removeChild(msg); input.removeAttribute('aria-describedby'); }
    if (!cell.querySelector('.sg-field__msg')) { cell.classList.remove('is-error'); }
  }

  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!(form instanceof HTMLFormElement)) { return; }
    if (form.hasAttribute('data-sg-validate')) {
      var first = null;
      var inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
      Array.prototype.forEach.call(inputs, function (input) {
        var empty = (input.type === 'checkbox' || input.type === 'radio') ? !input.checked : !String(input.value).trim();
        if (empty) {
          var label = input.getAttribute('data-msg-required');
          if (!label) {
            var cell = fieldOf(input);
            var lab = cell && cell.querySelector('.sg-field__label span');
            label = lab ? 'Escriba ' + (input.tagName === 'SELECT' ? 'o elija ' : '') + 'su ' + lab.textContent.trim().toLowerCase() + '.' : 'Complete este campo.';
            if (input.tagName === 'SELECT') { label = 'Elija una opción.'; }
          }
          setFieldError(input, label);
          if (!first) { first = input; }
        } else { clearFieldError(input); }
      });
      if (first) { e.preventDefault(); first.focus(); return; }
    }
    if (form.hasAttribute('data-sg-loading') && !e.defaultPrevented) {
      var btn = e.submitter || form.querySelector('button[type="submit"], input[type="submit"]');
      if (btn && !btn.hasAttribute('data-sg-no-loading')) {
        // Se deshabilita después del envío para no perder el name/value del botón
        setTimeout(function () { loading(btn, true); btn.disabled = true; }, 0);
      }
    }
  }, true);

  document.addEventListener('input', function (e) {
    var t = e.target;
    if (t && t.getAttribute && t.getAttribute('aria-invalid') === 'true' && t.closest('form[data-sg-validate]')) { clearFieldError(t); }
  });

  /* Al volver con «Atrás» el navegador puede restaurar la página con el botón en «cargando» */
  window.addEventListener('pageshow', function (e) {
    if (!e.persisted) { return; }
    Array.prototype.forEach.call(document.querySelectorAll('.is-loading[data-label-original]'), function (b) { loading(b, false); });
  });

  /* ---------- Clics delegados ---------- */
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest) { return; }

    var d = t.closest('[data-sg-dismiss]');
    if (d) { dismiss(d.closest('.sg-alert, .sg-toast')); return; }

    var clear = t.closest('[data-sg-clear]');
    if (clear) {
      var form = clear.closest('form');
      if (form) {
        e.preventDefault();
        var q = form.querySelector('input[name="q"]');
        if (q) { q.value = ''; }
        if (form.requestSubmit) { form.requestSubmit(); } else { form.submit(); }
      }
      return;
    }

    // Toda la celda de cajetín es objetivo de clic: enfoca su control
    var cell = t.closest('.sg-field');
    if (cell && !t.closest('button, a, input, select, textarea, label')) {
      var ctl = cell.querySelector('input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), select, textarea');
      if (ctl && !ctl.disabled) { ctl.focus(); }
    }
  });

  /* ---------- Selección de filas en tablas .sg-table ---------- */
  function updateSelection(table) {
    var rows = table.querySelectorAll('tbody input[type="checkbox"]:not([data-sg-select-all])');
    var checked = 0;
    Array.prototype.forEach.call(rows, function (cb) {
      var tr = cb.closest('tr');
      if (tr) { tr.classList.toggle('is-selected', cb.checked); }
      if (cb.checked) { checked++; }
    });
    var all = table.querySelector('[data-sg-select-all]');
    if (all) {
      all.checked = rows.length > 0 && checked === rows.length;
      all.indeterminate = checked > 0 && checked < rows.length;
    }
    Array.prototype.forEach.call(document.querySelectorAll('[data-sg-selected-count]'), function (el) { el.textContent = checked; });
  }

  document.addEventListener('change', function (e) {
    var t = e.target;
    if (!t || !t.matches || !t.matches('input[type="checkbox"]')) { return; }
    var table = t.closest('table');
    if (!table) { return; }
    if (t.hasAttribute('data-sg-select-all')) {
      Array.prototype.forEach.call(table.querySelectorAll('tbody input[type="checkbox"]'), function (cb) { if (!cb.disabled) { cb.checked = t.checked; } });
    }
    updateSelection(table);
  });

  /* ---------- Campana: el contador se oculta en cero y el nombre accesible lo dice ---------- */
  function watchBell() {
    var count = document.getElementById('notificationCount');
    var bell = document.getElementById('notificationBell');
    if (!count) { return; }
    var sync = function () {
      var n = parseInt(count.textContent, 10);
      var has = !isNaN(n) && n > 0;
      count.hidden = !has;
      if (bell) { bell.setAttribute('aria-label', has ? 'Notificaciones, ' + n + (n === 1 ? ' sin leer' : ' sin leer') : 'Notificaciones'); }
    };
    sync();
    if (window.MutationObserver) {
      new MutationObserver(sync).observe(count, { childList: true, characterData: true, subtree: true });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('[data-sg-autodismiss]'), function (el) {
      autoDismiss(el, parseInt(el.getAttribute('data-sg-autodismiss'), 10));
    });
    watchBell();
    Array.prototype.forEach.call(document.querySelectorAll('.sg-table'), updateSelection);
  });
}());
