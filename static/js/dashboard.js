// extractor/static/js/dashboard.js

(function() {
    'use strict';

    // Mapa de colores FIJOS por estado (NUNCA cambian sin importar el orden)
    const COLOR_MAP = {
        'generado': '#17a2b8',      // Azul turquesa
        'en proceso': '#ffc107',    // Amarillo
        'completado': '#28a745',    // Verde
        'cancelado': '#dc3545',     // Rojo
        'no exitoso': '#6c757d',    // Gris
        'sin ticket': '#e83e8c'     // Rosado
    };

    // Orden fijo de visualización en los gráficos
    const ORDEN_FIJO = ['Generado', 'En Proceso', 'Completado', 'Cancelado', 'No Exitoso', 'Sin Ticket'];

    // Función para obtener color según el estado (consistente)
    function getEstadoColor(estadoLabel) {
        const estadoLower = estadoLabel.toLowerCase();
        return COLOR_MAP[estadoLower] || '#17a2b8';
    }

    // Función para reordenar datos según orden fijo
    function reordenarDatos(labels, data) {
        const resultado = {
            labels: [],
            data: [],
            colors: []
        };
        
        // Primero agregar en orden fijo
        ORDEN_FIJO.forEach(estadoFijo => {
            const idx = labels.findIndex(l => l.toLowerCase() === estadoFijo.toLowerCase());
            if (idx !== -1 && data[idx] > 0) {
                resultado.labels.push(labels[idx]);
                resultado.data.push(data[idx]);
                resultado.colors.push(getEstadoColor(estadoFijo));
            }
        });
        
        // Luego agregar estados que no están en el orden fijo
        labels.forEach((label, idx) => {
            if (!ORDEN_FIJO.some(estado => estado.toLowerCase() === label.toLowerCase()) && data[idx] > 0) {
                resultado.labels.push(label);
                resultado.data.push(data[idx]);
                resultado.colors.push(getEstadoColor(label));
            }
        });
        
        return resultado;
    }

    // Función para construir URL de filtro hacia ticket_list
    function buildFilterUrl(estado, tipoGrafico, chartData) {
        const urlParams = new URLSearchParams(window.location.search);
        const params = new URLSearchParams();
        
        params.append('estado', estado);
        params.append('from_dashboard', 'true');
        
        if (tipoGrafico === 'periodo' && chartData) {
            if (chartData.periodo_fecha_desde) {
                params.append('fecha_desde', chartData.periodo_fecha_desde);
            }
            if (chartData.periodo_fecha_hasta) {
                params.append('fecha_hasta', chartData.periodo_fecha_hasta);
            }
        } else {
            const fechaDesde = urlParams.get('fecha_desde') || '';
            const fechaHasta = urlParams.get('fecha_hasta') || '';
            if (fechaDesde) params.append('fecha_desde', fechaDesde);
            if (fechaHasta) params.append('fecha_hasta', fechaHasta);
        }
        
        const clienteSelected = urlParams.get('cliente') || '';
        const proyectoSelected = urlParams.get('proyecto') || '';
        if (clienteSelected) params.append('cliente', clienteSelected);
        if (proyectoSelected) params.append('proyecto', proyectoSelected);
        
        const ticketListUrl = document.querySelector('[data-ticket-list-url]')?.getAttribute('data-ticket-list-url') || '/tickets/';
        
        return ticketListUrl + '?' + params.toString();
    }

    // Función para obtener código de estado
    function getEstadoCode(estadoLabel) {
        const label = estadoLabel.toLowerCase();
        const estadoMap = {
            'sin ticket': 'SIN_TICKET',
            'no exitoso': 'NO EXITOSO',
            'generado': 'GENERADO',
            'en proceso': 'EN_PROCESO',
            'completado': 'COMPLETADO',
            'cancelado': 'CANCELADO'
        };
        return estadoMap[label] || estadoLabel.toUpperCase();
    }

    // Función para manejar clic en gráficos
    function handlePieChartClick(activeElements, chartData, tipoGrafico, labels) {
        if (activeElements.length > 0) {
            const index = activeElements[0].index;
            const estadoLabel = labels[index];
            
            if (estadoLabel === 'Sin Ticket') {
                const solicitudListUrl = '/solicitudes/';
                const params = new URLSearchParams();
                params.append('sin_ticket', 'si');
                
                const urlParams = new URLSearchParams(window.location.search);
                const clienteSelected = urlParams.get('cliente') || '';
                const proyectoSelected = urlParams.get('proyecto') || '';
                if (clienteSelected) params.append('cliente', clienteSelected);
                if (proyectoSelected) params.append('proyecto', proyectoSelected);
                
                if (tipoGrafico === 'periodo' && chartData) {
                    if (chartData.periodo_fecha_desde) params.append('fecha_desde', chartData.periodo_fecha_desde);
                    if (chartData.periodo_fecha_hasta) params.append('fecha_hasta', chartData.periodo_fecha_hasta);
                }
                
                window.location.href = solicitudListUrl + '?' + params.toString();
                return;
            }
            
            const estadoCode = getEstadoCode(estadoLabel);
            const url = buildFilterUrl(estadoCode, tipoGrafico, chartData);
            window.location.href = url;
        }
    }

    // Función para inicializar gráficos
    function initCharts(chartData) {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js no está cargado');
            return;
        }

        if (typeof ChartDataLabels !== 'undefined') {
            Chart.register(ChartDataLabels);
        }

        const pieOptions = {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { size: 11 }, padding: 10, usePointStyle: true, boxWidth: 10 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        };

        if (typeof ChartDataLabels !== 'undefined') {
            pieOptions.plugins.datalabels = {
                color: 'white',
                font: { weight: 'bold', size: 14 },
                formatter: (value, context) => {
                    const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                    return percentage > 5 && value > 0 ? `${percentage}%` : '';
                },
                backgroundColor: 'rgba(0,0,0,0.6)',
                borderRadius: 4,
                padding: { left: 6, right: 6, top: 4, bottom: 4 },
                align: 'center',
                anchor: 'center',
                offset: 0
            };
        }

        // Gráfico General
        const ctxGeneral = document.getElementById('estadosGeneralChart');
        if (ctxGeneral && chartData.estados_general_labels) {
            const labelsRaw = JSON.parse(chartData.estados_general_labels);
            const dataRaw = JSON.parse(chartData.estados_general_data);
            const { labels, data, colors } = reordenarDatos(labelsRaw, dataRaw);
            
            if (labels.length > 0) {
                new Chart(ctxGeneral.getContext('2d'), {
                    type: 'pie',
                    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 2, borderColor: 'white' }] },
                    options: {
                        ...pieOptions,
                        onClick: (event, activeElements) => handlePieChartClick(activeElements, chartData, 'general', labels)
                    }
                });
            }
        }

        // Gráfico Período
        const ctxPeriodo = document.getElementById('estadosPeriodoChart');
        if (ctxPeriodo && chartData.estados_periodo_labels) {
            const labelsRaw = JSON.parse(chartData.estados_periodo_labels);
            const dataRaw = JSON.parse(chartData.estados_periodo_data);
            const { labels, data, colors } = reordenarDatos(labelsRaw, dataRaw);
            
            if (labels.length > 0) {
                new Chart(ctxPeriodo.getContext('2d'), {
                    type: 'pie',
                    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 2, borderColor: 'white' }] },
                    options: {
                        ...pieOptions,
                        onClick: (event, activeElements) => handlePieChartClick(activeElements, chartData, 'periodo', labels)
                    }
                });
            }
        }

        // Gráfico de Clientes
        const ctxClientes = document.getElementById('clientesChart');
        if (ctxClientes && chartData.clientes_labels) {
            const labels = JSON.parse(chartData.clientes_labels);
            const data = JSON.parse(chartData.clientes_data);
            
            new Chart(ctxClientes.getContext('2d'), {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Número de Tickets',
                        data,
                        backgroundColor: 'rgba(52, 152, 219, 0.7)',
                        borderColor: '#3498db',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { legend: { position: 'top' } },
                    scales: {
                        y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, title: { display: true, text: 'Cantidad de Tickets' } },
                        x: { ticks: { rotation: -45, autoSkip: true }, title: { display: true, text: 'Clientes' } }
                    }
                }
            });
        }

        // Gráfico de Tendencia
        const ctxTendencias = document.getElementById('tendenciasChart');
        if (ctxTendencias && chartData.tendencias_labels) {
            const labels = JSON.parse(chartData.tendencias_labels);
            const data = JSON.parse(chartData.tendencias_data);
            
            new Chart(ctxTendencias.getContext('2d'), {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Tickets Creados',
                        data,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#2980b9',
                        pointBorderColor: 'white',
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { legend: { position: 'top' } },
                    scales: {
                        y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, title: { display: true, text: 'Cantidad de Tickets' } },
                        x: { title: { display: true, text: 'Fecha' }, ticks: { rotation: -30, autoSkip: true } }
                    }
                }
            });
        }
        
        console.log('Dashboard cargado - Gráficos con colores consistentes');
    }

    function loadChartData() {
        const chartDataElement = document.getElementById('chart-data');
        if (chartDataElement) {
            try {
                const chartData = JSON.parse(chartDataElement.textContent);
                initCharts(chartData);
            } catch(e) {
                console.error('Error<script id="chart-data" type="application/json"> parsing chart data:', e);
            }
        }
    }

    function waitForChart() {
        if (typeof Chart !== 'undefined') {
            loadChartData();
        } else {
            setTimeout(waitForChart, 100);
        }
    }

    window.toggleCard = function(headerElement) {
        const card = headerElement.closest('.data-card');
        if (!card) return;
        const body = card.querySelector('.data-card-body');
        const icon = headerElement.querySelector('.toggle-icon');
        if (body) {
            if (body.classList.contains('collapsed')) {
                body.classList.remove('collapsed');
                if (icon) icon.textContent = '▼';
            } else {
                body.classList.add('collapsed');
                if (icon) icon.textContent = '▶';
            }
        }
    };

    window.toggleUsuarioDetalle = function(headerElement) {
        const usuarioCard = headerElement.closest('.usuario-card');
        if (!usuarioCard) return;
        const detalle = usuarioCard.querySelector('.usuario-detalle');
        if (detalle) {
            detalle.classList.toggle('collapsed');
        }
    };

    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.data-card-body').forEach(body => body.classList.remove('collapsed'));
        document.querySelectorAll('.usuario-detalle').forEach(detalle => detalle.classList.remove('collapsed'));
        waitForChart();
    });

})();