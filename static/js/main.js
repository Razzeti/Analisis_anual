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

    refreshButton.addEventListener('click', refreshData);
    fetchDataAndRender();
});

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
}