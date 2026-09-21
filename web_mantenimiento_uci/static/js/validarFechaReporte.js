/* SGUM-UCI · Estadísticas: filtro de mes (all_reportes.html).

   Antes este archivo buscaba #registroForm, #fechaInicio y #fechaFin, que la página nunca tuvo, y fallaba
   al cargarse. Ahora valida el único filtro real: el campo «mesAnio» del formulario #filtroPeriodo.

   Contrato con el servidor (backend-contract.md §3.14): GET mesAnio=AAAA-MM y anio=AAAA.
   Un mes inválido no rompe nada en el servidor (lo ignora con un aviso), pero es mejor decirlo antes.
   Firefox y Safari de escritorio no dibujan <input type="month">: lo muestran como texto, por eso se
   comprueba el formato AAAA-MM aquí además de en el navegador.

   Además, el año del gráfico mensual sigue al mes elegido: al aplicar «2025-06» se envía anio=2025. */
(function () {
  'use strict';

  var form = document.getElementById('filtroPeriodo');
  if (!form) { return; }
  var campo = form.elements.mesAnio;
  var anio = form.elements.anio;
  var aviso = document.getElementById('filtro-error');
  if (!campo) { return; }

  var FORMATO = /^(\d{4})-(0[1-9]|1[0-2])$/;

  function textoDeError(valor) {
    if (!valor) { return ''; }                       // vacío = todos los periodos
    var m = FORMATO.exec(valor);
    if (!m) { return 'Escriba el mes con el formato AAAA-MM, por ejemplo 2026-03.'; }
    var y = parseInt(m[1], 10);
    if (y < 2000 || y > 2100) { return 'Escriba un año entre 2000 y 2100.'; }
    var maximo = campo.getAttribute('max');
    if (maximo && valor > maximo) { return 'Elija un mes que no sea posterior a ' + maximo + ': todavía no hay incidencias de ese mes.'; }
    return '';
  }

  function mostrarError(texto) {
    if (aviso) {
      aviso.hidden = !texto;
      aviso.textContent = '';
      if (texto) {
        var ns = 'http://www.w3.org/2000/svg';
        var svg = document.createElementNS(ns, 'svg');
        svg.setAttribute('class', 'sg-icon');
        svg.setAttribute('aria-hidden', 'true');
        svg.setAttribute('focusable', 'false');
        var use = document.createElementNS(ns, 'use');
        use.setAttribute('href', '#i-alert');
        svg.appendChild(use);
        aviso.appendChild(svg);
        var span = document.createElement('span');
        span.textContent = texto;
        aviso.appendChild(span);
      }
    }
    if (texto) { campo.setAttribute('aria-invalid', 'true'); } else { campo.removeAttribute('aria-invalid'); }
  }

  form.addEventListener('submit', function (e) {
    var valor = campo.value.trim();
    var texto = textoDeError(valor);
    mostrarError(texto);
    if (texto) {
      e.preventDefault();
      campo.focus();
      return;
    }
    if (valor && anio) { anio.value = valor.slice(0, 4); }
  });

  campo.addEventListener('input', function () {
    if (campo.getAttribute('aria-invalid') === 'true') { mostrarError(textoDeError(campo.value.trim())); }
  });
}());
