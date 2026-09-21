/* SGUM-UCI · campana de notificaciones.
   Contrato (ver .impeccable/agents/backend-contract.md §3.20 y foundation-handoff.md):
     · GET  NOTIFICATIONS_URL              → { items:[{id,message,is_read,created_at,url}], unread_count }
     · POST /notifications/<id>/read/       → { status:'success' }
     · POST /notifications/<id>/delete/     → { status:'success' }   (X-CSRFToken con la variable global csrftoken)
   Marcado: #notificationDropdown es la <ul class="sg-notif__list">; #notificationCount es el contador (sgum.js lo oculta en 0).
   Todo el texto de las notificaciones entra con textContent; nunca con innerHTML.
   Teclado y lector de pantalla: el mensaje es un enlace, «Marcar como leída» y «Eliminar» son botones con nombre propio,
   y una región aria-live dice qué pasó. Sin dependencias (usa window.SGUM y bootstrap si existen). */
(function () {
  'use strict';

  var POLL_MS = 30000;
  var list, countEl, bell, live;
  var state = { items: [], unread: 0, loaded: false, busy: false };

  /* ---------- Estilos propios de la lista (la campana está en todas las páginas y este archivo es su único dueño) ---------- */
  function injectStyles() {
    if (document.getElementById('sgum-notif-css')) { return; }
    var css =
      '.sg-notif__list>li.notification{padding-bottom:var(--sg-s-2)}' +
      '.nt-link{display:block;color:inherit;text-decoration:none;overflow-wrap:anywhere}' +
      '.nt-link:hover{text-decoration:underline;text-underline-offset:.2em}' +
      '.nt-link:focus-visible{outline:2px solid var(--sg-focus);outline-offset:2px}' +
      '.nt-meta{display:flex;flex-wrap:wrap;align-items:center;gap:0 var(--sg-s-1);margin-top:2px}' +
      '.nt-time{margin-right:auto;font-size:var(--sg-fs-xs);color:var(--sg-text-3);white-space:nowrap}' +
      '.sg-notif__list li.read .nt-time{color:var(--sg-text-3)}' +
      '.nt-btn.sg-btn{min-height:2.25rem;padding-inline:var(--sg-s-2);font-size:var(--sg-fs-xs)}' +
      '.nt-btn.sg-btn--icon{width:2.25rem;padding:0}' +
      '@media (pointer:coarse){.nt-btn.sg-btn{min-height:var(--sg-touch)}.nt-btn.sg-btn--icon{width:var(--sg-touch)}}' +
      '.nt-state{display:flex;flex-direction:column;align-items:flex-start;gap:var(--sg-s-1)}' +
      '.nt-state strong{font-weight:var(--sg-fw-semi);color:var(--sg-text)}' +
      '.nt-state span{color:var(--sg-text-3)}' +
      '.nt-skel{display:flex;flex-direction:column;gap:var(--sg-s-2)}';
    var style = document.createElement('style');
    style.id = 'sgum-notif-css';
    style.textContent = css;
    document.head.appendChild(style);
  }

  /* ---------- Utilidades ---------- */
  function el(tag, className, text) {
    var e = document.createElement(tag);
    if (className) { e.className = className; }
    if (text != null) { e.textContent = text; }
    return e;
  }
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
  function toast(message, kind) { if (window.SGUM) { window.SGUM.toast(message, { kind: kind || 'info' }); } }
  function say(message) {
    if (!live) { return; }
    live.textContent = '';
    window.setTimeout(function () { live.textContent = message; }, 40);
  }
  function short(text, n) { text = String(text || ''); return text.length > n ? text.slice(0, n - 1) + '…' : text; }

  /* Solo rutas del propio sitio: empiezan con «/» y no con «//» */
  function safeUrl(url) {
    url = String(url || '');
    return /^\/(?!\/)/.test(url) ? url : '/';
  }

  function formatWhen(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) { return { text: '', title: '' }; }
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    var abs = pad(d.getDate()) + '/' + pad(d.getMonth() + 1) + '/' + d.getFullYear() + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    var diff = Math.round((Date.now() - d.getTime()) / 1000);
    var text = abs;
    if (diff < 45) { text = 'ahora'; }
    else if (diff < 3600) { var m = Math.max(1, Math.round(diff / 60)); text = 'hace ' + m + ' min'; }
    else if (diff < 86400) { var h = Math.round(diff / 3600); text = 'hace ' + h + (h === 1 ? ' hora' : ' horas'); }
    else if (diff < 86400 * 7) { var dd = Math.round(diff / 86400); text = dd === 1 ? 'ayer' : 'hace ' + dd + ' días'; }
    return { text: text, title: abs };
  }

  /* ---------- Contador de la campana ---------- */
  function setCount(n) {
    state.unread = Math.max(0, n | 0);
    if (countEl) { countEl.textContent = state.unread > 99 ? '99+' : String(state.unread); }
  }

  /* ---------- Estados de la lista ---------- */
  function clearList() { while (list.firstChild) { list.removeChild(list.firstChild); } }

  function showLoading() {
    clearList();
    list.setAttribute('aria-busy', 'true');
    var li = el('li', 'text-muted');
    var box = el('div', 'nt-skel');
    box.setAttribute('role', 'status');
    box.appendChild(el('span', 'sg-visually-hidden', 'Cargando notificaciones…'));
    box.appendChild(el('span', 'sg-skeleton sg-skeleton--text'));
    box.appendChild(el('span', 'sg-skeleton sg-skeleton--short'));
    li.appendChild(box);
    list.appendChild(li);
  }

  function showEmpty() {
    clearList();
    list.removeAttribute('aria-busy');
    var li = el('li', 'text-muted');
    var box = el('div', 'nt-state');
    box.appendChild(el('strong', null, 'No hay notificaciones'));
    box.appendChild(el('span', null, 'Aquí verá los avisos sobre sus incidencias y solicitudes de soporte.'));
    li.appendChild(box);
    list.appendChild(li);
  }

  function showError(message, sessionExpired) {
    clearList();
    list.removeAttribute('aria-busy');
    var li = el('li', 'text-muted');
    var box = el('div', 'nt-state');
    box.setAttribute('role', 'alert');
    box.appendChild(el('strong', null, sessionExpired ? 'Su sesión expiró' : 'No se pudieron cargar las notificaciones'));
    box.appendChild(el('span', null, message));
    if (sessionExpired) {
      var a = el('a', 'sg-btn sg-btn--secondary sg-btn--sm', 'Iniciar sesión');
      a.href = '/?next=' + encodeURIComponent(location.pathname + location.search);
      box.appendChild(a);
    } else {
      var retry = el('button', 'sg-btn sg-btn--secondary sg-btn--sm', 'Reintentar');
      retry.type = 'button';
      retry.setAttribute('data-nt-retry', '');
      box.appendChild(retry);
    }
    li.appendChild(box);
    list.appendChild(li);
  }

  /* ---------- Una notificación ---------- */
  function buildItem(n) {
    var li = el('li', 'notification' + (n.is_read ? ' read' : ''));
    li.setAttribute('data-id', String(n.id));

    var link = el('a', 'nt-link');
    link.href = safeUrl(n.url);
    link.setAttribute('data-nt-open', '');
    if (!n.is_read) { link.appendChild(el('span', 'sg-visually-hidden', 'Sin leer: ')); }
    link.appendChild(document.createTextNode(n.message));
    li.appendChild(link);

    var meta = el('div', 'nt-meta');
    var when = formatWhen(n.created_at);
    if (when.text) {
      var t = el('time', 'nt-time sg-mono', when.text);
      t.setAttribute('datetime', n.created_at);
      if (when.title) { t.title = when.title; }
      meta.appendChild(t);
    }
    if (!n.is_read) {
      var read = el('button', 'sg-btn sg-btn--ghost sg-btn--sm nt-btn', 'Marcar como leída');
      read.type = 'button';
      read.setAttribute('data-nt-read', '');
      read.setAttribute('data-loading-label', 'Marcando…');
      read.setAttribute('aria-label', 'Marcar como leída: ' + short(n.message, 60));
      meta.appendChild(read);
    }
    var del = el('button', 'sg-btn sg-btn--ghost sg-btn--icon sg-btn--sm nt-btn');
    del.type = 'button';
    del.setAttribute('data-nt-delete', '');
    del.setAttribute('aria-label', 'Eliminar la notificación: ' + short(n.message, 60));
    del.title = 'Eliminar';
    del.appendChild(icon('trash'));
    meta.appendChild(del);
    li.appendChild(meta);
    return li;
  }

  function render() {
    list.removeAttribute('aria-busy');
    clearList();
    if (!state.items.length) { showEmpty(); return; }
    state.items.forEach(function (n) { list.appendChild(buildItem(n)); });
  }

  /* Datos: la forma nueva (items) y, por si el servidor aún envía solo la antigua, la serializada de Django */
  function normalize(data) {
    if (data && Array.isArray(data.items)) { return data.items; }
    try {
      return JSON.parse(data.notifications).map(function (o) {
        return { id: o.pk, message: o.fields.message, is_read: o.fields.is_read, created_at: o.fields.created_at, url: '/' + String(o.fields.urlAsociated || '').replace(/^\/+/, '') };
      });
    } catch (e) { return []; }
  }

  /* ---------- Carga ---------- */
  function load(opts) {
    opts = opts || {};
    if (state.busy || typeof NOTIFICATIONS_URL === 'undefined') { return; }
    state.busy = true;
    if (!state.loaded && !opts.silent) { showLoading(); }
    fetch(NOTIFICATIONS_URL, { credentials: 'same-origin', headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (res) {
        if (res.status === 401) { var e = new Error('sesion'); e.expired = true; throw e; }
        if (!res.ok) { throw new Error('http ' + res.status); }
        return res.json();
      })
      .then(function (data) {
        state.busy = false;
        state.items = normalize(data);
        state.loaded = true;
        var unread = typeof data.unread_count === 'number' ? data.unread_count : state.items.filter(function (n) { return !n.is_read; }).length;
        setCount(unread);
        // No se vuelve a dibujar la lista mientras el foco está dentro de ella: se perdería el lugar del usuario.
        if (list.contains(document.activeElement) && document.activeElement !== list) { return; }
        render();
      })
      .catch(function (err) {
        state.busy = false;
        if (err && err.expired) { showError('Vuelva a iniciar sesión para ver sus notificaciones.', true); return; }
        // Una actualización en segundo plano que falla no borra lo que ya se ve.
        if (state.loaded && opts.silent) { return; }
        showError('Compruebe su conexión a la red e inténtelo de nuevo.', false);
      });
  }

  /* ---------- Acciones ---------- */
  function post(path) {
    return fetch(path, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'X-CSRFToken': typeof csrftoken !== 'undefined' ? csrftoken : '', 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
    }).then(function (res) {
      if (res.status === 401) { var e = new Error('sesion'); e.expired = true; throw e; }
      return res.json().catch(function () { return {}; }).then(function (body) {
        if (!res.ok || body.status !== 'success') { throw new Error(body.message || ('http ' + res.status)); }
        return body;
      });
    });
  }

  function findItem(id) {
    for (var i = 0; i < state.items.length; i++) { if (String(state.items[i].id) === String(id)) { return state.items[i]; } }
    return null;
  }

  function failure(err, what) {
    if (err && err.expired) { toast('Su sesión expiró. Vuelva a iniciar sesión.', 'danger'); return; }
    toast('No se pudo ' + what + '. Compruebe su conexión e inténtelo de nuevo.', 'danger');
  }

  function markRead(li, btn) {
    var id = li.getAttribute('data-id');
    var item = findItem(id);
    if (btn && window.SGUM) { window.SGUM.loading(btn, true); btn.disabled = true; }
    post('/notifications/' + encodeURIComponent(id) + '/read/').then(function () {
      if (item && !item.is_read) { item.is_read = true; setCount(state.unread - 1); }
      li.classList.add('read');
      var hidden = li.querySelector('.nt-link > .sg-visually-hidden');
      if (hidden) { hidden.parentNode.removeChild(hidden); }
      var focusBack = btn && btn === document.activeElement;
      if (btn && btn.parentNode) { btn.parentNode.removeChild(btn); }
      if (focusBack) { var next = li.querySelector('[data-nt-delete]') || li.querySelector('[data-nt-open]'); if (next) { next.focus(); } }
      say('Notificación marcada como leída.');
    }).catch(function (err) {
      if (btn && window.SGUM) { btn.disabled = false; window.SGUM.loading(btn, false); }
      failure(err, 'marcar la notificación como leída');
    });
  }

  function remove(li, btn) {
    var id = li.getAttribute('data-id');
    var item = findItem(id);
    if (btn) { btn.disabled = true; btn.setAttribute('aria-busy', 'true'); }
    post('/notifications/' + encodeURIComponent(id) + '/delete/').then(function () {
      if (item) {
        if (!item.is_read) { setCount(state.unread - 1); }
        state.items.splice(state.items.indexOf(item), 1);
      }
      var sibling = li.nextElementSibling || li.previousElementSibling;
      var hadFocus = li.contains(document.activeElement);
      li.parentNode.removeChild(li);
      if (!state.items.length) { showEmpty(); if (hadFocus && bell) { bell.focus(); } }
      else if (hadFocus && sibling) { var f = sibling.querySelector('[data-nt-open]'); if (f) { f.focus(); } }
      say('Notificación eliminada.');
    }).catch(function (err) {
      if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
      failure(err, 'eliminar la notificación');
    });
  }

  function onListClick(e) {
    var t = e.target;
    if (!t || !t.closest) { return; }
    var retry = t.closest('[data-nt-retry]');
    if (retry) { state.loaded = false; load(); return; }
    var li = t.closest('li[data-id]');
    if (!li) { return; }
    var btnRead = t.closest('[data-nt-read]');
    if (btnRead) { markRead(li, btnRead); return; }
    var btnDel = t.closest('[data-nt-delete]');
    if (btnDel) { remove(li, btnDel); return; }
  }

  /* Abrir una notificación la marca como leída (no la elimina) y sigue el enlace normalmente.
     keepalive permite que la petición termine aunque la página cambie. */
  function onOpen(e) {
    var link = e.target && e.target.closest ? e.target.closest('[data-nt-open]') : null;
    if (!link) { return; }
    var li = link.closest('li[data-id]');
    var item = li && findItem(li.getAttribute('data-id'));
    if (!item || item.is_read) { return; }
    item.is_read = true;
    setCount(state.unread - 1);
    li.classList.add('read');
    try {
      fetch('/notifications/' + encodeURIComponent(item.id) + '/read/', {
        method: 'POST', credentials: 'same-origin', keepalive: true,
        headers: { 'X-CSRFToken': typeof csrftoken !== 'undefined' ? csrftoken : '', 'X-Requested-With': 'XMLHttpRequest' }
      });
    } catch (err) { /* si falla, sigue sin leer: no impide abrir la página */ }
  }

  /* ---------- Arranque ---------- */
  function init() {
    list = document.getElementById('notificationDropdown');
    countEl = document.getElementById('notificationCount');
    bell = document.getElementById('notificationBell');
    if (!list) { return; }
    injectStyles();

    // Región que anuncia el resultado de cada acción a los lectores de pantalla
    live = el('div', 'sg-visually-hidden');
    live.setAttribute('role', 'status');
    live.setAttribute('aria-live', 'polite');
    if (list.parentNode) { list.parentNode.appendChild(live); }
    list.setAttribute('role', 'list');

    list.addEventListener('click', onListClick);
    list.addEventListener('click', onOpen);
    list.addEventListener('auxclick', onOpen);

    // Al abrir la campana se pide la lista al momento
    document.addEventListener('show.bs.dropdown', function (e) {
      if (e.target && e.target.id === 'notificationBell') { load({ silent: state.loaded }); }
    });

    load();
    window.setInterval(function () { if (!document.hidden) { load({ silent: true }); } }, POLL_MS);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) { load({ silent: true }); } });
  }

  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); } else { init(); }
}());
