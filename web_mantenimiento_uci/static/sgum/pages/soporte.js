/* SGUM-UCI · Soporte (solicitar, bandeja y conversación).
   Sin dependencias (usa window.SGUM y bootstrap si existen). Atributos que activan cada parte:
     data-so-counter="id-del-textarea"   caja con [data-so-count] (cifra) y [data-so-status] (aviso hablado al acercarse al límite)
     data-so-delete="id-del-formulario"  botón «Eliminar seleccionadas»; data-so-modal="id-del-modal"
     data-so-composer + data-so-draft    formulario de mensaje: conserva lo escrito si algo falla o si se sale de la página
   El borrador vive en sessionStorage (esta pestaña) para no dejar texto en equipos compartidos. */
(function () {
  'use strict';

  var store = {
    get: function (k) { try { return window.sessionStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.sessionStorage.setItem(k, v); } catch (e) { /* sin almacenamiento: no pasa nada */ } },
    del: function (k) { try { window.sessionStorage.removeItem(k); } catch (e) { /* ídem */ } }
  };
  function norm(s) { return String(s || '').replace(/\r\n/g, '\n').trim(); }
  function toast(msg, kind) { if (window.SGUM) { window.SGUM.toast(msg, { kind: kind || 'info' }); } }

  /* ---------- Contador de caracteres ----------
     El servidor cuenta cada salto de línea como 2 caracteres (CRLF) y el navegador como 1:
     se resta al maxlength para que lo que el navegador acepta también lo acepte el servidor. */
  function setupCounter(box) {
    var ta = document.getElementById(box.getAttribute('data-so-counter'));
    var out = box.querySelector('[data-so-count]');
    var status = box.querySelector('[data-so-status]');
    if (!ta || !out) { return; }
    var max = parseInt(ta.getAttribute('data-max') || ta.getAttribute('maxlength'), 10) || 0;
    var announced = false;
    function update() {
      var breaks = (ta.value.match(/\n/g) || []).length;
      var used = ta.value.length + breaks;
      if (max) { ta.maxLength = Math.max(1, max - breaks); }
      out.textContent = used;
      var near = max && used >= max * 0.9;
      box.classList.toggle('is-near', !!near);
      if (status) {
        if (near && !announced) { status.textContent = 'Le quedan ' + Math.max(0, max - used) + ' caracteres.'; announced = true; }
        if (!near) { status.textContent = ''; announced = false; }
      }
    }
    ta.addEventListener('input', update);
    ta.addEventListener('so:refresh', update);
    update();
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-so-counter]'), setupCounter);

  /* ---------- Eliminar seleccionadas: avisa si no hay nada marcado; si lo hay, abre la confirmación ---------- */
  document.addEventListener('click', function (e) {
    var btn = e.target && e.target.closest ? e.target.closest('[data-so-delete]') : null;
    if (!btn) { return; }
    var form = document.getElementById(btn.getAttribute('data-so-delete'));
    var modal = document.getElementById(btn.getAttribute('data-so-modal'));
    if (!form || !modal) { return; }
    var n = form.querySelectorAll('input[name="ids"]:checked').length;
    if (!n) { toast('Marque al menos una solicitud para eliminar.', 'warn'); return; }
    var title = modal.querySelector('.modal-title');
    var lead = modal.querySelector('[id$="-body"] p');
    if (title) { title.textContent = n === 1 ? '¿Eliminar la solicitud seleccionada?' : '¿Eliminar las ' + n + ' solicitudes seleccionadas?'; }
    if (lead) { lead.textContent = n === 1 ? 'Se borrará la solicitud y toda su conversación.' : 'Se borrarán las solicitudes y toda su conversación.'; }
    if (window.bootstrap && window.bootstrap.Modal) { window.bootstrap.Modal.getOrCreateInstance(modal).show(); }
  });

  /* ---------- Mensaje de la conversación: no perder lo escrito ----------
     Enter añade una línea (es un textarea); el envío es solo con el botón.
     Al enviar se guarda el texto; si al volver a cargar la página el mensaje no figura entre los propios, se recupera. */
  var comp = document.querySelector('[data-so-composer]');
  if (comp) {
    var key = comp.getAttribute('data-so-draft');
    var ta = comp.querySelector('textarea');
    var recovered = document.querySelector('[data-so-recovered]');
    var mine = document.querySelectorAll('[data-so-mine]');
    var last = mine.length ? mine[mine.length - 1] : null;
    var draft = store.get(key);
    var wasSent = store.get(key + ':sent') === '1';
    store.del(key + ':sent');

    if (draft && ta) {
      if (wasSent && last && norm(last.getAttribute('data-texto')) === norm(draft)) {
        store.del(key);
        toast('Mensaje enviado.', 'ok');
        last.scrollIntoView({ block: 'center' });
      } else if (!ta.value) {
        ta.value = draft;
        ta.dispatchEvent(new Event('so:refresh'));
        if (recovered) { recovered.hidden = false; }
      }
    }
    if (ta) {
      ta.addEventListener('input', function () { if (ta.value) { store.set(key, ta.value); } else { store.del(key); } });
    }
    comp.addEventListener('submit', function (e) {
      if (e.defaultPrevented || !ta) { return; }
      store.set(key, ta.value);
      store.set(key + ':sent', '1');
    });
  }
}());
