/* SGUM-UCI · Estadísticas: gráficos con Chart.js local (static/vendor/chart.umd.min.js).
   Lee los datos que all_reportes.html deja en <script type="application/json"> (json_script) y los colores
   de los tokens del sistema (tokens.css). Sin CDN, sin degradados ni sombras.

   Forma de cada gráfico según la pregunta que responde:
     · Por mes (evolución en el año)  -> columnas de un solo color; el mes filtrado se resalta.
     · Por tipo (qué pesa más)        -> barras horizontales ordenadas de mayor a menor, un solo color.
     · Por estado (parte del todo)    -> barra de una pieza en HTML/CSS dentro de la plantilla, con su tabla.
   Cada gráfico tiene su tabla de datos (los tooltips ayudan, no son la única vía) y un resumen en texto. */
(function () {
  'use strict';

  function json(id) {
    var el = document.getElementById(id);
    if (!el) { return null; }
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  var config = document.getElementById('dash-config');
  var anio = config ? parseInt(config.getAttribute('data-year'), 10) : new Date().getFullYear();
  var mesAnio = config ? (config.getAttribute('data-mes-anio') || '') : '';
  var meses = json('dato-meses') || [];
  var porMes = json('dato-mes') || [];
  var porTipo = json('dato-tipo') || [];

  var raiz = getComputedStyle(document.documentElement);
  function token(nombre) { return raiz.getPropertyValue(nombre).trim(); }
  var C = {
    tinta: token('--sg-ink'), tintaHover: token('--sg-ink-deep'), texto: token('--sg-text'),
    texto2: token('--sg-text-2'), texto3: token('--sg-text-3'), rejilla: token('--sg-grid'),
    rejillaFuerte: token('--sg-grid-strong'), apagado: token('--sg-neutral-line'), fuente: token('--sg-font')
  };

  function mostrar(el, si) { if (el) { el.hidden = !si; } }
  function texto(id, valor) { var el = document.getElementById(id); if (el) { el.textContent = valor; } }
  function plural(n, uno, varios) { return n === 1 ? uno : varios; }
  function unir(lista) {
    if (lista.length <= 1) { return lista.join(''); }
    return lista.slice(0, -1).join(', ') + ' y ' + lista[lista.length - 1];
  }
  function suma(lista) { return lista.reduce(function (a, b) { return a + b; }, 0); }

  /* Tabla de datos, siempre presente como alternativa al gráfico */
  function llenarTabla(idTabla, filas, totalEtiqueta) {
    var tabla = document.getElementById(idTabla);
    if (!tabla) { return; }
    var cuerpo = tabla.querySelector('tbody');
    cuerpo.textContent = '';
    filas.forEach(function (f) {
      var tr = document.createElement('tr');
      var th = document.createElement('th');
      th.scope = 'row'; th.textContent = f[0];
      var td = document.createElement('td');
      td.className = 'sg-num sg-data'; td.textContent = String(f[1]);
      tr.appendChild(th); tr.appendChild(td);
      cuerpo.appendChild(tr);
    });
    var pie = tabla.querySelector('tfoot');
    if (pie) { pie.parentNode.removeChild(pie); }
    pie = document.createElement('tfoot');
    var tr2 = document.createElement('tr');
    var th2 = document.createElement('th');
    th2.scope = 'row'; th2.textContent = totalEtiqueta;
    var td2 = document.createElement('td');
    td2.className = 'sg-num sg-data'; td2.textContent = String(suma(filas.map(function (f) { return f[1]; })));
    tr2.appendChild(th2); tr2.appendChild(td2); pie.appendChild(tr2);
    tabla.appendChild(pie);
  }

  /* Valor en la punta de las barras, solo donde ayuda:
     ninguna etiqueta por punto salvo las indicadas (máximo) o todas si el gráfico es corto. */
  var etiquetasPunta = {
    id: 'sgEtiquetasPunta',
    afterDatasetsDraw: function (chart, args, opciones) {
      if (!opciones || opciones.modo === 'ninguna') { return; }
      var ctx = chart.ctx;
      var meta = chart.getDatasetMeta(0);
      var datos = chart.data.datasets[0].data;
      var max = Math.max.apply(null, datos);
      var horizontal = chart.options.indexAxis === 'y';
      var conValor = datos.filter(function (v) { return v > 0; }).length;
      ctx.save();
      ctx.font = '600 12px ' + C.fuente;
      ctx.fillStyle = C.texto;
      meta.data.forEach(function (barra, i) {
        var v = datos[i];
        if (!v) { return; }
        var todas = opciones.modo === 'todas' || conValor <= (opciones.hasta || 0);
        if (!todas && v !== max) { return; }
        if (horizontal) {
          ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
          ctx.fillText(String(v), barra.x + 6, barra.y);
        } else {
          ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
          ctx.fillText(String(v), barra.x, barra.y - 4);
        }
      });
      ctx.restore();
    }
  };

  function opcionesBase() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: false, // sin animación de entrada: en modo Operar el movimiento solo comunica estado
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: C.texto, titleColor: '#ffffff', bodyColor: '#ffffff',
          cornerRadius: 0, padding: 10, displayColors: false,
          titleFont: { family: C.fuente, size: 13, weight: '600' }, bodyFont: { family: C.fuente, size: 13 }
        }
      }
    };
  }

  if (window.Chart) {
    window.Chart.defaults.font.family = C.fuente;
    window.Chart.defaults.font.size = 12;
    window.Chart.defaults.color = C.texto2;
  }

  /* ---------- Incidencias por mes ---------- */
  (function porMesAnio() {
    var lienzo = document.getElementById('grafico-mes');
    if (!lienzo) { return; }
    var total = suma(porMes);
    var filas = meses.map(function (m, i) { return [m, porMes[i] || 0]; });
    var resumen = meses.map(function (m, i) { return m + ' ' + (porMes[i] || 0); }).join(', ');
    lienzo.setAttribute('aria-label', 'Gráfico de columnas de incidencias por mes en ' + anio + '. ' + resumen + '. Total ' + total + '.');
    llenarTabla('mes-tabla', filas, 'Total del año');

    if (total === 0) {
      mostrar(document.getElementById('mes-lienzo'), false);
      mostrar(document.getElementById('mes-vacio'), true);
      mostrar(document.getElementById('mes-datos'), false);
      return;
    }

    var max = Math.max.apply(null, porMes);
    var lideres = [];
    porMes.forEach(function (v, i) { if (v === max) { lideres.push(meses[i]); } });
    texto('mes-resumen', lideres.length === 1
      ? 'En ' + anio + ' se registraron ' + total + ' ' + plural(total, 'incidencia', 'incidencias') + '. ' + lideres[0] + ' fue el mes con más: ' + max + '.'
      : 'En ' + anio + ' se registraron ' + total + ' ' + plural(total, 'incidencia', 'incidencias') + '. Los meses con más fueron ' + unir(lideres) + ', con ' + max + ' cada uno.');

    // Mes filtrado: se resalta en tinta y el resto queda en tono apagado
    var indiceFiltrado = -1;
    var m = /^(\d{4})-(\d{1,2})$/.exec(mesAnio);
    if (m) {
      var mesN = parseInt(m[2], 10);
      if (parseInt(m[1], 10) === anio && mesN >= 1 && mesN <= 12) { indiceFiltrado = mesN - 1; }
      texto('mes-nota', indiceFiltrado >= 0
        ? 'El mes filtrado (' + meses[indiceFiltrado].toLowerCase() + ') aparece en azul oscuro; los demás, en gris azulado.'
        : 'El mes filtrado no pertenece a ' + anio + ', por eso no se resalta aquí.');
    }
    var colores = porMes.map(function (v, i) { return indiceFiltrado >= 0 && i !== indiceFiltrado ? C.apagado : C.tinta; });

    if (!window.Chart) { return; }
    var opciones = opcionesBase();
    opciones.layout = { padding: { top: 20 } };
    opciones.interaction = { mode: 'index', intersect: false };
    opciones.plugins.sgEtiquetasPunta = { modo: 'max', hasta: 4 };
    opciones.plugins.tooltip.callbacks = {
      title: function (items) { return meses[items[0].dataIndex] + ' de ' + anio; },
      label: function (item) { var v = item.parsed.y; return v + ' ' + plural(v, 'incidencia', 'incidencias'); }
    };
    opciones.scales = {
      x: {
        grid: { display: false },
        border: { color: C.rejillaFuerte },
        ticks: {
          color: C.texto2, autoSkip: false, maxRotation: 0,
          callback: function (valor) {
            var nombre = meses[valor] || '';
            return this.chart.width < 440 ? nombre.charAt(0) : nombre.slice(0, 3);
          }
        }
      },
      y: {
        beginAtZero: true,
        grid: { color: C.rejilla, lineWidth: 1 },
        border: { display: false },
        ticks: { precision: 0, color: C.texto2 },
        title: { display: true, text: 'Incidencias', color: C.texto3, font: { size: 12 } }
      }
    };
    new window.Chart(lienzo, {
      type: 'bar',
      data: {
        labels: meses,
        datasets: [{
          label: 'Incidencias', data: porMes, backgroundColor: colores, hoverBackgroundColor: C.tintaHover,
          borderWidth: 0, borderRadius: 0, maxBarThickness: 24, categoryPercentage: 0.8, barPercentage: 0.9
        }]
      },
      options: opciones,
      plugins: [etiquetasPunta]
    });
  }());

  /* ---------- Incidencias por tipo ---------- */
  (function porTipoIncidencia() {
    var lienzo = document.getElementById('grafico-tipo');
    if (!lienzo) { return; }
    var todas = porTipo.map(function (t) { return [t.etiqueta, t.cantidad]; });
    llenarTabla('tipo-tabla', todas.slice().sort(function (a, b) { return b[1] - a[1]; }), 'Total');

    var conDatos = porTipo.filter(function (t) { return t.cantidad > 0; })
      .sort(function (a, b) { return b.cantidad - a.cantidad; });
    var sinDatos = porTipo.filter(function (t) { return t.cantidad === 0; }).map(function (t) { return t.etiqueta; });
    var total = suma(porTipo.map(function (t) { return t.cantidad; }));

    lienzo.setAttribute('aria-label', 'Gráfico de barras de incidencias por tipo. ' + (conDatos.length
      ? conDatos.map(function (t) { return t.etiqueta + ' ' + t.cantidad; }).join(', ') + '. Total ' + total + '.'
      : 'No hay incidencias de los tipos de la lista.'));

    var nota = [];
    if (conDatos.length === 1) {
      nota.push('Todas son de ' + conDatos[0].etiqueta + '.');
    } else if (conDatos.length && conDatos[0].cantidad > 0) {
      var lideres = conDatos.filter(function (t) { return t.cantidad === conDatos[0].cantidad; }).map(function (t) { return t.etiqueta; });
      nota.push(lideres.length === 1
        ? lideres[0] + ' concentra ' + conDatos[0].cantidad + ' de ' + total + ' (' + Math.round(conDatos[0].cantidad * 100 / total) + ' %).'
        : 'Con más incidencias: ' + unir(lideres) + ', con ' + conDatos[0].cantidad + ' cada uno.');
    }
    if (sinDatos.length) { nota.push('Sin incidencias: ' + unir(sinDatos) + '.'); }
    texto('tipo-nota', nota.join(' '));

    if (!conDatos.length) {
      mostrar(document.getElementById('tipo-lienzo'), false);
      return;
    }
    if (!window.Chart) { return; }

    var contenedor = document.getElementById('tipo-lienzo');
    if (contenedor) { contenedor.style.height = (conDatos.length * 34 + 56) + 'px'; }

    var opciones = opcionesBase();
    opciones.indexAxis = 'y';
    opciones.layout = { padding: { right: 32 } };
    opciones.interaction = { mode: 'nearest', axis: 'y', intersect: false };
    opciones.plugins.sgEtiquetasPunta = { modo: 'todas' };
    opciones.plugins.tooltip.callbacks = {
      title: function (items) { return items[0].label; },
      label: function (item) {
        var v = item.parsed.x;
        return v + ' ' + plural(v, 'incidencia', 'incidencias') + ' (' + Math.round(v * 100 / total) + ' %)';
      }
    };
    opciones.scales = {
      x: {
        beginAtZero: true,
        grid: { color: C.rejilla, lineWidth: 1 },
        border: { display: false },
        ticks: { precision: 0, color: C.texto2 },
        title: { display: true, text: 'Incidencias', color: C.texto3, font: { size: 12 } }
      },
      y: {
        grid: { display: false },
        border: { color: C.rejillaFuerte },
        ticks: { color: C.texto, autoSkip: false }
      }
    };
    new window.Chart(lienzo, {
      type: 'bar',
      data: {
        labels: conDatos.map(function (t) { return t.etiqueta; }),
        datasets: [{
          label: 'Incidencias', data: conDatos.map(function (t) { return t.cantidad; }),
          backgroundColor: C.tinta, hoverBackgroundColor: C.tintaHover,
          borderWidth: 0, borderRadius: 0, maxBarThickness: 20, categoryPercentage: 0.85, barPercentage: 0.9
        }]
      },
      options: opciones,
      plugins: [etiquetasPunta]
    });
  }());
}());
