/* SGUM-UCI · mostrar/ocultar contraseña y aviso de Bloq Mayús.
   Cargado por master.html y login.html (el archivo se llama «togglepassword.js», todo en minúsculas).
   Uso:
     <input type="password" id="password" ...>
     <button type="button" data-sg-toggle-password aria-controls="password" aria-pressed="false" aria-label="Mostrar contraseña">
       <svg data-icon-show>…ojo…</svg>  <svg data-icon-hide hidden>…ojo tachado…</svg>
     </button>
     <p data-sg-caps-for="password" hidden>Bloq Mayús está activado.</p>          (opcional) */
(function () {
  'use strict';

  function fieldInput(btn) {
    var id = btn.getAttribute('aria-controls');
    if (id) { return document.getElementById(id); }
    var cell = btn.closest('.sg-field, .input-group');
    return cell ? cell.querySelector('input[type="password"], input[type="text"]') : null;
  }

  function setVisible(btn, input, show) {
    input.type = show ? 'text' : 'password';
    btn.setAttribute('aria-pressed', show ? 'true' : 'false');
    btn.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
    Array.prototype.forEach.call(btn.querySelectorAll('[data-icon-show]'), function (el) { el.hidden = show; });
    Array.prototype.forEach.call(btn.querySelectorAll('[data-icon-hide]'), function (el) { el.hidden = !show; });
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('[data-sg-toggle-password], #togglePassword') : null;
    if (!btn) { return; }
    var input = fieldInput(btn) || document.getElementById('password');
    if (!input) { return; }
    var show = input.type === 'password';
    setVisible(btn, input, show);
    input.focus();
  });

  function capsHint(e) {
    var t = e.target;
    if (!t || t.type !== 'password' || !e.getModifierState) { return; }
    var hint = document.querySelector('[data-sg-caps-for="' + t.id + '"]');
    if (hint) { hint.hidden = !e.getModifierState('CapsLock'); }
  }
  document.addEventListener('keydown', capsHint);
  document.addEventListener('keyup', capsHint);
  document.addEventListener('focusout', function (e) {
    var t = e.target;
    if (t && t.type === 'password') {
      var hint = document.querySelector('[data-sg-caps-for="' + t.id + '"]');
      if (hint) { hint.hidden = true; }
    }
  });
}());
