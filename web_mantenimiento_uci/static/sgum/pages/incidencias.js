/* SGUM-UCI · lista de incidencias.
   Detalle desplegable por fila, barra de selección, confirmaciones, validación de materiales y filtros en móvil.
   Solo mejora la página: los formularios envían por POST aunque este archivo no cargue.
   No usa innerHTML; todo texto se escribe con textContent. */
(function () {
  'use strict';

  var STORE = 'sgum-inc-abierta';
  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };
  var table = $('#inc-table');

  /* ---------- Detalle desplegable ---------- */
  function setOpen(id, open, section) {
    var panel = document.getElementById('inc-' + id + '-detalle');
    var row = document.getElementById('inc-' + id);
    if (!panel) { return; }
    panel.hidden = !open;
    if (row) { row.classList.toggle('is-open', open); }
    $$('[data-inc-toggle="' + id + '"]').forEach(function (b) { b.setAttribute('aria-expanded', open ? 'true' : 'false'); });
    if (open && section) {
      var box = document.getElementById('inc-' + id + '-' + section);
      var target = box && (box.querySelector('input[type="radio"]:not(:disabled)') || box.querySelector('select, input:not([type="hidden"]):not(:disabled), button:not(:disabled)'));
      if (target) { target.focus(); }
    }
  }

  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target.closest('[data-inc-toggle]') : null;
    if (!t) { return; }
    var id = t.getAttribute('data-inc-toggle');
    var panel = document.getElementById('inc-' + id + '-detalle');
    if (!panel) { return; }
    var section = t.getAttribute('data-inc-focus');
    setOpen(id, section ? true : panel.hidden, section);
  });

  // Al enviar una acción desde un detalle, se recuerda cuál era para volver a abrirlo tras la redirección
  document.addEventListener('submit', function (e) {
    if (e.defaultPrevented || !e.target.closest) { return; }
    var d = e.target.closest('.inc-detail');
    if (!d) { return; }
    var m = /^inc-(\d+)-detalle$/.exec(d.id);
    if (m) { try { sessionStorage.setItem(STORE, m[1]); } catch (err) { /* sin almacenamiento */ } }
  });

  try {
    var recordada = sessionStorage.getItem(STORE);
    sessionStorage.removeItem(STORE);
    if (recordada) { setOpen(recordada, true); }
  } catch (err) { /* sin almacenamiento */ }

  /* ---------- Selección múltiple ---------- */
  var bulk = $('#inc-bulk');

  if (table && !$('input[name="ids"]', table)) { table.classList.add('is-sin-casillas'); }
  if (table && !$('tbody .sg-col-check > *', table)) { table.classList.add('is-sin-seleccion'); }

  function seleccionadas() { return $$('input[name="ids"]:checked').length; }

  function actualizarBarra() {
    if (!bulk) { return; }
    var n = seleccionadas();
    bulk.hidden = n === 0;
    var num = $('[data-inc-bulk-n]', bulk);
    var txt = $('[data-inc-bulk-txt]', bulk);
    if (num) { num.textContent = n; }
    if (txt) { txt.textContent = n === 1 ? 'seleccionada' : 'seleccionadas'; }
  }

  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t && t.matches && (t.matches('input[name="ids"]') || t.hasAttribute('data-sg-select-all'))) {
      // sgum.js aplica «marcar todas» en su propio manejador; se lee el resultado después
      setTimeout(actualizarBarra, 0);
    }
  });

  var limpiar = $('[data-inc-bulk-clear]');
  if (limpiar) {
    limpiar.addEventListener('click', function () {
      var all = $('[data-sg-select-all]');
      if (all) {
        all.checked = false;
        all.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        $$('input[name="ids"]').forEach(function (cb) { cb.checked = false; });
      }
      setTimeout(actualizarBarra, 0);
    });
  }

  /* ---------- Confirmaciones ---------- */
  document.addEventListener('show.bs.modal', function (e) {
    var modal = e.target;
    if (!modal || !modal.id) { return; }

    if (modal.id === 'eliminarIncidencias') {
      var n = seleccionadas();
      var titulo = $('#eliminarIncidencias-title');
      if (titulo) { titulo.textContent = n === 1 ? '¿Eliminar la incidencia seleccionada?' : '¿Eliminar las ' + n + ' incidencias seleccionadas?'; }
    }

    if (modal.id === 'quitarTecnico' && e.relatedTarget) {
      var b = e.relatedTarget;
      var form = $('#quitarTecnico-form');
      if (form) { form.setAttribute('action', b.getAttribute('data-action') || ''); }
      var num = b.getAttribute('data-incidencia');
      var tec = b.getAttribute('data-tecnico');
      var titulo2 = $('#quitarTecnico-title');
      if (titulo2) { titulo2.textContent = '¿Quitar a ' + tec + ' de la incidencia n.º ' + num + '?'; }
      var texto = $('#quitarTecnico-texto');
      if (texto) { texto.textContent = 'La incidencia n.º ' + num + ' vuelve a Pendiente y queda sin técnico hasta que asigne otro.'; }
    }
  });

  /* ---------- Asignar técnico: el botón espera a que se elija uno ---------- */
  $$('form[data-inc-asignar]').forEach(function (form) {
    var btn = $('[data-inc-asignar-btn]', form);
    if (!btn) { return; }
    var sync = function () { btn.disabled = !$('input[type="radio"]:checked:not(:disabled)', form); };
    sync();
    form.addEventListener('change', sync);
  });

  /* ---------- Asignar material: existencia visible y cantidad validada ---------- */
  function existencia(form) {
    var sel = $('[data-inc-mat-sel]', form);
    if (!sel || !sel.value) { return 0; }
    return parseInt(sel.options[sel.selectedIndex].getAttribute('data-stock'), 10) || 0;
  }

  function mensajeMaterial(form) {
    var sel = $('[data-inc-mat-sel]', form);
    var cant = $('[data-inc-cant]', form);
    if (!sel.value) { return { campo: sel, texto: 'Elija el material que se va a usar.' }; }
    var v = String(cant.value).trim();
    if (!v) { return { campo: cant, texto: 'Escriba cuántas unidades se usaron.' }; }
    if (!/^\d+$/.test(v) || parseInt(v, 10) < 1) { return { campo: cant, texto: 'La cantidad debe ser un número entero de 1 en adelante, sin signos ni decimales.' }; }
    var stock = existencia(form);
    if (parseInt(v, 10) > stock) {
      return { campo: cant, texto: 'Solo hay ' + stock + (stock === 1 ? ' unidad disponible' : ' unidades disponibles') + ' de este material. Escriba una cantidad menor o igual.' };
    }
    return null;
  }

  function mostrarError(form, problema) {
    var err = $('[data-inc-err]', form);
    var sel = $('[data-inc-mat-sel]', form);
    var cant = $('[data-inc-cant]', form);
    [sel, cant].forEach(function (c) { c.removeAttribute('aria-invalid'); });
    if (!err) { return; }
    if (!problema) { err.hidden = true; return; }
    err.querySelector('span').textContent = problema.texto;
    err.hidden = false;
    problema.campo.setAttribute('aria-invalid', 'true');
  }

  $$('form[data-inc-material]').forEach(function (form) {
    var sel = $('[data-inc-mat-sel]', form);
    var cant = $('[data-inc-cant]', form);
    var info = $('[data-inc-stock]', form);

    function pintarExistencia() {
      var stock = existencia(form);
      info.textContent = '';
      if (!sel.value) {
        info.textContent = 'Elija un material para ver cuántas unidades hay.';
        cant.removeAttribute('max');
        return;
      }
      cant.max = stock;
      info.appendChild(document.createTextNode('En inventario: '));
      var b = document.createElement('b');
      b.textContent = stock;
      info.appendChild(b);
      info.appendChild(document.createTextNode(stock === 1 ? ' unidad.' : ' unidades.'));
    }

    sel.addEventListener('change', function () {
      pintarExistencia();
      if (cant.value) { mostrarError(form, mensajeMaterial(form)); } else { mostrarError(form, null); }
    });
    cant.addEventListener('input', function () {
      var v = String(cant.value).trim();
      // Aviso inmediato solo si ya se pasó de la existencia; lo demás se dice al registrar
      var p = v ? mensajeMaterial(form) : null;
      mostrarError(form, p && v && /^\d+$/.test(v) ? p : null);
    });
    form.addEventListener('submit', function (e) {
      var p = mensajeMaterial(form);
      if (p) {
        e.preventDefault();
        mostrarError(form, p);
        p.campo.focus();
        return;
      }
      // Sin doble envío: el botón pasa a «cargando» (el formulario no usa data-sg-loading para poder validar antes)
      var btn = e.submitter || $('button[type="submit"]', form);
      if (btn && window.SGUM) { setTimeout(function () { window.SGUM.loading(btn, true, 'Asignando…'); btn.disabled = true; }, 0); }
    });
    pintarExistencia();
  });

  /* ---------- Filtros en móvil: plegados salvo que haya alguno activo ---------- */
  var filtros = $('#inc-filtros');
  var toggleFiltros = $('[data-inc-filtros-toggle]');
  if (filtros && toggleFiltros) {
    var mq = window.matchMedia ? window.matchMedia('(max-width: 767.98px)') : null;
    var plegar = function (si) {
      filtros.classList.toggle('is-collapsed', si);
      toggleFiltros.setAttribute('aria-expanded', si ? 'false' : 'true');
    };
    var aplicar = function () { plegar(!!(mq && mq.matches && filtros.classList.contains('is-collapsible'))); };
    aplicar();
    if (mq && mq.addEventListener) { mq.addEventListener('change', aplicar); }
    toggleFiltros.addEventListener('click', function () { plegar(!filtros.classList.contains('is-collapsed')); });
  }
}());
