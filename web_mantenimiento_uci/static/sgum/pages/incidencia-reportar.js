/* SGUM-UCI · formulario «Registrar incidencia».
   Contadores, ayuda de ubicación por zona del campus, pistas de prioridad y preparación de la foto en el navegador
   (lado mayor 1600 px, JPEG con calidad 0,8, mediante canvas). Si algo falla se sube la foto original.
   Sin innerHTML: el texto se escribe con textContent. */
(function () {
  'use strict';

  var form = document.getElementById('rep-form');
  if (!form) { return; }

  var $ = function (sel, ctx) { return (ctx || form).querySelector(sel); };
  var MAX_LADO = 1600;
  var CALIDAD = 0.8;

  /* ---------- Errores del servidor: llevar la atención al resumen ---------- */
  var resumen = document.getElementById('rep-errores');
  if (resumen) { resumen.focus({ preventScroll: false }); }

  /* ---------- Contadores ---------- */
  function contador(inputId, countId, max) {
    var input = document.getElementById(inputId);
    var out = document.getElementById(countId);
    if (!input || !out) { return; }
    var pintar = function () {
      var n = input.value.length;
      out.textContent = n + '/' + max;
      out.classList.toggle('is-limit', n >= max);
    };
    input.addEventListener('input', pintar);
    pintar();
  }
  contador('ubicacion', 'ubicacion-count', parseInt(form.getAttribute('data-ubicacion-max'), 10) || 50);
  contador('descripcion', 'descripcion-count', parseInt(form.getAttribute('data-descripcion-max'), 10) || 1000);

  /* ---------- Ayuda de ubicación según la zona ---------- */
  var ZONAS = {
    residencia: {
      ej: 'Residencia: escriba la residencia, el edificio y el número de apartamento o cuarto.',
      ph: 'Ej.: Res. 3, edif. B, apto 214'
    },
    docente: {
      ej: 'Local docente u oficina: escriba la facultad o el edificio y el número del local.',
      ph: 'Ej.: Fac. 2, edif. 5, local 105'
    },
    exterior: {
      ej: 'Zona exterior o servicio: escriba el punto de referencia más cercano (vial, área verde, comedor, red de agua, luz o gas).',
      ph: 'Ej.: Vial frente al comedor 2'
    }
  };
  var ubic = document.getElementById('ubicacion');
  var ejemplo = document.getElementById('ubicacion-ejemplo');
  var zonas = Array.prototype.slice.call(form.querySelectorAll('.rep-zona'));
  zonas.forEach(function (b) {
    b.addEventListener('click', function () {
      var z = ZONAS[b.getAttribute('data-zona')];
      if (!z) { return; }
      var ya = b.getAttribute('aria-pressed') === 'true';
      zonas.forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
      if (ya) { return; }
      b.setAttribute('aria-pressed', 'true');
      if (ejemplo) { ejemplo.textContent = z.ej + ' ' + z.ph.replace('Ej.: ', 'Por ejemplo: ') + '.'; }
      if (ubic) { ubic.placeholder = z.ph; }
    });
  });

  /* ---------- Pista de la prioridad elegida ---------- */
  var pista = document.getElementById('rep-prio-hint');
  var pistaBase = pista ? pista.textContent : '';
  Array.prototype.forEach.call(form.querySelectorAll('input[name="prioridad"]'), function (r) {
    r.addEventListener('change', function () {
      if (pista && r.checked) { pista.textContent = r.getAttribute('data-hint') + ' ' + pistaBase; }
    });
  });

  /* ---------- Foto ---------- */
  var input = document.getElementById('imagen');
  var prev = $('[data-rep-foto-prev]');
  var thumb = $('[data-rep-foto-thumb]');
  var nombre = $('[data-rep-foto-name]');
  var tam = $('[data-rep-foto-size]');
  var estado = $('[data-rep-foto-estado]');
  var quitar = $('[data-rep-foto-quitar]');
  var rotulo = $('[data-rep-foto-txt]');
  var maxBytes = parseInt(form.getAttribute('data-max-bytes'), 10) || 8 * 1024 * 1024;
  var maxMb = form.getAttribute('data-max-mb') || '8';
  var procesando = false;
  var urlVista = null;
  var token = 0;

  function fmt(bytes) {
    if (bytes >= 1048576) { return (bytes / 1048576).toFixed(1).replace('.', ',') + ' MB'; }
    return Math.max(1, Math.round(bytes / 1024)) + ' KB';
  }

  function mensaje(texto, error) {
    if (!estado) { return; }
    estado.textContent = texto || '';
    estado.classList.toggle('is-error', !!error);
  }

  function soltarVista() {
    if (urlVista) { URL.revokeObjectURL(urlVista); urlVista = null; }
  }

  function vaciar() {
    token++;
    procesando = false;
    if (input) { input.value = ''; }
    soltarVista();
    if (thumb) { thumb.textContent = ''; }
    if (prev) { prev.hidden = true; }
    if (quitar) { quitar.hidden = true; }
    if (rotulo) { rotulo.textContent = 'Tomar o elegir una foto'; }
  }

  function mostrar(file, detalle) {
    soltarVista();
    urlVista = URL.createObjectURL(file);
    if (thumb) {
      thumb.textContent = '';
      var img = document.createElement('img');
      img.alt = 'Vista previa de la foto elegida';
      img.width = 120; img.height = 120;
      img.src = urlVista;
      thumb.appendChild(img);
    }
    if (nombre) { nombre.textContent = file.name; }
    if (tam) { tam.textContent = detalle; }
    if (prev) { prev.hidden = false; }
    if (quitar) { quitar.hidden = false; }
    if (rotulo) { rotulo.textContent = 'Cambiar foto'; }
  }

  function cargar(file) {
    if (window.createImageBitmap) {
      return window.createImageBitmap(file, { imageOrientation: 'from-image' }).catch(function () { return window.createImageBitmap(file); });
    }
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () { URL.revokeObjectURL(url); resolve(img); };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('No se pudo leer la imagen')); };
      img.src = url;
    });
  }

  function aBlob(canvas) {
    return new Promise(function (resolve) { canvas.toBlob(resolve, 'image/jpeg', CALIDAD); });
  }

  function reducir(file) {
    return cargar(file).then(function (src) {
      var w = src.width || src.naturalWidth;
      var h = src.height || src.naturalHeight;
      if (!w || !h) { throw new Error('Sin dimensiones'); }
      var escala = Math.min(1, MAX_LADO / Math.max(w, h));
      var cw = Math.round(w * escala);
      var ch = Math.round(h * escala);
      var canvas = document.createElement('canvas');
      canvas.width = cw; canvas.height = ch;
      var ctx = canvas.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, cw, ch);
      ctx.drawImage(src, 0, 0, cw, ch);
      if (src.close) { src.close(); }
      return aBlob(canvas).then(function (blob) {
        if (!blob) { throw new Error('Sin resultado'); }
        return { blob: blob, w: cw, h: ch, reducida: escala < 1 };
      });
    });
  }

  function poner(file) {
    // Sustituye el archivo elegido por la versión preparada; si el navegador no lo permite, se conserva el original
    try {
      var dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      return true;
    } catch (e) { return false; }
  }

  function procesar(file) {
    var mi = ++token;
    if (!/^image\//.test(file.type)) {
      vaciar();
      mensaje('El archivo elegido no es una imagen. Elija una foto en formato JPG, PNG o WEBP.', true);
      return;
    }
    procesando = true;
    mensaje('Preparando la foto…', false);
    mostrar(file, fmt(file.size));

    var terminar = function (final, detalle) {
      if (mi !== token) { return; }
      procesando = false;
      if (final.size > maxBytes) {
        vaciar();
        mensaje('La foto pesa ' + fmt(final.size) + ' y el máximo es ' + maxMb + ' MB. Tome otra con menor resolución o elija una imagen más ligera.', true);
        return;
      }
      mostrar(final, detalle);
      mensaje('Foto lista para subir.', false);
    };

    var conservar = function (razon) {
      terminar(file, fmt(file.size) + (razon ? ' · ' + razon : ''));
    };

    if (file.type === 'image/gif' || file.type === 'image/svg+xml') { conservar('se sube sin cambios'); return; }

    reducir(file).then(function (r) {
      if (mi !== token) { return; }
      // Si no hizo falta reducir y el resultado pesa más, se conserva la original
      if (!r.reducida && r.blob.size >= file.size) { conservar('ya es ligera'); return; }
      var base = file.name.replace(/\.[^.]+$/, '') || 'foto';
      var nuevo = new File([r.blob], base + '.jpg', { type: 'image/jpeg', lastModified: Date.now() });
      if (!poner(nuevo)) { conservar('se sube sin reducir'); return; }
      terminar(nuevo, fmt(file.size) + ' → ' + fmt(nuevo.size) + ' · ' + r.w + ' × ' + r.h + ' px');
    }).catch(function () {
      // Formato que el navegador no decodifica (por ejemplo HEIC): se sube el original y el servidor decide
      conservar('no se pudo reducir; se sube tal cual');
    });
  }

  if (input) {
    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (!file) { vaciar(); mensaje('', false); return; }
      procesar(file);
    });
  }
  if (quitar) {
    quitar.addEventListener('click', function () {
      vaciar();
      mensaje('Foto quitada.', false);
      if (input) { input.focus(); }
    });
  }

  /* No se envía mientras la foto se está preparando (esta escucha va antes que la de sgum.js, en la captura de window) */
  window.addEventListener('submit', function (e) {
    if (e.target !== form || !procesando) { return; }
    e.preventDefault();
    e.stopPropagation();
    mensaje('Espere un momento: la foto todavía se está preparando.', true);
  }, true);
}());
