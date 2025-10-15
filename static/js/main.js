document.addEventListener('DOMContentLoaded', function() {
    const loadingOverlay = document.getElementById('loading');
    const refreshButton = document.getElementById('refresh-button');
    let activeCharts = [];

    function showLoading(isRefreshing = false) {
        if (isRefreshing) {
            loadingOverlay.querySelector('p.text-lg').textContent = 'Actualizando datos...';
        } else {
            loadingOverlay.querySelector('p.text-lg').textContent = 'Procesando tus datos financieros...';
        }
        loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        loadingOverlay.style.display = 'none';
    }

    function destroyCharts() {
        activeCharts.forEach(chart => chart.destroy());
        activeCharts = [];
    }

    function fetchDataAndRender(isRefreshing = false) {
        showLoading(isRefreshing);
        destroyCharts();

        fetch('/api/data')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error en la red: ${response.statusText}`);
                }
                return response.json();
            })
            .then(transacciones => {
                hideLoading();
                if (transacciones.error) {
                    throw new Error(transacciones.error);
                }
                procesarYVisualizarDatos(transacciones);
            })
            .catch(error => {
                console.error('Error al obtener los datos:', error);
                hideLoading();
                const container = document.querySelector('.container');
                if (container) {
                    container.innerHTML = `<div class="text-center p-8 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                        <h2 class="text-2xl font-bold mb-2">Error al Cargar los Datos</h2>
                        <p>${error.message}</p>
                        <p class="mt-4 text-sm">Por favor, intenta refrescar los datos o revisa la consola para más detalles.</p>
                    </div>`;
                }
            });
    }

    function refreshData() {
        showLoading(true);
        destroyCharts();

        fetch('/api/data/refresh', { method: 'POST' })
            .then(response => response.json())
            .then(result => {
                if (result.status === 'success') {
                    fetchDataAndRender(true);
                } else {
                    throw new Error(result.message || 'La actualización falló.');
                }
            })
            .catch(error => {
                console.error('Error al refrescar los datos:', error);
                hideLoading();
                alert(`Error al actualizar: ${error.message}`);
            });
    }

    function procesarYVisualizarDatos(transacciones) {
        const mesesEs = { 'ENE': 'JAN', 'FEB': 'FEB', 'MAR': 'MAR', 'ABR': 'APR', 'MAY': 'MAY', 'JUN': 'JUN', 'JUL': 'JUL', 'AGO': 'AUG', 'SEP': 'SEP', 'OCT': 'OCT', 'NOV': 'NOV', 'DIC': 'DEC' };

        transacciones.forEach(t => {
            t.Gastos = parseFloat(t['CARGOS / DEBE']) || 0;
            t.Ingresos = parseFloat(t['ABONOS / HABER']) || 0;

            const fechaRaw = t.FECHA;
            const dia = fechaRaw.substring(0, 2);
            const mesAbbr = fechaRaw.substring(2, 5).toUpperCase();
            const mesEn = mesesEs[mesAbbr];
            const anio = new Date().getFullYear();

            t.FechaObj = mesEn ? new Date(`${mesEn} ${dia}, ${anio}`) : null;
        });

        const transaccionesValidas = transacciones.filter(t => t.FechaObj && !isNaN(t.FechaObj));

        const totalIngresos = transaccionesValidas.reduce((sum, t) => sum + t.Ingresos, 0);
        const totalGastos = transaccionesValidas.reduce((sum, t) => sum + t.Gastos, 0);
        const balanceNeto = totalIngresos - totalGastos;

        const formatoMoneda = (valor) => valor.toLocaleString('es-PE', { style: 'currency', currency: 'PEN' });

        document.getElementById('totalIngresos').textContent = formatoMoneda(totalIngresos);
        document.getElementById('totalGastos').textContent = formatoMoneda(totalGastos);
        const balanceEl = document.getElementById('balanceNeto');
        balanceEl.textContent = formatoMoneda(balanceNeto);
        balanceEl.className = 'text-3xl font-bold mt-2';
        if (balanceNeto >= 0) {
            balanceEl.classList.add('text-emerald-500');
        } else {
            balanceEl.classList.add('text-red-500');
        }

        const mensual = {};
        transaccionesValidas.forEach(t => {
            const month = t.FechaObj.toISOString().slice(0, 7);
            if (!mensual[month]) {
                mensual[month] = { ingresos: 0, gastos: 0 };
            }
            mensual[month].ingresos += t.Ingresos;
            mensual[month].gastos += t.Gastos;
        });
        const labelsMensual = Object.keys(mensual).sort();
        const dataIngresosMensual = labelsMensual.map(m => mensual[m].ingresos);
        const dataGastosMensual = labelsMensual.map(m => mensual[m].gastos);

        const porCuenta = transaccionesValidas.reduce((acc, t) => {
            const cuenta = t.CUENTA_ORIGEN || 'Desconocida';
            if (!acc[cuenta]) {
                acc[cuenta] = { total: 0 };
            }
            acc[cuenta].total += t.Ingresos + t.Gastos;
            return acc;
        }, {});

        function getTop5(data, descriptionField, amountField) {
            const grouped = data.filter(d => d[amountField] > 0).reduce((acc, curr) => {
                let key = curr[descriptionField] || 'Sin descripción';
                key = key.replace(/Pago YAPE (de|a) \d+/i, 'Pago YAPE a Terceros').trim();
                key = key.replace(/CLAR\d+/i, 'Servicios (Claro)').trim();
                key = key.replace(/WOW\d+/i, 'Suscripción (WOW)').trim();
                key = key.replace(/ABON PLIN-[\w\s\*]+/i, 'Recepción PLIN').trim();
                acc[key] = (acc[key] || 0) + curr[amountField];
                return acc;
            }, {});
            return Object.entries(grouped).sort(([, a], [, b]) => b - a).slice(0, 5);
        }
        const topIngresos = getTop5(transaccionesValidas, 'DESCRIPCION', 'Ingresos');
        const topGastos = getTop5(transaccionesValidas, 'DESCRIPCION', 'Gastos');

        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#64748b';

        const charts = {
            evolucionMensual: new Chart(document.getElementById('evolucionMensualChart'), {
                type: 'line',
                data: {
                    labels: labelsMensual,
                    datasets: [
                        { label: 'Ingresos', data: dataIngresosMensual, borderColor: '#10b981', backgroundColor: '#10b98130', fill: true, tension: 0.3, pointBackgroundColor: '#10b981' },
                        { label: 'Gastos', data: dataGastosMensual, borderColor: '#ef4444', backgroundColor: '#ef444430', fill: true, tension: 0.3, pointBackgroundColor: '#ef4444' }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                        x: { type: 'time', time: { unit: 'month', displayFormats: { month: 'MMM yy' } } },
                        y: { ticks: { callback: value => formatoMoneda(value) } }
                    },
                    plugins: { tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${formatoMoneda(context.parsed.y)}` } } }
                }
            }),
            cuentaOrigen: new Chart(document.getElementById('cuentaOrigenChart'), {
                type: 'doughnut',
                data: {
                    labels: Object.keys(porCuenta),
                    datasets: [{
                        data: Object.values(porCuenta).map(c => c.total),
                        backgroundColor: ['#38bdf8', '#fb923c', '#a78bfa', '#f472b6', '#4ade80'],
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 4,
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' },
                        tooltip: { callbacks: { label: (context) => `${context.label}: ${formatoMoneda(context.parsed)}` } }
                    }
                }
            }),
            topIngresos: new Chart(document.getElementById('topIngresosChart'), {
                type: 'bar',
                data: {
                    labels: topIngresos.map(item => item[0]),
                    datasets: [{
                        label: 'Monto Total',
                        data: topIngresos.map(item => item[1]),
                        backgroundColor: '#10b98190',
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { x: { ticks: { callback: value => formatoMoneda(value) } } }
                }
            }),
            topGastos: new Chart(document.getElementById('topGastosChart'), {
                type: 'bar',
                data: {
                    labels: topGastos.map(item => item[0]),
                    datasets: [{
                        label: 'Monto Total',
                        data: topGastos.map(item => item[1]),
                        backgroundColor: '#ef444490',
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { x: { ticks: { callback: value => formatoMoneda(value) } } }
                }
            })
        };
        activeCharts.push(...Object.values(charts));

        analizarGastosDetalladamente(transaccionesValidas, totalGastos);

    }

    function analizarGastosDetalladamente(transacciones, totalGastosGeneral) {
        const contenedor = document.getElementById('analisis-gastos-detallado');
        if (!contenedor) return;
        contenedor.innerHTML = '';

        const formatoMoneda = (valor) => valor.toLocaleString('es-PE', { style: 'currency', currency: 'PEN' });

        const reglasCategorias = {
            'Servicios Básicos': /pago de servicio|luz del sur|sedapal|calidda|movistar|claro|entel|directv/i,
            'Transporte': /beat|uber|cabify|didi|peaje|pasaje|transporte/i,
            'Comida y Restaurantes': /restaurante|cafe|pardo's chicken|kfc|mcdonald's|starbucks|chifa|comida|mercado|plaza vea|wong|metro|tottus|vivanda/i,
            'Suscripciones y Digital': /netflix|spotify|disney+|hbo max|prime video|google|microsoft|apple|wow/i,
            'Salud': /farmacia|doctor|clínica|salud|botica/i,
            'Compras': /ripley|saga falabella|h&m|zara|compras|tienda|mall|jockey plaza/i,
            'Transferencias y Retiros': /transferencia a|retiro en|envío a/i,
            'Otros Gastos': /./
        };

        let gastosPorCategoria = {};

        transacciones.filter(t => t.Gastos > 0).forEach(t => {
            let categoriaAsignada = 'Otros Gastos';
            for (const categoria in reglasCategorias) {
                if (reglasCategorias[categoria].test(t.DESCRIPCION)) {
                    categoriaAsignada = categoria;
                    break;
                }
            }
            if (!gastosPorCategoria[categoriaAsignada]) {
                gastosPorCategoria[categoriaAsignada] = [];
            }
            gastosPorCategoria[categoriaAsignada].push(t);
        });

        let analisisHTML = '<div class="space-y-8">';

        // 1. Acumulación de Dinero por Destino
        analisisHTML += '<div>';
        analisisHTML += '<h3 class="text-xl font-semibold text-gray-800 mb-3">Acumulación de Gastos por Categoría</h3>';
        analisisHTML += '<ul class="space-y-2 text-gray-700">';
        Object.entries(gastosPorCategoria).sort(([, a], [, b]) => b.reduce((s, t) => s + t.Gastos, 0) - a.reduce((s, t) => s + t.Gastos, 0)).forEach(([categoria, gastos]) => {
            const totalCategoria = gastos.reduce((sum, t) => sum + t.Gastos, 0);
            const porcentaje = (totalCategoria / totalGastosGeneral) * 100;
            analisisHTML += `<li class="flex justify-between items-center bg-gray-100 p-3 rounded-lg">
                <span>${categoria}</span>
                <span class="font-medium">${formatoMoneda(totalCategoria)} (${porcentaje.toFixed(2)}%)</span>
            </li>`;
        });
        analisisHTML += '</ul></div>';

        // 2. Valores Extraños (Anomalías)
        const mediaGeneral = totalGastosGeneral / transacciones.filter(t => t.Gastos > 0).length;
        const desviacionEstandar = Math.sqrt(transacciones.filter(t => t.Gastos > 0).reduce((sum, t) => sum + Math.pow(t.Gastos - mediaGeneral, 2), 0) / transacciones.length);
        const umbralAnomalia = mediaGeneral + (2 * desviacionEstandar); // Umbral: media + 2 * stddev
        const gastosAnomalos = transacciones.filter(t => t.Gastos > umbralAnomalia);

        if (gastosAnomalos.length > 0) {
            analisisHTML += '<div>';
            analisisHTML += `<h3 class="text-xl font-semibold text-gray-800 mb-3">Posibles Gastos Atípicos (Mayores a ${formatoMoneda(umbralAnomalia)})</h3>`;
            analisisHTML += '<ul class="space-y-2">';
            gastosAnomalos.sort((a,b) => b.Gastos - a.Gastos).forEach(g => {
                analisisHTML += `<li class="p-3 bg-yellow-100 border-l-4 border-yellow-400 rounded">
                    <p class="font-semibold">${g.DESCRIPCION}</p>
                    <p class="text-sm text-gray-600">${g.FECHA} - <span class="font-bold text-yellow-800">${formatoMoneda(g.Gastos)}</span></p>
                </li>`;
            });
            analisisHTML += '</ul></div>';
        }

        // 3. Recomendaciones y Niveles de Mejora
        analisisHTML += '<div>';
        analisisHTML += '<h3 class="text-xl font-semibold text-gray-800 mb-3">Recomendaciones y Oportunidades de Mejora</h3>';
        analisisHTML += '<div class="space-y-3">';
        const categoriaMasCara = Object.entries(gastosPorCategoria).sort(([, a], [, b]) => b.reduce((s, t) => s + t.Gastos, 0) - a.reduce((s, t) => s + t.Gastos, 0))[0];
        if (categoriaMasCara) {
             const totalCategoria = categoriaMasCara[1].reduce((s, t) => s + t.Gastos, 0);
             const porcentaje = (totalCategoria / totalGastosGeneral) * 100;
             analisisHTML += `<div class="p-4 bg-blue-100 border-l-4 border-blue-400 rounded">
                <h4 class="font-bold text-blue-800">Foco Principal: ${categoriaMasCara[0]}</h4>
                <p class="text-gray-700">Has gastado ${formatoMoneda(totalCategoria)}, que representa el ${porcentaje.toFixed(2)}% de tus gastos totales. Revisa las transacciones en esta categoría para identificar posibles ahorros.</p>
             </div>`;
        }
        const suscripciones = gastosPorCategoria['Suscripciones y Digital'];
        if (suscripciones && suscripciones.length > 1) {
            const totalSuscripciones = suscripciones.reduce((s, t) => s + t.Gastos, 0);
            analisisHTML += `<div class="p-4 bg-indigo-100 border-l-4 border-indigo-400 rounded">
                <h4 class="font-bold text-indigo-800">Revisa tus Suscripciones</h4>
                <p class="text-gray-700">Detectamos ${suscripciones.length} gastos en suscripciones y servicios digitales por un total de ${formatoMoneda(totalSuscripciones)}. ¿Sigues usando todos estos servicios?</p>
            </div>`;
        }
        analisisHTML += '</div></div>';


        analisisHTML += '</div>'; // Cierre del contenedor principal

        contenedor.innerHTML = analisisHTML;
    }

    refreshButton.addEventListener('click', refreshData);
    fetchDataAndRender();
});