/* SGUM-UCI · Personas: comportamientos de la lista de usuarios y del formulario de cuenta.
   Se carga con {% block scripts %} en all_usuarios.html y editar_usuario.html. No depende de jQuery.
   Requiere sgum.js (SGUM.toast, SGUM.loading), que se ejecuta después (defer): por eso todo
   lo que lo usa espera a DOMContentLoaded.

   Qué hace
     · Panel de alta (#alta-usuario): se abre con #btn-alta o con la dirección #registrar / #registrar-tecnico,
       valida en el cliente y envía por fetch a la URL del formulario (respuesta JSON: success | errors).
     · Formularios .persona-form (alta y edición): validación con mensajes dentro de cada celda,
       ayuda de contraseña (requisitos y seguridad) y descripción del rol elegido.
     · Confirmaciones de la lista (#confirmarDesactivar, #confirmarEliminar): rellenan el formulario
       compartido #usuario-accion con los datos del botón que las abrió.
     · Botones con aria-disabled y data-motivo: explican por qué no están disponibles.        */
(function () {
  'use strict';

  var CLAVE_CREADO = 'sgum-usuario-creado';
  var REQUERIDO = {
    username: 'Escriba el nombre de usuario.',
    name: 'Escriba el nombre.', first_name: 'Escriba el nombre.',
    lastname: 'Escriba los apellidos.', last_name: 'Escriba los apellidos.',
    email: 'Escriba el correo electrónico, por ejemplo nombre@uci.cu.',
    password: 'Escriba una contraseña.',
    confirmPassword: 'Repita la contraseña para confirmarla.',
    rol: 'Elija un rol de la lista.'
  };
  var NO_COINCIDEN = 'Las contraseñas no coinciden. Escríbalas de nuevo.';
  var NIVELES = ['', 'Débil', 'Aceptable', 'Buena', 'Muy buena'];
  var CAMPOS_SERVIDOR = {
    usuario: 'username', nombre: 'name', apellidos: 'lastname', email: 'email',
    password: 'password', confirmPassword: 'confirmPassword', rol: 'rol'
  };

  function $(id) { return document.getElementById(id); }
  function todos(raiz, selector) { return Array.prototype.slice.call(raiz.querySelectorAll(selector)); }

  /* ---------------------------------------------------------------- errores en celda */
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

  function celda(campo) { return campo.closest('.sg-field'); }

  function marcarError(campo, texto) {
    var c = celda(campo);
    campo.setAttribute('aria-invalid', 'true');
    if (!c) { return; }
    c.classList.add('is-error');
    var msg = c.querySelector('.sg-field__msg[data-persona-msg]');
    if (!msg) {
      msg = document.createElement('p');
      msg.className = 'sg-field__msg';
      msg.setAttribute('role', 'alert');
      msg.setAttribute('data-persona-msg', '');
      msg.id = (campo.id || 'campo') + '-msg';
      msg.appendChild(iconoAlerta());
      msg.appendChild(document.createElement('span'));
      c.appendChild(msg);
    }
    msg.lastChild.textContent = texto;
    campo.setAttribute('aria-describedby', msg.id);
  }

  function quitarError(campo) {
    campo.removeAttribute('aria-invalid');
    var c = celda(campo);
    if (!c) { return; }
    todos(c, '.sg-field__msg').forEach(function (m) { m.parentNode.removeChild(m); });
    c.classList.remove('is-error');
    campo.removeAttribute('aria-describedby');
  }

  function limpiar(form) {
    todos(form, '[aria-invalid="true"]').forEach(quitarError);
    todos(form, '.sg-field.is-error').forEach(function (c) { c.classList.remove('is-error'); });
    resumen(form, 0, '');
  }

  /* Resumen del formulario: «Corrija los 3 campos marcados: no se guardó nada.» */
  function resumen(form, cantidad, texto) {
    var caja = form.querySelector('[data-persona-resumen]');
    if (!caja) { return; }
    var t = texto;
    if (!t && cantidad) {
      t = 'Corrija ' + (cantidad === 1 ? 'el campo marcado' : 'los ' + cantidad + ' campos marcados') +
        ': ' + (form.getAttribute('data-persona-fallo') || 'no se guardó nada') + '.';
    }
    if (!t) { caja.hidden = true; return; }
    caja.querySelector('[data-persona-resumen-txt]').textContent = t;
    caja.hidden = false;
  }

  /* ---------------------------------------------------------------- validación en el cliente */
  function largoMinimo(form) { return form.__pwMin || 8; }

  function validar(form) {
    var errs = [];
    function anadir(campo, texto) { if (campo) { errs.push({ campo: campo, texto: texto }); } }
    function campo(n) { return form.elements[n] || null; }

    var usuario = campo('username');
    if (usuario && !usuario.disabled) {
      var u = usuario.value.trim();
      if (!u) { anadir(usuario, REQUERIDO.username); }
      else if (/\s/.test(u)) { anadir(usuario, 'El nombre de usuario no puede llevar espacios. Use letras, números o los signos @ . + - _'); }
    }
    ['name', 'first_name', 'lastname', 'last_name'].forEach(function (n) {
      var el = campo(n);
      if (el && el.required && !el.value.trim()) { anadir(el, REQUERIDO[n]); }
    });
    var correo = campo('email');
    if (correo) {
      var m = correo.value.trim();
      if (!m) { anadir(correo, REQUERIDO.email); }
      else if (!correo.checkValidity()) { anadir(correo, 'El correo no es válido. Escríbalo así: nombre@uci.cu.'); }
    }
    var clave = campo('password'), conf = campo('confirmPassword');
    if (clave) {
      var p = clave.value, min = largoMinimo(form);
      if (!p) {
        if (clave.required) { anadir(clave, REQUERIDO.password); }
      } else if (p.length < min) {
        anadir(clave, 'La contraseña necesita al menos ' + min + ' caracteres; le faltan ' + (min - p.length) + '.');
      } else if (/^\d+$/.test(p)) {
        anadir(clave, 'La contraseña no puede ser solo números. Añada letras u otros signos.');
      }
      if (conf) {
        if (!p && !conf.value) {
          if (conf.required) { anadir(conf, REQUERIDO.confirmPassword); }
        } else if (conf.value !== p) {
          anadir(conf, conf.value ? NO_COINCIDEN : REQUERIDO.confirmPassword);
        }
      }
    }
    var rol = campo('rol');
    if (rol && rol.required && !rol.disabled && !rol.value) { anadir(rol, REQUERIDO.rol); }
    errs.sort(function (a, b) { return a.campo.compareDocumentPosition(b.campo) & 4 ? -1 : 1; });
    return errs;
  }

  /* El resumen queda arriba del formulario: se trae a la vista (bajo la barra fija) antes de enfocar el primer error */
  function verResumen(form) {
    var caja = form.querySelector('[data-persona-resumen]');
    if (caja && !caja.hidden) { caja.scrollIntoView({ block: 'nearest' }); }
  }

  function mostrar(form, errs) {
    errs.forEach(function (e) { marcarError(e.campo, e.texto); });
    resumen(form, errs.length, '');
    if (errs.length) { verResumen(form); errs[0].campo.focus({ preventScroll: true }); }
  }

  /* Al corregir un campo se retira su mensaje */
  function vigilarCorreccion(form) {
    function alCambiar(e) {
      var t = e.target;
      if (t && t.getAttribute && t.getAttribute('aria-invalid') === 'true') { quitarError(t); }
    }
    /* En captura: se retira el mensaje antes de que un manejador del propio campo pueda volver a ponerlo */
    form.addEventListener('input', alCambiar, true);
    form.addEventListener('change', alCambiar, true);
  }

  /* ---------------------------------------------------------------- ayuda de contraseña */
  function iniciarClave(form) {
    var clave = form.elements.password, conf = form.elements.confirmPassword;
    var caja = form.querySelector('[data-pw]');
    if (!clave || !caja) { return; }
    var reglas = todos(caja, '.pw-reglas li').map(function (li) {
      var texto = li.textContent, m = /(\d+)\s+caracteres/i.exec(texto), tipo = 'servidor', min = 0;
      if (m) { tipo = 'largo'; min = parseInt(m[1], 10); form.__pwMin = min; }
      else if (/num[eé]ric/i.test(texto)) { tipo = 'numerica'; }
      if (tipo === 'servidor') { li.classList.add('is-info'); }
      return { li: li, tipo: tipo, min: min, estado: li.querySelector('[data-pw-estado]') };
    });
    var medidor = caja.querySelector('.pw-meter');
    var nivelTxt = caja.querySelector('[data-pw-nivel]');
    var min = largoMinimo(form);

    function puntos(v) {
      if (!v) { return 0; }
      var s = 0;
      if (v.length >= min) { s++; }
      if (v.length >= 12) { s++; }
      if (/[A-Za-z]/.test(v) && /\d/.test(v)) { s++; }
      if (/[^A-Za-z0-9]/.test(v) || (/[a-z]/.test(v) && /[A-Z]/.test(v))) { s++; }
      if (/^\d+$/.test(v) || v.length < min) { s = Math.min(s, 1); }
      return Math.max(1, Math.min(4, s));
    }

    function actualizar() {
      var v = clave.value;
      reglas.forEach(function (r) {
        if (r.tipo === 'servidor') { return; }
        var ok = r.tipo === 'largo' ? v.length >= r.min : (v.length > 0 && !/^\d+$/.test(v));
        r.li.classList.toggle('is-ok', ok);
        if (r.estado) { r.estado.textContent = ok ? ' (cumple)' : ' (pendiente)'; }
      });
      var n = puntos(v);
      if (medidor) { medidor.setAttribute('data-nivel', String(n)); }
      if (nivelTxt) { nivelTxt.textContent = n ? NIVELES[n] : 'aún sin escribir'; }
    }

    clave.addEventListener('input', function () {
      actualizar();
      if (conf && conf.value && conf.getAttribute('aria-invalid') === 'true' && conf.value === clave.value) { quitarError(conf); }
    });
    if (conf) {
      conf.addEventListener('blur', function () {
        if (conf.value && conf.value !== clave.value) { marcarError(conf, NO_COINCIDEN); }
      });
      conf.addEventListener('input', function () {
        if (conf.value.length >= clave.value.length && conf.value !== clave.value) { marcarError(conf, NO_COINCIDEN); }
      });
    }
    actualizar();
  }

  /* ---------------------------------------------------------------- descripción del rol */
  function iniciarRol(form) {
    var sel = form.elements.rol, desc = form.querySelector('[data-rol-desc]');
    if (!sel || !desc || sel.tagName !== 'SELECT') { return; }
    function mostrarDesc() {
      var op = sel.options[sel.selectedIndex];
      var t = op ? op.getAttribute('data-desc') : '';
      if (t) { desc.textContent = t; }
    }
    sel.addEventListener('change', mostrarDesc);
    mostrarDesc();
  }

  /* ---------------------------------------------------------------- envío */
  function enviando(boton, si) {
    if (!boton || !window.SGUM) { return; }
    if (si) { window.SGUM.loading(boton, true, boton.getAttribute('data-loading-label')); boton.disabled = true; }
    else { window.SGUM.loading(boton, false); }
  }

  function pintarErroresServidor(form, errores) {
    var n = 0, otros = [], marcados = [];
    Object.keys(errores).forEach(function (k) {
      if (k === 'general') { return; }
      var campo = CAMPOS_SERVIDOR[k] && form.elements[CAMPOS_SERVIDOR[k]];
      if (campo) {
        marcarError(campo, errores[k]);
        marcados.push(campo);
        n++;
      } else {
        otros.push(errores[k]);
      }
    });
    marcados.sort(function (a, b) { return a.compareDocumentPosition(b) & 4 ? -1 : 1; });
    if (!n && !otros.length && errores.general) { otros.push(errores.general); }
    if (otros.length) { resumen(form, 0, otros.join(' ')); }
    else { resumen(form, n, ''); }
    if (marcados.length) { verResumen(form); marcados[0].focus({ preventScroll: true }); }
  }

  function registrado(form, datos) {
    var nombre = form.elements.username.value.trim();
    try { window.sessionStorage.setItem(CLAVE_CREADO, nombre); } catch (e) { /* sin almacenamiento: solo se pierde el aviso */ }
    var lista = form.getAttribute('data-lista') || window.location.pathname;
    if (window.location.pathname === lista && !window.location.search) {
      window.location.hash = 'usuario-' + datos.id;
      window.location.reload();
    } else {
      window.location.assign(lista + '#usuario-' + datos.id);
    }
  }

  function iniciarAlta() {
    var form = $('form-alta');
    if (!form) { return; }
    var boton = form.querySelector('[data-persona-enviar]');

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      limpiar(form);
      var errs = validar(form);
      if (errs.length) { mostrar(form, errs); return; }

      enviando(boton, true);
      fetch(form.getAttribute('action'), {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
      }).then(function (r) {
        return r.json().then(
          function (d) { return { status: r.status, datos: d }; },
          function () { return { status: r.status, datos: null }; }
        );
      }).then(function (res) {
        var d = res.datos;
        if (d && d.success) { registrado(form, d); return; }
        enviando(boton, false);
        if (d && d.errors) { pintarErroresServidor(form, d.errors); }
        else if (res.status === 403 || (d && d.message)) {
          resumen(form, 0, (d && d.message) || 'Su rol no permite registrar usuarios.');
        } else {
          resumen(form, 0, 'No se registró el usuario. Si su sesión venció, recargue la página e inicie sesión de nuevo; si no, inténtelo otra vez.');
        }
      }).catch(function () {
        enviando(boton, false);
        resumen(form, 0, 'No se pudo comunicar con el servidor. Compruebe la conexión de red e inténtelo de nuevo.');
      });
    });
  }

  function iniciarEdicion() {
    var form = $('form-edicion');
    if (!form) { return; }
    form.addEventListener('submit', function (e) {
      limpiar(form);
      var errs = validar(form);
      if (errs.length) { e.preventDefault(); mostrar(form, errs); return; }
      var boton = e.submitter || form.querySelector('[data-persona-enviar]');
      setTimeout(function () { enviando(boton, true); }, 0);
    });
  }

  /* ---------------------------------------------------------------- panel de alta */
  function iniciarPanel() {
    var boton = $('btn-alta'), panel = $('alta-usuario'), form = $('form-alta');
    if (!boton || !panel || !form) { return; }

    function abrir(rol) {
      panel.hidden = false;
      boton.setAttribute('aria-expanded', 'true');
      if (rol && form.elements.rol) {
        form.elements.rol.value = rol;
        form.elements.rol.dispatchEvent(new Event('change', { bubbles: true }));
      }
      panel.scrollIntoView({ block: 'nearest' });
      var primero = form.querySelector('input:not([type="hidden"])');
      if (primero) { primero.focus({ preventScroll: true }); }
    }
    function cerrar(devolverFoco) {
      form.reset();
      limpiar(form);
      form.elements.password.dispatchEvent(new Event('input', { bubbles: true }));
      form.elements.rol.dispatchEvent(new Event('change', { bubbles: true }));
      panel.hidden = true;
      boton.setAttribute('aria-expanded', 'false');
      if (devolverFoco) { boton.focus(); }
    }

    boton.addEventListener('click', function () { if (panel.hidden) { abrir(); } else { cerrar(true); } });
    var cancelar = form.querySelector('[data-persona-cancelar]');
    if (cancelar) { cancelar.addEventListener('click', function () { cerrar(true); }); }
    panel.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !e.defaultPrevented) { e.preventDefault(); cerrar(true); }
    });

    function porDireccion() {
      var h = window.location.hash;
      if (h === '#registrar' || h === '#registrar-tecnico') { abrir(h === '#registrar-tecnico' ? 'tecnico' : ''); }
    }
    porDireccion();
    window.addEventListener('hashchange', porDireccion);
  }

  /* ---------------------------------------------------------------- confirmaciones de la lista */
  function iniciarConfirmaciones() {
    var accion = $('usuario-accion');
    if (!accion) { return; }
    var modos = {
      confirmarDesactivar: {
        titulo: function (q) { return '¿Desactivar la cuenta de «' + q + '»?'; },
        texto: function (q) { return '«' + q + '» ya no podrá iniciar sesión y, si tiene una sesión abierta, se cerrará en su próxima petición.'; },
        detalle: function () { return 'Sus incidencias, solicitudes y notificaciones se conservan. Puede reactivar la cuenta cuando quiera.'; }
      },
      confirmarEliminar: {
        titulo: function (q) { return '¿Eliminar la cuenta de «' + q + '»?'; },
        texto: function (q) { return 'Se borrará la cuenta de «' + q + '» de forma permanente.'; },
        detalle: function () { return 'Si la cuenta tiene incidencias registradas o atendidas no se eliminará: desactívela para conservar el historial.'; }
      }
    };
    Object.keys(modos).forEach(function (id) {
      var modal = $(id);
      if (!modal) { return; }
      modal.addEventListener('show.bs.modal', function (ev) {
        var t = ev.relatedTarget;
        if (!t) { return; }
        var quien = t.getAttribute('data-usuario') || '';
        var els = accion.elements;
        accion.setAttribute('action', t.getAttribute('data-url'));
        if (id === 'confirmarDesactivar') {
          els.is_active.disabled = false; els.is_active.value = '0';
          els.action.disabled = true; els.ids.disabled = true;
        } else {
          els.is_active.disabled = true;
          els.action.disabled = false; els.action.value = 'delete';
          els.ids.disabled = false; els.ids.value = t.getAttribute('data-id');
        }
        modal.querySelector('.modal-title').textContent = modos[id].titulo(quien);
        var ps = modal.querySelectorAll('.modal-body p');
        if (ps[0]) { ps[0].textContent = modos[id].texto(quien); }
        if (ps[1]) { ps[1].textContent = modos[id].detalle(quien); }
      });
    });
  }

  /* Botón no disponible: explica el motivo al pulsarlo (también en pantallas táctiles) */
  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('[aria-disabled="true"][data-motivo]') : null;
    if (!b) { return; }
    e.preventDefault();
    if (window.SGUM) { window.SGUM.toast(b.getAttribute('data-motivo'), { kind: 'info', timeout: 7000 }); }
  });

  document.addEventListener('DOMContentLoaded', function () {
    todos(document, 'form.persona-form, form#form-alta').forEach(function (form) {
      vigilarCorreccion(form);
      iniciarClave(form);
      iniciarRol(form);
    });
    iniciarAlta();
    iniciarEdicion();
    iniciarPanel();
    iniciarConfirmaciones();

    try {
      var nuevo = window.sessionStorage.getItem(CLAVE_CREADO);
      if (nuevo) {
        window.sessionStorage.removeItem(CLAVE_CREADO);
        if (window.SGUM) { window.SGUM.toast('Se registró la cuenta «' + nuevo + '». Ya puede iniciar sesión.', { kind: 'ok', timeout: 8000 }); }
      }
    } catch (e) { /* sin almacenamiento: no hay aviso */ }
  });
}());
