/* SGUM-UCI · Materiales (alta, edición y baja).
   Usado por all_materiales.html y editar_material.html. No depende de jQuery ni de otros scripts de página.

   Contrato con el servidor (backend-contract.md §3.12 y §3.13): campos POST «nombre», «tipo» y «cantidad».
   El servidor valida también y devuelve sus errores junto a cada campo; esta validación solo adelanta el aviso.
   Reglas iguales a las del servidor: nombre obligatorio (hasta 100), tipo obligatorio, cantidad entera de 0 al máximo.

   Atributos que reconoce:
     form[data-material-form]        formulario del material (alta o edición)
     [data-al-campo="nombre|tipo|cantidad"]   controles del cajetín
     [data-al-resumen]               aviso de error del formulario (con [data-al-resumen-texto])
     [data-al-abrir="id"]            botón que abre o pliega el panel de alta
     [data-al-cerrar="id"]           botón que pliega el panel
     [data-al-cero="id"]             botón que deja en 0 el campo de cantidad indicado
     #modalEliminarMaterial          modal de confirmación; toma data-id y data-nombre del botón que lo abre */
(function () {
  'use strict';

  var NOMBRE_MAX = 100;
  var SOLO_DIGITOS = /^[0-9]+$/;

  function formatoMiles(n) {
    try { return Number(n).toLocaleString('es-ES'); } catch (e) { return String(n); }
  }

  /* ---------- Errores dentro de la celda (misma estructura que sgum.js y partials/field.html) ---------- */
  function celdaDe(control) { return control.closest('.sg-field'); }

  function iconoAlerta() {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'sg-icon');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    var use = document.createElementNS(ns, 'use');
    use.setAttribute('href', '#i-alert');
    svg.appendChild(use);
    return svg;
  }

  function quitarError(control) {
    control.removeAttribute('aria-invalid');
    var celda = celdaDe(control);
    if (!celda) { return; }
    var mensajes = celda.querySelectorAll('.sg-field__msg');
    Array.prototype.forEach.call(mensajes, function (m) { m.parentNode.removeChild(m); });
    control.removeAttribute('aria-describedby');
    celda.classList.remove('is-error');
  }

  function ponerError(control, texto) {
    quitarError(control);
    control.setAttribute('aria-invalid', 'true');
    var celda = celdaDe(control);
    if (!celda) { return; }
    celda.classList.add('is-error');
    var p = document.createElement('p');
    p.className = 'sg-field__msg';
    p.id = control.id + '-msg';
    p.setAttribute('role', 'alert');
    p.appendChild(iconoAlerta());
    var span = document.createElement('span');
    span.textContent = texto;
    p.appendChild(span);
    celda.appendChild(p);
    control.setAttribute('aria-describedby', p.id);
  }

  /* ---------- Reglas (devuelven el texto del error o '') ---------- */
  function errorNombre(control) {
    var v = control.value.trim();
    if (!v) { return 'Escriba el nombre del material.'; }
    if (v.length > NOMBRE_MAX) {
      return 'El nombre admite hasta ' + NOMBRE_MAX + ' caracteres y usted escribió ' + v.length + '.';
    }
    return '';
  }

  function errorTipo(control) {
    return control.value ? '' : 'Seleccione el tipo de material.';
  }

  function errorCantidad(control) {
    var v = control.value.trim();
    var max = parseInt(control.getAttribute('data-max'), 10) || 1000000;
    if (!v) { return 'Escriba la cantidad en existencia. Use 0 si aún no hay unidades.'; }
    if (!SOLO_DIGITOS.test(v) || v.length > 12 || parseInt(v, 10) > max) {
      return 'La cantidad debe ser un número entero entre 0 y ' + formatoMiles(max) + ', sin signos ni decimales.';
    }
    return '';
  }

  var REGLAS = { nombre: errorNombre, tipo: errorTipo, cantidad: errorCantidad };

  function actualizarResumen(form, n) {
    var caja = form.querySelector('[data-al-resumen]');
    if (!caja) { return; }
    var texto = caja.querySelector('[data-al-resumen-texto]');
    if (n === 0) { caja.hidden = true; return; }
    var accion = form.id === 'formEditarMaterial' ? 'no se guardó ningún cambio' : 'no se registró el material';
    if (texto) {
      texto.textContent = n === 1
        ? 'Corrija el campo marcado: ' + accion + '.'
        : 'Corrija los ' + n + ' campos marcados: ' + accion + '.';
    }
    caja.hidden = false;
  }

  function validarFormulario(form) {
    var primero = null;
    var n = 0;
    Array.prototype.forEach.call(form.querySelectorAll('[data-al-campo]'), function (control) {
      var regla = REGLAS[control.getAttribute('data-al-campo')];
      var texto = regla ? regla(control) : '';
      if (texto) {
        ponerError(control, texto);
        n++;
        if (!primero) { primero = control; }
      } else {
        quitarError(control);
      }
    });
    actualizarResumen(form, n);
    return primero;
  }

  /* Se registra en captura, antes que el de sgum.js: si el formulario no es válido,
     sgum.js ve el envío cancelado y no deja el botón en «cargando». */
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!(form instanceof HTMLFormElement) || !form.hasAttribute('data-material-form')) { return; }
    var primero = validarFormulario(form);
    if (primero) {
      e.preventDefault();
      primero.focus();
    }
  }, true);

  /* Al escribir, el aviso de ese campo desaparece; se vuelve a evaluar al salir del campo. */
  document.addEventListener('input', function (e) {
    var t = e.target;
    if (t && t.matches && t.matches('[data-al-campo]') && t.getAttribute('aria-invalid') === 'true') {
      quitarError(t);
      var form = t.closest('form');
      if (form) {
        var restantes = form.querySelectorAll('[data-al-campo][aria-invalid="true"]').length;
        actualizarResumen(form, restantes);
      }
    }
  });

  document.addEventListener('focusout', function (e) {
    var t = e.target;
    if (!t || !t.matches || !t.matches('[data-al-campo]')) { return; }
    var regla = REGLAS[t.getAttribute('data-al-campo')];
    var texto = regla ? regla(t) : '';
    if (texto && (t.value.trim() !== '' || t.getAttribute('aria-invalid') === 'true')) { ponerError(t, texto); }
  });

  /* ---------- Panel de alta: se pliega dentro de la lámina ---------- */
  function panel(id) { return document.getElementById(id); }

  function sincronizarBotones(id, abierto) {
    Array.prototype.forEach.call(document.querySelectorAll('[data-al-abrir="' + id + '"]'), function (b) {
      b.setAttribute('aria-expanded', abierto ? 'true' : 'false');
    });
  }

  function abrirPanel(id) {
    var p = panel(id);
    if (!p) { return; }
    p.removeAttribute('data-cerrado');
    sincronizarBotones(id, true);
    var primero = p.querySelector('[data-al-campo]');
    if (primero) { primero.focus(); }
    if (p.scrollIntoView) { p.scrollIntoView({ block: 'nearest' }); }
  }

  function plegarPanel(id, devolverFoco) {
    var p = panel(id);
    if (!p) { return; }
    p.setAttribute('data-cerrado', '');
    sincronizarBotones(id, false);
    Array.prototype.forEach.call(p.querySelectorAll('[data-al-campo]'), function (c) {
      quitarError(c);
      if (c.tagName === 'SELECT') { c.selectedIndex = 0; } else { c.value = ''; }
    });
    var form = p.querySelector('form');
    if (form) { actualizarResumen(form, 0); }
    if (devolverFoco) {
      var boton = document.querySelector('[data-al-abrir="' + id + '"]');
      if (boton) { boton.focus(); }
    }
  }

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest) { return; }

    var abrir = t.closest('[data-al-abrir]');
    if (abrir) {
      e.preventDefault();
      var id = abrir.getAttribute('data-al-abrir');
      var p = panel(id);
      if (p && p.hasAttribute('data-cerrado')) { abrirPanel(id); }
      else if (p) { plegarPanel(id, false); }
      return;
    }

    var cerrar = t.closest('[data-al-cerrar]');
    if (cerrar) {
      plegarPanel(cerrar.getAttribute('data-al-cerrar'), true);
      return;
    }

    var cero = t.closest('[data-al-cero]');
    if (cero) {
      var campo = document.getElementById(cero.getAttribute('data-al-cero'));
      if (campo) {
        campo.value = '0';
        quitarError(campo);
        campo.focus();
        campo.select();
        if (window.SGUM) { window.SGUM.toast('La cantidad quedó en 0. Pulse «Guardar cambios» para confirmarlo.', { kind: 'info' }); }
      }
    }
  });

  /* ---------- Confirmación de eliminar: copia el material del botón que abrió el modal ---------- */
  var modal = document.getElementById('modalEliminarMaterial');
  if (modal) {
    modal.addEventListener('show.bs.modal', function (e) {
      var origen = e.relatedTarget;
      if (!origen || !origen.getAttribute) { return; }
      var ids = modal.querySelector('[data-al-ids]');
      if (ids) { ids.value = origen.getAttribute('data-id') || ''; }
      var nombre = modal.querySelector('[data-al-nombre]');
      if (nombre) { nombre.textContent = origen.getAttribute('data-nombre') || 'este material'; }
      var titulo = modal.querySelector('.modal-title');
      if (titulo) { titulo.textContent = '¿Eliminar el material «' + (origen.getAttribute('data-nombre') || '') + '»?'; }
    });
  }

  /* ---------- Estado inicial ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    // Con errores del servidor o sin materiales, el panel llega abierto: se enfoca el primer campo con error.
    var invalido = document.querySelector('form[data-material-form] [aria-invalid="true"]');
    if (invalido) { invalido.focus(); }
  });
}());
