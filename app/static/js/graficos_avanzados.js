// Gráficos Avanzados Demo - Supervisión Operativa
console.log('🚀 Iniciando Demo Avanzada de Gráficos...');

// Check if Telegram WebApp is available
if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
}

// Base URL para API
const baseUrl = 'https://6d8c759e04c7.ngrok-free.app';

// Global data storage
let dashboardData = {};
let currentCategory = 'all';
let chartInstances = {};

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 Inicializando Demo Avanzada...');
    showLoading(true);
    loadAllData().catch(error => {
        console.error('Error initializing:', error);
        showLoading(false);
        showNotification('Error al cargar la demo', 'error');
    });
    setupEventListeners();
});

async function loadAllData() {
    try {
        showLoading(true);
        
        const fetchOptions = {
            headers: {
                'ngrok-skip-browser-warning': 'true'
            }
        };
        
        // Load all necessary data
        const [summaryRes, sucursalPerfRes, grupoPerfRes, areasRes, estadosRes] = await Promise.all([
            fetch(`${baseUrl}/api/summary`, fetchOptions),
            fetch(`${baseUrl}/api/performance/sucursal`, fetchOptions),
            fetch(`${baseUrl}/api/performance/grupo`, fetchOptions),
            fetch(`${baseUrl}/api/areas/supervision`, fetchOptions),
            fetch(`${baseUrl}/api/metadata/estados`, fetchOptions)
        ]);
        
        const responses = await Promise.all([
            summaryRes.json(),
            sucursalPerfRes.json(),
            grupoPerfRes.json(),
            areasRes.json(),
            estadosRes.json()
        ]);
        
        dashboardData = {
            summary: responses[0],
            sucursalPerf: responses[1],
            grupoPerf: responses[2],
            areas: responses[3],
            estados: responses[4]
        };
        
        console.log('📊 Datos cargados:', dashboardData);
        
        // Update stats
        updateStats();
        
        // Initialize all charts
        initializeAllCharts();
        
        showLoading(false);
        
    } catch (error) {
        console.error('❌ Error cargando datos:', error);
        showLoading(false);
        showNotification('Error al cargar los datos', 'error');
    }
}

function updateStats() {
    const promedio = dashboardData.summary?.data?.promedio_general || 0;
    const totalEvaluaciones = dashboardData.summary?.data?.total_evaluaciones || 0;
    const totalSucursales = dashboardData.summary?.data?.total_sucursales || 0;
    const totalEstados = dashboardData.estados?.data?.length || 0;
    
    document.getElementById('stat-promedio').textContent = `${parseFloat(promedio).toFixed(1)}%`;
    document.getElementById('stat-evaluaciones').textContent = totalEvaluaciones.toLocaleString();
    document.getElementById('stat-sucursales').textContent = totalSucursales.toLocaleString();
    document.getElementById('stat-estados').textContent = totalEstados.toLocaleString();
}

function setupEventListeners() {
    // Category tabs
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentCategory = tab.dataset.category;
            filterChartsByCategory();
        });
    });
    
    // Search
    const searchInput = document.getElementById('chart-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterChartsBySearch(e.target.value);
        });
    }
    
    // Export buttons
    document.querySelectorAll('[data-export]').forEach(btn => {
        btn.addEventListener('click', () => {
            const chartId = btn.dataset.export;
            exportChart(chartId);
        });
    });
}

function filterChartsByCategory() {
    const charts = document.querySelectorAll('.advanced-chart-card');
    charts.forEach(chart => {
        const chartCategory = chart.dataset.category;
        if (currentCategory === 'all' || chartCategory === currentCategory) {
            chart.style.display = 'block';
        } else {
            chart.style.display = 'none';
        }
    });
}

function filterChartsBySearch(searchTerm) {
    const charts = document.querySelectorAll('.advanced-chart-card');
    const term = searchTerm.toLowerCase();
    
    charts.forEach(chart => {
        const title = chart.querySelector('.chart-header h3').textContent.toLowerCase();
        const category = chart.dataset.category;
        
        if (title.includes(term) || category.includes(term)) {
            chart.style.display = 'block';
        } else {
            chart.style.display = 'none';
        }
    });
}

function initializeAllCharts() {
    console.log('🎨 Inicializando todos los gráficos avanzados...');
    
    // Maps Category
    createChoroplethMap();
    createPinMap();
    createBubbleMap();
    createHeatMap();
    create3DMap();
    createFlowMap();
    
    // Bars Category
    createHorizontalBars();
    createGroupedBars();
    createStackedBars();
    createBarWithLine();
    createBipolarBars();
    createWaterfallChart();
    
    // Trends Category
    createPredictionChart();
    createAreaZoomChart();
    createCandlestickChart();
    createSparklines();
    createStreamChart();
    createTimelineChart();
    
    // Comparison Category
    createRadarComparison();
    createParallelCoordinates();
    createBulletCharts();
    createDumbbellChart();
    createSlopeChart();
    createButterflyChart();
    
    // Distribution Category
    createMultilevelDonut();
    createBoxPlot();
    createViolinPlot();
    createRidgePlot();
    createJoyPlot();
    createBeeswarm();
    
    // Gauges Category
    createClassicGauge();
    createModernGauge();
    createProgressBars();
    createSemiCircleGauge();
    createActivityGauge();
    createSpeedometer();
    
    // Advanced Category
    createSunburst();
    createNetworkGraph();
    create3DScatter();
    createChordDiagram();
    createAlluvialDiagram();
    createPolarChart();
}

// MAPS CATEGORY
function createChoroplethMap() {
    try {
        const container = document.getElementById('choropleth-map');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        // Group by estado
        const estadosData = {};
        dashboardData.sucursalPerf.data.forEach(sucursal => {
            const estado = sucursal.estado;
            if (!estadosData[estado]) {
                estadosData[estado] = {
                    promedio: 0,
                    count: 0,
                    sum: 0
                };
            }
            estadosData[estado].sum += parseFloat(sucursal.promedio);
            estadosData[estado].count += 1;
            estadosData[estado].promedio = estadosData[estado].sum / estadosData[estado].count;
        });
        
        const estados = Object.keys(estadosData);
        const values = Object.values(estadosData).map(d => d.promedio);
        
        const trace = {
            type: 'choropleth',
            locationmode: 'geojson-id',
            geojson: window.getMexicoAngelGeoJSON ? window.getMexicoAngelGeoJSON() : null,
            locations: estados,
            z: values,
            text: estados.map(estado => `${estado}: ${estadosData[estado].promedio.toFixed(1)}%`),
            colorscale: [
                [0, '#ff4444'],
                [0.5, '#ffaa00'],
                [0.75, '#00aaff'],
                [1, '#00ff88']
            ],
            colorbar: {
                title: 'Promedio (%)',
                thickness: 15
            }
        };
        
        const layout = {
            geo: {
                scope: 'north america',
                showframe: false,
                showcoastlines: false,
                projection: { type: 'mercator' }
            },
            height: 400,
            margin: { t: 0, b: 0, l: 0, r: 0 }
        };
        
        Plotly.newPlot(container, [trace], layout, { responsive: true });
        chartInstances['choropleth-map'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating choropleth map:', error);
    }
}

function createPinMap() {
    try {
        const container = document.getElementById('pin-map');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        // Create pin map data
        const pinData = dashboardData.sucursalPerf.data.slice(0, 50).map(sucursal => ({
            type: 'scattergeo',
            mode: 'markers',
            name: sucursal.sucursal_clean,
            lon: [-99.1332 + (Math.random() - 0.5) * 10], // Simulated coordinates
            lat: [19.4326 + (Math.random() - 0.5) * 10],
            marker: {
                size: Math.max(sucursal.total_evaluaciones / 2, 10),
                color: parseFloat(sucursal.promedio),
                colorscale: 'Viridis',
                cmin: 0,
                cmax: 100,
                line: {
                    color: 'white',
                    width: 1
                }
            },
            text: `${sucursal.sucursal_clean}<br>Promedio: ${sucursal.promedio}%<br>Evaluaciones: ${sucursal.total_evaluaciones}`
        }));
        
        const layout = {
            geo: {
                scope: 'north america',
                projection: { type: 'mercator' },
                center: { lat: 23.6345, lon: -102.5528 },
                showland: true,
                landcolor: 'rgb(243, 243, 243)',
                coastlinecolor: 'rgb(204, 204, 204)',
                showlakes: true,
                lakecolor: 'rgb(255, 255, 255)'
            },
            height: 400,
            margin: { t: 0, b: 0, l: 0, r: 0 }
        };
        
        Plotly.newPlot(container, pinData, layout, { responsive: true });
        chartInstances['pin-map'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating pin map:', error);
    }
}

function createBubbleMap() {
    try {
        const container = document.getElementById('bubble-map');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        const bubbleData = dashboardData.grupoPerf.data.map((grupo, idx) => ({
            type: 'scattergeo',
            mode: 'markers',
            name: grupo.grupo_operativo,
            lon: [-102.5528 + (Math.random() - 0.5) * 15],
            lat: [23.6345 + (Math.random() - 0.5) * 15],
            marker: {
                size: Math.sqrt(grupo.total_evaluaciones) * 5,
                color: parseFloat(grupo.promedio),
                colorscale: 'Portland',
                cmin: 70,
                cmax: 100,
                line: {
                    color: 'white',
                    width: 2
                },
                sizemode: 'diameter'
            },
            text: `${grupo.grupo_operativo}<br>Promedio: ${grupo.promedio}%<br>Evaluaciones: ${grupo.total_evaluaciones}`
        }));
        
        const layout = {
            geo: {
                scope: 'north america',
                projection: { type: 'mercator' },
                center: { lat: 23.6345, lon: -102.5528 },
                showland: true
            },
            height: 400,
            margin: { t: 0, b: 0, l: 0, r: 0 }
        };
        
        Plotly.newPlot(container, bubbleData, layout, { responsive: true });
        chartInstances['bubble-map'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating bubble map:', error);
    }
}

function createHeatMap() {
    try {
        const container = document.getElementById('heat-map');
        if (!container || !dashboardData.areas?.data) return;
        
        // Create grid data for heatmap
        const areas = dashboardData.areas.data.slice(0, 10);
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago'];
        
        const z = areas.map(area => 
            months.map(() => Math.random() * 30 + 70) // Simulated data
        );
        
        const data = [{
            type: 'heatmap',
            z: z,
            x: months,
            y: areas.map(a => a.area.substring(0, 20)),
            colorscale: [
                [0, '#ff0000'],
                [0.25, '#ff8800'],
                [0.5, '#ffff00'],
                [0.75, '#88ff00'],
                [1, '#00ff00']
            ],
            colorbar: {
                title: 'Performance %',
                titleside: 'right'
            }
        }];
        
        const layout = {
            height: 400,
            margin: { t: 20, b: 40, l: 150, r: 40 }
        };
        
        Plotly.newPlot(container, data, layout, { responsive: true });
        chartInstances['heat-map'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating heat map:', error);
    }
}

function create3DMap() {
    try {
        const container = document.getElementById('3d-map');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        // Create 3D surface data
        const size = 20;
        const x = Array.from({length: size}, (_, i) => i);
        const y = Array.from({length: size}, (_, i) => i);
        const z = [];
        
        for(let i = 0; i < size; i++) {
            z[i] = [];
            for(let j = 0; j < size; j++) {
                z[i][j] = Math.sin(i/3) * Math.cos(j/3) * 20 + 80 + Math.random() * 10;
            }
        }
        
        const data = [{
            type: 'surface',
            x: x,
            y: y,
            z: z,
            colorscale: 'Viridis',
            contours: {
                z: {
                    show: true,
                    usecolormap: true,
                    highlightcolor: "#42f462",
                    project: { z: true }
                }
            }
        }];
        
        const layout = {
            scene: {
                xaxis: { title: 'Longitud' },
                yaxis: { title: 'Latitud' },
                zaxis: { title: 'Performance %' },
                camera: {
                    eye: { x: 1.5, y: 1.5, z: 1.5 }
                }
            },
            height: 400,
            margin: { t: 0, b: 0, l: 0, r: 0 }
        };
        
        Plotly.newPlot(container, data, layout, { responsive: true });
        chartInstances['3d-map'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating 3D map:', error);
    }
}

function createFlowMap() {
    try {
        const container = document.getElementById('flow-map');
        if (!container) return;
        
        // Create flow/connection lines between locations
        const connections = [];
        const nodes = [];
        
        // Sample nodes (cities)
        const cities = [
            { name: 'CDMX', lat: 19.4326, lon: -99.1332, size: 30 },
            { name: 'Monterrey', lat: 25.6866, lon: -100.3161, size: 25 },
            { name: 'Guadalajara', lat: 20.6597, lon: -103.3496, size: 20 },
            { name: 'Puebla', lat: 19.0414, lon: -98.2063, size: 15 },
            { name: 'Tijuana', lat: 32.5149, lon: -117.0382, size: 18 }
        ];
        
        // Create nodes
        cities.forEach(city => {
            nodes.push({
                type: 'scattergeo',
                mode: 'markers+text',
                lon: [city.lon],
                lat: [city.lat],
                marker: {
                    size: city.size,
                    color: '#2196F3',
                    line: { color: 'white', width: 2 }
                },
                text: city.name,
                textposition: 'top center',
                name: city.name
            });
        });
        
        // Create connections
        for (let i = 0; i < cities.length - 1; i++) {
            for (let j = i + 1; j < cities.length; j++) {
                if (Math.random() > 0.5) { // Random connections
                    connections.push({
                        type: 'scattergeo',
                        mode: 'lines',
                        lon: [cities[i].lon, cities[j].lon],
                        lat: [cities[i].lat, cities[j].lat],
                        line: {
                            width: Math.random() * 4 + 1,
                            color: `rgba(33, 150, 243, ${Math.random() * 0.5 + 0.3})`
                        },
                        showlegend: false
                    });
                }
            }
        }
        
        const layout = {
            geo: {
                scope: 'north america',
                projection: { type: 'mercator' },
                center: { lat: 23.6345, lon: -102.5528 },
                showland: true,
                landcolor: 'rgb(243, 243, 243)',
                coastlinecolor: 'rgb(204, 204, 204)'
            },
            height: 400,
            margin: { t: 0, b: 0, l: 0, r: 0 },
            showlegend: false
        };
        
        Plotly.newPlot(container, [...connections, ...nodes], layout, { responsive: true });
        chartInstances['flow-map'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating flow map:', error);
    }
}

// BARS CATEGORY
function createHorizontalBars() {
    try {
        const container = document.getElementById('horizontal-bars');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        const data = dashboardData.sucursalPerf.data.slice(0, 15);
        
        const options = {
            series: [{
                name: 'Performance %',
                data: data.map(d => ({
                    x: parseFloat(d.promedio),
                    y: d.sucursal_clean,
                    fillColor: getColorByScore(parseFloat(d.promedio))
                }))
            }],
            chart: {
                type: 'bar',
                height: 400,
                toolbar: { show: false }
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    distributed: true,
                    barHeight: '75%',
                    borderRadius: 4
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function(val) {
                    return val.toFixed(1) + '%';
                },
                style: {
                    fontSize: '12px',
                    fontWeight: 600
                }
            },
            xaxis: {
                title: { text: 'Performance (%)' },
                min: 0,
                max: 100
            },
            yaxis: {
                title: { text: '' }
            },
            legend: { show: false },
            tooltip: {
                custom: function({series, seriesIndex, dataPointIndex, w}) {
                    const data = w.config.series[0].data[dataPointIndex];
                    return `<div class="custom-tooltip">
                        <strong>${data.y}</strong><br/>
                        Performance: ${data.x.toFixed(1)}%
                    </div>`;
                }
            }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['horizontal-bars'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating horizontal bars:', error);
    }
}

function createGroupedBars() {
    try {
        const container = document.getElementById('grouped-bars');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        const grupos = dashboardData.grupoPerf.data.slice(0, 6);
        
        const options = {
            series: [{
                name: 'Q1 2025',
                data: grupos.map(g => parseFloat(g.promedio) - Math.random() * 5)
            }, {
                name: 'Q2 2025',
                data: grupos.map(g => parseFloat(g.promedio))
            }],
            chart: {
                type: 'bar',
                height: 400,
                toolbar: { show: false }
            },
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: '55%',
                    borderRadius: 4
                }
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                show: true,
                width: 2,
                colors: ['transparent']
            },
            xaxis: {
                categories: grupos.map(g => g.grupo_operativo),
                labels: {
                    rotate: -45,
                    rotateAlways: true
                }
            },
            yaxis: {
                title: { text: 'Performance (%)' },
                min: 0,
                max: 100
            },
            fill: {
                opacity: 1
            },
            colors: ['#667eea', '#f093fb'],
            legend: {
                position: 'top',
                horizontalAlign: 'right'
            }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['grouped-bars'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating grouped bars:', error);
    }
}

function createStackedBars() {
    try {
        const container = document.getElementById('stacked-bars');
        if (!container || !dashboardData.areas?.data) return;
        
        const areas = dashboardData.areas.data.slice(0, 6);
        
        const options = {
            series: [{
                name: 'Excelente',
                data: areas.map(() => Math.random() * 30 + 40)
            }, {
                name: 'Bueno',
                data: areas.map(() => Math.random() * 20 + 20)
            }, {
                name: 'Regular',
                data: areas.map(() => Math.random() * 15 + 10)
            }, {
                name: 'Malo',
                data: areas.map(() => Math.random() * 10 + 5)
            }],
            chart: {
                type: 'bar',
                height: 400,
                stacked: true,
                toolbar: { show: false }
            },
            plotOptions: {
                bar: {
                    horizontal: false,
                    borderRadius: 4
                }
            },
            xaxis: {
                categories: areas.map(a => a.area.substring(0, 15) + '...'),
                labels: {
                    rotate: -45,
                    rotateAlways: true
                }
            },
            yaxis: {
                title: { text: 'Porcentaje (%)' }
            },
            fill: {
                opacity: 1
            },
            colors: ['#00ff88', '#00aaff', '#ffaa00', '#ff4444'],
            legend: {
                position: 'top',
                horizontalAlign: 'center'
            }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['stacked-bars'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating stacked bars:', error);
    }
}

function createBarWithLine() {
    try {
        const container = document.getElementById('bar-with-line');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        const data = dashboardData.sucursalPerf.data.slice(0, 10);
        
        const options = {
            series: [{
                name: 'Performance',
                type: 'column',
                data: data.map(d => parseFloat(d.promedio))
            }, {
                name: 'Meta',
                type: 'line',
                data: data.map(() => 85)
            }],
            chart: {
                height: 400,
                type: 'line',
                toolbar: { show: false }
            },
            stroke: {
                width: [0, 4],
                curve: 'smooth'
            },
            plotOptions: {
                bar: {
                    columnWidth: '50%',
                    borderRadius: 4
                }
            },
            dataLabels: {
                enabled: false
            },
            xaxis: {
                categories: data.map(d => d.sucursal_clean),
                labels: {
                    rotate: -45,
                    rotateAlways: true
                }
            },
            yaxis: [{
                title: { text: 'Performance (%)' },
                min: 0,
                max: 100
            }],
            colors: ['#667eea', '#ff4444'],
            legend: {
                position: 'top'
            }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['bar-with-line'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating bar with line:', error);
    }
}

function createBipolarBars() {
    try {
        const container = document.getElementById('bipolar-bars');
        if (!container || !dashboardData.areas?.data) return;
        
        const areas = dashboardData.areas.data.slice(0, 8);
        
        const trace1 = {
            type: 'bar',
            name: 'Por debajo de meta',
            y: areas.map(a => a.area.substring(0, 20)),
            x: areas.map(a => -(85 - parseFloat(a.promedio))),
            orientation: 'h',
            marker: { color: '#ff4444' }
        };
        
        const trace2 = {
            type: 'bar',
            name: 'Por encima de meta',
            y: areas.map(a => a.area.substring(0, 20)),
            x: areas.map(a => Math.max(0, parseFloat(a.promedio) - 85)),
            orientation: 'h',
            marker: { color: '#00ff88' }
        };
        
        const layout = {
            barmode: 'relative',
            height: 400,
            xaxis: {
                title: 'Diferencia con Meta (85%)',
                zeroline: true,
                zerolinewidth: 2,
                zerolinecolor: 'black'
            },
            margin: { l: 150 }
        };
        
        Plotly.newPlot(container, [trace1, trace2], layout, { responsive: true });
        chartInstances['bipolar-bars'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating bipolar bars:', error);
    }
}

function createWaterfallChart() {
    try {
        const container = document.getElementById('waterfall-chart');
        if (!container) return;
        
        // Waterfall data
        const data = [{
            type: 'waterfall',
            orientation: 'v',
            measure: ['relative', 'relative', 'total', 'relative', 'relative', 'relative', 'total'],
            x: ['Inicio Q1', 'Mejoras', 'Total Q1', 'Nuevas Sucursales', 'Optimización', 'Ajustes', 'Total Q2'],
            textposition: 'outside',
            text: ['+80', '+5', '85', '+3', '+4', '-2', '90'],
            y: [80, 5, 0, 3, 4, -2, 0],
            connector: {
                line: { color: 'rgb(63, 63, 63)' }
            },
            increasing: { marker: { color: '#00ff88' } },
            decreasing: { marker: { color: '#ff4444' } },
            totals: { marker: { color: '#667eea' } }
        }];
        
        const layout = {
            title: { text: '' },
            height: 400,
            showlegend: false,
            margin: { t: 20 }
        };
        
        Plotly.newPlot(container, data, layout, { responsive: true });
        chartInstances['waterfall-chart'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating waterfall chart:', error);
    }
}

// TRENDS CATEGORY
function createPredictionChart() {
    try {
        const container = document.getElementById('prediction-chart');
        if (!container) return;
        
        // Historical and predicted data
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        const historical = [82, 84, 83, 85, 87, 86, 88, 89];
        const predicted = [null, null, null, null, null, null, null, 89, 90, 91, 92, 93];
        
        const options = {
            series: [{
                name: 'Histórico',
                data: historical
            }, {
                name: 'Predicción',
                data: predicted
            }],
            chart: {
                type: 'line',
                height: 400,
                toolbar: { show: false }
            },
            stroke: {
                curve: 'smooth',
                dashArray: [0, 5],
                width: 3
            },
            xaxis: {
                categories: months
            },
            yaxis: {
                title: { text: 'Performance (%)' },
                min: 80,
                max: 95
            },
            colors: ['#667eea', '#f093fb'],
            markers: {
                size: [4, 6],
                strokeWidth: 2
            },
            annotations: {
                xaxis: [{
                    x: 'Jul',
                    borderColor: '#999',
                    label: {
                        borderColor: '#999',
                        style: {
                            color: '#fff',
                            background: '#999'
                        },
                        text: 'Inicio Predicción'
                    }
                }]
            }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['prediction-chart'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating prediction chart:', error);
    }
}

function createAreaZoomChart() {
    try {
        const container = document.getElementById('area-zoom-chart');
        if (!container) return;
        
        // Generate time series data
        const generateData = (count, yrange) => {
            const series = [];
            let baseTime = new Date('2025-01-01').getTime();
            
            for(let i = 0; i < count; i++) {
                const x = baseTime;
                const y = Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;
                series.push([x, y]);
                baseTime += 86400000; // Add 1 day
            }
            return series;
        };
        
        const options = {
            series: [{
                name: 'Performance Diario',
                data: generateData(180, { min: 75, max: 95 })
            }],
            chart: {
                type: 'area',
                height: 400,
                zoom: {
                    enabled: true,
                    type: 'x',
                    autoScaleYaxis: true
                },
                toolbar: {
                    autoSelected: 'zoom'
                }
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                curve: 'smooth',
                width: 2
            },
            fill: {
                type: 'gradient',
                gradient: {
                    shadeIntensity: 1,
                    opacityFrom: 0.7,
                    opacityTo: 0.3
                }
            },
            xaxis: {
                type: 'datetime',
                title: { text: 'Fecha' }
            },
            yaxis: {
                title: { text: 'Performance (%)' },
                min: 70,
                max: 100
            },
            colors: ['#667eea']
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['area-zoom-chart'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating area zoom chart:', error);
    }
}

function createCandlestickChart() {
    try {
        const container = document.getElementById('candlestick-chart');
        if (!container) return;
        
        // Generate candlestick data
        const generateCandlestickData = () => {
            const data = [];
            let baseTime = new Date('2025-01-01').getTime();
            let baseValue = 85;
            
            for(let i = 0; i < 60; i++) {
                const open = baseValue + Math.random() * 5 - 2.5;
                const close = open + Math.random() * 6 - 3;
                const high = Math.max(open, close) + Math.random() * 2;
                const low = Math.min(open, close) - Math.random() * 2;
                
                data.push({
                    x: new Date(baseTime),
                    y: [open, high, low, close]
                });
                
                baseTime += 86400000; // 1 day
                baseValue = close;
            }
            return data;
        };
        
        const options = {
            series: [{
                data: generateCandlestickData()
            }],
            chart: {
                type: 'candlestick',
                height: 400,
                toolbar: { show: false }
            },
            xaxis: {
                type: 'datetime'
            },
            yaxis: {
                title: { text: 'Performance Range (%)' },
                tooltip: { enabled: true }
            },
            plotOptions: {
                candlestick: {
                    colors: {
                        upward: '#00ff88',
                        downward: '#ff4444'
                    }
                }
            }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['candlestick-chart'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating candlestick chart:', error);
    }
}

function createSparklines() {
    try {
        const container = document.getElementById('sparklines');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        container.innerHTML = ''; // Clear container
        
        const grupos = dashboardData.grupoPerf.data.slice(0, 6);
        
        grupos.forEach(grupo => {
            const sparklineContainer = document.createElement('div');
            sparklineContainer.className = 'sparkline-item';
            sparklineContainer.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: 600;">${grupo.grupo_operativo}</span>
                    <span style="color: ${getColorByScore(parseFloat(grupo.promedio))}; font-weight: 600;">
                        ${grupo.promedio}%
                    </span>
                </div>
                <div id="sparkline-${grupo.grupo_operativo.replace(/\s+/g, '-')}"></div>
            `;
            container.appendChild(sparklineContainer);
            
            const options = {
                series: [{
                    data: Array.from({length: 30}, () => 
                        parseFloat(grupo.promedio) + (Math.random() - 0.5) * 10
                    )
                }],
                chart: {
                    type: 'line',
                    height: 50,
                    sparkline: { enabled: true }
                },
                stroke: {
                    curve: 'smooth',
                    width: 2
                },
                colors: [getColorByScore(parseFloat(grupo.promedio))],
                tooltip: {
                    fixed: {
                        enabled: false
                    },
                    x: { show: false },
                    y: {
                        title: {
                            formatter: function() { return ''; }
                        }
                    }
                }
            };
            
            const chart = new ApexCharts(
                sparklineContainer.querySelector(`#sparkline-${grupo.grupo_operativo.replace(/\s+/g, '-')}`), 
                options
            );
            chart.render();
        });
        
    } catch (error) {
        console.error('Error creating sparklines:', error);
    }
}

function createStreamChart() {
    try {
        const container = document.getElementById('stream-chart');
        if (!container || !dashboardData.areas?.data) return;
        
        // Generate stream data
        const areas = dashboardData.areas.data.slice(0, 5);
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul'];
        
        const traces = areas.map((area, idx) => ({
            type: 'scatter',
            mode: 'lines',
            name: area.area.substring(0, 20),
            x: months,
            y: months.map(() => Math.random() * 20 + 10 + idx * 10),
            stackgroup: 'one',
            fillcolor: getColorByIndex(idx),
            line: { width: 0 }
        }));
        
        const layout = {
            height: 400,
            margin: { t: 20 },
            xaxis: { title: 'Meses' },
            yaxis: { title: 'Volumen de Evaluaciones' },
            hovermode: 'x unified'
        };
        
        Plotly.newPlot(container, traces, layout, { responsive: true });
        chartInstances['stream-chart'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating stream chart:', error);
    }
}

function createTimelineChart() {
    try {
        const container = document.getElementById('timeline-chart');
        if (!container) return;
        
        // Timeline data
        const events = [
            { name: 'Inicio Programa', start: '2025-01-01', end: '2025-01-15', group: 'Hitos' },
            { name: 'Primera Evaluación', start: '2025-01-15', end: '2025-02-01', group: 'Evaluaciones' },
            { name: 'Capacitación Personal', start: '2025-02-01', end: '2025-02-15', group: 'Capacitación' },
            { name: 'Segunda Evaluación', start: '2025-03-01', end: '2025-03-15', group: 'Evaluaciones' },
            { name: 'Implementación Mejoras', start: '2025-03-15', end: '2025-04-01', group: 'Mejoras' },
            { name: 'Evaluación Final Q1', start: '2025-03-20', end: '2025-03-31', group: 'Evaluaciones' }
        ];
        
        const groups = ['Hitos', 'Evaluaciones', 'Capacitación', 'Mejoras'];
        const colors = ['#667eea', '#f093fb', '#00aaff', '#00ff88'];
        
        const options = {
            series: events.map(event => ({
                name: event.name,
                data: [{
                    x: event.group,
                    y: [new Date(event.start).getTime(), new Date(event.end).getTime()],
                    fillColor: colors[groups.indexOf(event.group)]
                }]
            })),
            chart: {
                height: 400,
                type: 'rangeBar',
                toolbar: { show: false }
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    distributed: true,
                    dataLabels: { hideOverflowingLabels: false }
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function(val, opts) {
                    return opts.w.globals.seriesNames[opts.seriesIndex];
                },
                style: { fontSize: '11px' }
            },
            xaxis: {
                type: 'datetime',
                title: { text: 'Línea de Tiempo 2025' }
            },
            yaxis: {
                title: { text: '' }
            },
            legend: { show: false }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['timeline-chart'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating timeline chart:', error);
    }
}

// COMPARISON CATEGORY
function createRadarComparison() {
    try {
        const container = document.getElementById('radar-comparison');
        if (!container || !dashboardData.areas?.data) return;
        
        const areas = dashboardData.areas.data.slice(0, 8);
        
        const options = {
            series: [{
                name: 'Q1 2025',
                data: areas.map(a => parseFloat(a.promedio) - Math.random() * 5)
            }, {
                name: 'Q2 2025',
                data: areas.map(a => parseFloat(a.promedio))
            }],
            chart: {
                height: 400,
                type: 'radar',
                toolbar: { show: false }
            },
            xaxis: {
                categories: areas.map(a => a.area.substring(0, 15))
            },
            yaxis: {
                min: 0,
                max: 100
            },
            colors: ['#667eea', '#f093fb'],
            markers: { size: 4 },
            fill: { opacity: 0.2 }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['radar-comparison'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating radar comparison:', error);
    }
}

function createParallelCoordinates() {
    try {
        const container = document.getElementById('parallel-coordinates');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        const data = dashboardData.sucursalPerf.data.slice(0, 20);
        
        const dimensions = [
            { label: 'Sucursal', values: data.map((d, i) => i) },
            { label: 'Performance', values: data.map(d => parseFloat(d.promedio)) },
            { label: 'Evaluaciones', values: data.map(d => d.total_evaluaciones) },
            { label: 'Tendencia', values: data.map(() => Math.random() * 100) }
        ];
        
        const trace = {
            type: 'parcoords',
            line: {
                color: data.map(d => parseFloat(d.promedio)),
                colorscale: 'Viridis',
                showscale: true
            },
            dimensions: dimensions
        };
        
        const layout = {
            height: 400,
            margin: { t: 30, b: 30 }
        };
        
        Plotly.newPlot(container, [trace], layout, { responsive: true });
        chartInstances['parallel-coordinates'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating parallel coordinates:', error);
    }
}

function createBulletCharts() {
    try {
        const container = document.getElementById('bullet-charts');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        container.innerHTML = ''; // Clear container
        
        const grupos = dashboardData.grupoPerf.data.slice(0, 4);
        
        grupos.forEach((grupo, idx) => {
            const bulletContainer = document.createElement('div');
            bulletContainer.style.marginBottom = '20px';
            bulletContainer.innerHTML = `<h4 style="margin-bottom: 10px;">${grupo.grupo_operativo}</h4>`;
            const chartDiv = document.createElement('div');
            bulletContainer.appendChild(chartDiv);
            container.appendChild(bulletContainer);
            
            const performance = parseFloat(grupo.promedio);
            const target = 85;
            
            const options = {
                series: [{
                    data: [{
                        x: 'Performance',
                        y: performance,
                        goals: [{
                            name: 'Meta',
                            value: target,
                            strokeHeight: 5,
                            strokeColor: '#775DD0'
                        }]
                    }]
                }],
                chart: {
                    height: 100,
                    type: 'bar',
                    toolbar: { show: false }
                },
                plotOptions: {
                    bar: {
                        horizontal: true,
                        distributed: true,
                        barHeight: '50%'
                    }
                },
                colors: [getColorByScore(performance)],
                dataLabels: {
                    enabled: true,
                    formatter: function(val) {
                        return val.toFixed(1) + '%';
                    }
                },
                xaxis: {
                    min: 0,
                    max: 100,
                    labels: { show: false }
                },
                yaxis: {
                    labels: { show: false }
                },
                legend: { show: false },
                grid: { show: false }
            };
            
            const chart = new ApexCharts(chartDiv, options);
            chart.render();
        });
        
    } catch (error) {
        console.error('Error creating bullet charts:', error);
    }
}

function createDumbbellChart() {
    try {
        const container = document.getElementById('dumbbell-chart');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        const data = dashboardData.sucursalPerf.data.slice(0, 10);
        
        const traces = [];
        data.forEach((sucursal, idx) => {
            const start = parseFloat(sucursal.promedio) - Math.random() * 10;
            const end = parseFloat(sucursal.promedio);
            
            // Line
            traces.push({
                type: 'scatter',
                mode: 'lines',
                x: [start, end],
                y: [idx, idx],
                line: { color: 'gray', width: 2 },
                showlegend: false
            });
            
            // Start point
            traces.push({
                type: 'scatter',
                mode: 'markers',
                x: [start],
                y: [idx],
                marker: { size: 10, color: '#ff4444' },
                name: idx === 0 ? 'Q1' : '',
                showlegend: idx === 0
            });
            
            // End point
            traces.push({
                type: 'scatter',
                mode: 'markers',
                x: [end],
                y: [idx],
                marker: { size: 10, color: '#00ff88' },
                name: idx === 0 ? 'Q2' : '',
                showlegend: idx === 0
            });
        });
        
        const layout = {
            height: 400,
            xaxis: {
                title: 'Performance (%)',
                range: [60, 100]
            },
            yaxis: {
                ticktext: data.map(d => d.sucursal_clean),
                tickvals: data.map((d, i) => i),
                automargin: true
            },
            margin: { l: 150 }
        };
        
        Plotly.newPlot(container, traces, layout, { responsive: true });
        chartInstances['dumbbell-chart'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating dumbbell chart:', error);
    }
}

function createSlopeChart() {
    try {
        const container = document.getElementById('slope-chart');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        const grupos = dashboardData.grupoPerf.data.slice(0, 6);
        
        const traces = [];
        grupos.forEach((grupo, idx) => {
            const startValue = parseFloat(grupo.promedio) - Math.random() * 10;
            const endValue = parseFloat(grupo.promedio);
            const improved = endValue > startValue;
            
            traces.push({
                type: 'scatter',
                mode: 'lines+markers+text',
                x: ['Q1 2025', 'Q2 2025'],
                y: [startValue, endValue],
                line: {
                    color: improved ? '#00ff88' : '#ff4444',
                    width: 2
                },
                marker: { size: 8 },
                text: [startValue.toFixed(1), endValue.toFixed(1)],
                textposition: ['middle left', 'middle right'],
                name: grupo.grupo_operativo
            });
        });
        
        const layout = {
            height: 400,
            xaxis: {
                title: '',
                fixedrange: true
            },
            yaxis: {
                title: 'Performance (%)',
                range: [60, 100]
            },
            showlegend: true,
            legend: {
                x: 1.1,
                y: 1
            }
        };
        
        Plotly.newPlot(container, traces, layout, { responsive: true });
        chartInstances['slope-chart'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating slope chart:', error);
    }
}

function createButterflyChart() {
    try {
        const container = document.getElementById('butterfly-chart');
        if (!container || !dashboardData.areas?.data) return;
        
        const areas = dashboardData.areas.data.slice(0, 8);
        
        const options = {
            series: [{
                name: 'Evaluaciones Positivas',
                data: areas.map(() => Math.floor(Math.random() * 50) + 50)
            }, {
                name: 'Evaluaciones Negativas',
                data: areas.map(() => -(Math.floor(Math.random() * 30) + 10))
            }],
            chart: {
                type: 'bar',
                height: 400,
                stacked: true,
                toolbar: { show: false }
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    barHeight: '80%'
                }
            },
            dataLabels: {
                enabled: false
            },
            xaxis: {
                categories: areas.map(a => a.area.substring(0, 20)),
                labels: {
                    formatter: function(val) {
                        return Math.abs(val);
                    }
                }
            },
            yaxis: {
                labels: {
                    minWidth: 150,
                    maxWidth: 150
                }
            },
            colors: ['#00ff88', '#ff4444'],
            legend: {
                position: 'top',
                horizontalAlign: 'center'
            }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['butterfly-chart'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating butterfly chart:', error);
    }
}

// DISTRIBUTION CATEGORY
function createMultilevelDonut() {
    try {
        const container = document.getElementById('multilevel-donut');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        const grupos = dashboardData.grupoPerf.data.slice(0, 5);
        const totalEval = grupos.reduce((sum, g) => sum + g.total_evaluaciones, 0);
        
        const options = {
            series: [
                ...grupos.map(g => g.total_evaluaciones),
                totalEval
            ],
            chart: {
                type: 'donut',
                height: 400
            },
            labels: [
                ...grupos.map(g => g.grupo_operativo),
                'Total'
            ],
            plotOptions: {
                pie: {
                    donut: {
                        size: '65%',
                        labels: {
                            show: true,
                            name: { show: true },
                            value: {
                                show: true,
                                formatter: function(val) {
                                    return parseInt(val);
                                }
                            },
                            total: {
                                show: true,
                                label: 'Total',
                                formatter: function(w) {
                                    return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                }
                            }
                        }
                    }
                }
            },
            colors: ['#667eea', '#f093fb', '#00aaff', '#00ff88', '#ffaa00', '#ff4444']
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['multilevel-donut'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating multilevel donut:', error);
    }
}

function createBoxPlot() {
    try {
        const container = document.getElementById('box-plot');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        const grupos = dashboardData.grupoPerf.data.slice(0, 5);
        
        const traces = grupos.map((grupo, idx) => ({
            type: 'box',
            y: Array.from({length: 50}, () => 
                parseFloat(grupo.promedio) + (Math.random() - 0.5) * 20
            ),
            name: grupo.grupo_operativo,
            boxpoints: 'outliers',
            marker: { color: getColorByIndex(idx) }
        }));
        
        const layout = {
            height: 400,
            yaxis: {
                title: 'Performance Distribution (%)',
                range: [50, 100]
            },
            showlegend: false
        };
        
        Plotly.newPlot(container, traces, layout, { responsive: true });
        chartInstances['box-plot'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating box plot:', error);
    }
}

function createViolinPlot() {
    try {
        const container = document.getElementById('violin-plot');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        const grupos = dashboardData.grupoPerf.data.slice(0, 4);
        
        const traces = grupos.map((grupo, idx) => ({
            type: 'violin',
            y: Array.from({length: 100}, () => 
                parseFloat(grupo.promedio) + (Math.random() - 0.5) * 15
            ),
            name: grupo.grupo_operativo,
            box: { visible: true },
            meanline: { visible: true },
            fillcolor: getColorByIndex(idx),
            opacity: 0.6
        }));
        
        const layout = {
            height: 400,
            yaxis: {
                title: 'Performance Distribution (%)',
                range: [60, 100]
            },
            showlegend: false
        };
        
        Plotly.newPlot(container, traces, layout, { responsive: true });
        chartInstances['violin-plot'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating violin plot:', error);
    }
}

function createRidgePlot() {
    try {
        const container = document.getElementById('ridge-plot');
        if (!container || !dashboardData.areas?.data) return;
        
        const areas = dashboardData.areas.data.slice(0, 6);
        const traces = [];
        
        areas.forEach((area, idx) => {
            const y = Array.from({length: 100}, () => 
                parseFloat(area.promedio) + (Math.random() - 0.5) * 10
            );
            
            traces.push({
                type: 'violin',
                y: y,
                name: area.area.substring(0, 20),
                side: 'positive',
                width: 3,
                points: false,
                fillcolor: getColorByIndex(idx),
                opacity: 0.7,
                meanline: { visible: true },
                yaxis: `y${idx + 1}`
            });
        });
        
        const layout = {
            height: 400,
            showlegend: false,
            xaxis: { showgrid: false, zeroline: false }
        };
        
        // Add y-axes configuration
        areas.forEach((area, idx) => {
            layout[`yaxis${idx + 1}`] = {
                showgrid: false,
                showticklabels: false,
                range: [60, 100],
                domain: [idx * 0.15, (idx + 1) * 0.15]
            };
        });
        
        Plotly.newPlot(container, traces, layout, { responsive: true });
        chartInstances['ridge-plot'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating ridge plot:', error);
    }
}

function createJoyPlot() {
    try {
        const container = document.getElementById('joy-plot');
        if (!container) return;
        
        // Similar to ridge plot but with overlapping distributions
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'];
        const traces = [];
        
        months.forEach((month, idx) => {
            const x = Array.from({length: 200}, (_, i) => i);
            const y = x.map(val => 
                Math.exp(-Math.pow(val - 100 - idx * 5, 2) / (2 * Math.pow(20, 2))) * 50 + idx * 10
            );
            
            traces.push({
                type: 'scatter',
                mode: 'lines',
                x: x,
                y: y,
                fill: 'tozeroy',
                fillcolor: getColorByIndex(idx),
                opacity: 0.6,
                name: month
            });
        });
        
        const layout = {
            height: 400,
            xaxis: { title: 'Performance Score' },
            yaxis: { title: 'Density + Time Offset' },
            hovermode: 'x unified'
        };
        
        Plotly.newPlot(container, traces, layout, { responsive: true });
        chartInstances['joy-plot'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating joy plot:', error);
    }
}

function createBeeswarm() {
    try {
        const container = document.getElementById('beeswarm');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        const data = dashboardData.sucursalPerf.data.slice(0, 100);
        
        // Create beeswarm effect by adding jitter to x position
        const trace = {
            type: 'scatter',
            mode: 'markers',
            x: data.map(() => Math.random() * 0.8 - 0.4),
            y: data.map(d => parseFloat(d.promedio)),
            marker: {
                size: 8,
                color: data.map(d => parseFloat(d.promedio)),
                colorscale: 'Viridis',
                showscale: true,
                colorbar: {
                    title: 'Performance %'
                }
            },
            text: data.map(d => d.sucursal_clean),
            hovertemplate: '%{text}<br>Performance: %{y:.1f}%<extra></extra>'
        };
        
        const layout = {
            height: 400,
            xaxis: {
                showgrid: false,
                showticklabels: false,
                title: ''
            },
            yaxis: {
                title: 'Performance (%)',
                range: [60, 100]
            },
            margin: { l: 60, r: 60 }
        };
        
        Plotly.newPlot(container, [trace], layout, { responsive: true });
        chartInstances['beeswarm'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating beeswarm:', error);
    }
}

// GAUGES CATEGORY
function createClassicGauge() {
    try {
        const container = document.getElementById('classic-gauge');
        if (!container || !dashboardData.summary?.data) return;
        
        const promedio = parseFloat(dashboardData.summary.data.promedio_general || 0);
        
        Highcharts.chart(container, {
            chart: {
                type: 'gauge',
                plotBackgroundColor: null,
                plotBackgroundImage: null,
                plotBorderWidth: 0,
                plotShadow: false,
                height: 300
            },
            title: { text: null },
            pane: {
                startAngle: -150,
                endAngle: 150,
                background: [{
                    backgroundColor: {
                        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
                        stops: [[0, '#FFF'], [1, '#333']]
                    },
                    borderWidth: 0,
                    outerRadius: '109%'
                }, {
                    backgroundColor: {
                        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
                        stops: [[0, '#333'], [1, '#FFF']]
                    },
                    borderWidth: 1,
                    outerRadius: '107%'
                }, {
                    backgroundColor: '#DDD',
                    borderWidth: 0,
                    outerRadius: '105%',
                    innerRadius: '103%'
                }]
            },
            yAxis: {
                min: 0,
                max: 100,
                minorTickInterval: 'auto',
                minorTickWidth: 1,
                minorTickLength: 10,
                minorTickPosition: 'inside',
                minorTickColor: '#666',
                tickPixelInterval: 30,
                tickWidth: 2,
                tickPosition: 'inside',
                tickLength: 10,
                tickColor: '#666',
                labels: {
                    step: 2,
                    rotation: 'auto'
                },
                title: {
                    text: 'Performance %'
                },
                plotBands: [{
                    from: 0,
                    to: 60,
                    color: '#DF5353' // red
                }, {
                    from: 60,
                    to: 80,
                    color: '#DDDF0D' // yellow
                }, {
                    from: 80,
                    to: 100,
                    color: '#55BF3B' // green
                }]
            },
            series: [{
                name: 'Performance',
                data: [promedio],
                tooltip: {
                    valueSuffix: ' %'
                }
            }],
            credits: { enabled: false }
        });
        
        chartInstances['classic-gauge'] = { type: 'highcharts', instance: container };
        
    } catch (error) {
        console.error('Error creating classic gauge:', error);
    }
}

function createModernGauge() {
    try {
        const container = document.getElementById('modern-gauge');
        if (!container || !dashboardData.summary?.data) return;
        
        const promedio = parseFloat(dashboardData.summary.data.promedio_general || 0);
        
        const options = {
            series: [promedio],
            chart: {
                height: 300,
                type: 'radialBar',
                offsetY: -10
            },
            plotOptions: {
                radialBar: {
                    startAngle: -135,
                    endAngle: 135,
                    hollow: {
                        margin: 0,
                        size: '70%',
                        background: '#fff',
                        image: undefined,
                        position: 'front',
                        dropShadow: {
                            enabled: true,
                            top: 3,
                            left: 0,
                            blur: 4,
                            opacity: 0.24
                        }
                    },
                    track: {
                        background: '#fff',
                        strokeWidth: '67%',
                        margin: 0,
                        dropShadow: {
                            enabled: true,
                            top: -3,
                            left: 0,
                            blur: 4,
                            opacity: 0.35
                        }
                    },
                    dataLabels: {
                        show: true,
                        name: {
                            offsetY: -10,
                            show: true,
                            color: '#888',
                            fontSize: '17px'
                        },
                        value: {
                            formatter: function(val) {
                                return parseInt(val) + "%";
                            },
                            color: '#111',
                            fontSize: '36px',
                            show: true
                        }
                    }
                }
            },
            fill: {
                type: 'gradient',
                gradient: {
                    shade: 'dark',
                    type: 'horizontal',
                    shadeIntensity: 0.5,
                    gradientToColors: ['#ABE5A1'],
                    inverseColors: true,
                    opacityFrom: 1,
                    opacityTo: 1,
                    stops: [0, 100]
                }
            },
            stroke: {
                lineCap: 'round'
            },
            labels: ['Performance'],
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['modern-gauge'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating modern gauge:', error);
    }
}

function createProgressBars() {
    try {
        const container = document.getElementById('progress-bars');
        if (!container || !dashboardData.areas?.data) return;
        
        container.innerHTML = ''; // Clear container
        
        const areas = dashboardData.areas.data.slice(0, 6);
        
        areas.forEach((area, idx) => {
            const progressContainer = document.createElement('div');
            progressContainer.style.marginBottom = '15px';
            
            const performance = parseFloat(area.promedio);
            const color = getColorByScore(performance);
            
            progressContainer.innerHTML = `
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-weight: 600; font-size: 14px;">${area.area.substring(0, 30)}</span>
                    <span style="font-weight: 600; color: ${color};">${performance.toFixed(1)}%</span>
                </div>
                <div id="progress-${idx}"></div>
            `;
            container.appendChild(progressContainer);
            
            const options = {
                series: [performance],
                chart: {
                    height: 30,
                    type: 'radialBar',
                    sparkline: { enabled: true }
                },
                plotOptions: {
                    radialBar: {
                        hollow: { size: '0%' },
                        track: { background: '#e7e7e7' },
                        dataLabels: { show: false }
                    }
                },
                colors: [color]
            };
            
            const chart = new ApexCharts(
                progressContainer.querySelector(`#progress-${idx}`), 
                options
            );
            chart.render();
        });
        
    } catch (error) {
        console.error('Error creating progress bars:', error);
    }
}

function createSemiCircleGauge() {
    try {
        const container = document.getElementById('semi-circle-gauge');
        if (!container || !dashboardData.summary?.data) return;
        
        const promedio = parseFloat(dashboardData.summary.data.promedio_general || 0);
        
        Highcharts.chart(container, {
            chart: {
                type: 'solidgauge',
                height: 250
            },
            title: null,
            pane: {
                center: ['50%', '85%'],
                size: '140%',
                startAngle: -90,
                endAngle: 90,
                background: {
                    backgroundColor: '#EEE',
                    innerRadius: '60%',
                    outerRadius: '100%',
                    shape: 'arc'
                }
            },
            tooltip: { enabled: false },
            yAxis: {
                min: 0,
                max: 100,
                stops: [
                    [0.1, '#DF5353'], // red
                    [0.5, '#DDDF0D'], // yellow
                    [0.9, '#55BF3B'] // green
                ],
                lineWidth: 0,
                tickWidth: 0,
                minorTickInterval: null,
                tickAmount: 2,
                title: {
                    y: -70,
                    text: 'Performance'
                },
                labels: { y: 16 }
            },
            plotOptions: {
                solidgauge: {
                    dataLabels: {
                        y: 5,
                        borderWidth: 0,
                        useHTML: true
                    }
                }
            },
            series: [{
                name: 'Performance',
                data: [promedio],
                dataLabels: {
                    format: '<div style="text-align:center">' +
                        '<span style="font-size:25px">{y}%</span><br/>' +
                        '<span style="font-size:12px;opacity:0.4">General</span>' +
                        '</div>'
                }
            }],
            credits: { enabled: false }
        });
        
        chartInstances['semi-circle-gauge'] = { type: 'highcharts', instance: container };
        
    } catch (error) {
        console.error('Error creating semi-circle gauge:', error);
    }
}

function createActivityGauge() {
    try {
        const container = document.getElementById('activity-gauge');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        const grupos = dashboardData.grupoPerf.data.slice(0, 3);
        
        const options = {
            series: grupos.map(g => parseFloat(g.promedio)),
            chart: {
                height: 300,
                type: 'radialBar'
            },
            plotOptions: {
                radialBar: {
                    offsetY: 0,
                    startAngle: 0,
                    endAngle: 270,
                    hollow: {
                        margin: 5,
                        size: '30%',
                        background: 'transparent',
                        image: undefined
                    },
                    dataLabels: {
                        name: {
                            show: true,
                            fontSize: '16px'
                        },
                        value: {
                            show: true,
                            fontSize: '14px',
                            formatter: function(val) {
                                return val.toFixed(1) + '%';
                            }
                        }
                    }
                }
            },
            colors: ['#667eea', '#f093fb', '#00aaff'],
            labels: grupos.map(g => g.grupo_operativo),
            legend: {
                show: true,
                floating: true,
                fontSize: '13px',
                position: 'left',
                offsetX: 50,
                offsetY: 10,
                labels: {
                    useSeriesColors: true
                },
                formatter: function(seriesName, opts) {
                    return seriesName + ":  " + opts.w.globals.series[opts.seriesIndex].toFixed(1) + '%';
                },
                itemMargin: {
                    horizontal: 3
                }
            }
        };
        
        const chart = new ApexCharts(container, options);
        chart.render();
        chartInstances['activity-gauge'] = { type: 'apex', instance: chart };
        
    } catch (error) {
        console.error('Error creating activity gauge:', error);
    }
}

function createSpeedometer() {
    try {
        const container = document.getElementById('speedometer');
        if (!container || !dashboardData.summary?.data) return;
        
        const promedio = parseFloat(dashboardData.summary.data.promedio_general || 0);
        
        const data = [{
            domain: { x: [0, 1], y: [0, 1] },
            value: promedio,
            title: { text: "Performance Score", font: { size: 24 } },
            type: "indicator",
            mode: "gauge+number+delta",
            delta: { reference: 85, increasing: { color: "#00ff88" } },
            gauge: {
                axis: { range: [null, 100], tickwidth: 1, tickcolor: "darkblue" },
                bar: { color: getColorByScore(promedio) },
                bgcolor: "white",
                borderwidth: 2,
                bordercolor: "gray",
                steps: [
                    { range: [0, 60], color: "#ffebee" },
                    { range: [60, 80], color: "#fff8e1" },
                    { range: [80, 100], color: "#e8f5e9" }
                ],
                threshold: {
                    line: { color: "red", width: 4 },
                    thickness: 0.75,
                    value: 85
                }
            }
        }];
        
        const layout = {
            margin: { t: 25, r: 25, l: 25, b: 25 },
            height: 300,
            font: { color: "darkblue", family: "Arial" }
        };
        
        Plotly.newPlot(container, data, layout, { responsive: true });
        chartInstances['speedometer'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating speedometer:', error);
    }
}

// ADVANCED CATEGORY
function createSunburst() {
    try {
        const container = document.getElementById('sunburst');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        // Prepare hierarchical data
        const estados = {};
        dashboardData.sucursalPerf.data.forEach(sucursal => {
            const estado = sucursal.estado;
            const grupo = sucursal.grupo_operativo;
            
            if (!estados[estado]) {
                estados[estado] = {};
            }
            if (!estados[estado][grupo]) {
                estados[estado][grupo] = [];
            }
            estados[estado][grupo].push({
                name: sucursal.sucursal_clean,
                value: sucursal.total_evaluaciones
            });
        });
        
        const data = {
            name: 'Total',
            children: Object.entries(estados).map(([estado, grupos]) => ({
                name: estado,
                children: Object.entries(grupos).map(([grupo, sucursales]) => ({
                    name: grupo,
                    children: sucursales
                }))
            }))
        };
        
        Highcharts.chart(container, {
            chart: {
                height: 400
            },
            series: [{
                type: 'sunburst',
                data: Highcharts.sunburstDataLabels(data),
                allowDrillToNode: true,
                cursor: 'pointer',
                dataLabels: {
                    format: '{point.name}',
                    filter: {
                        property: 'innerArcLength',
                        operator: '>',
                        value: 16
                    }
                },
                levels: [{
                    level: 1,
                    levelIsConstant: false,
                    dataLabels: {
                        filter: {
                            property: 'outerArcLength',
                            operator: '>',
                            value: 64
                        }
                    }
                }, {
                    level: 2,
                    colorByPoint: true
                }]
            }],
            title: { text: null },
            credits: { enabled: false }
        });
        
        chartInstances['sunburst'] = { type: 'highcharts', instance: container };
        
    } catch (error) {
        console.error('Error creating sunburst:', error);
    }
}

function createNetworkGraph() {
    try {
        const container = document.getElementById('network-graph');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        // Create network nodes and links
        const nodes = [];
        const links = [];
        
        // Central node
        nodes.push({
            id: 'central',
            label: 'Supervisión\nOperativa',
            size: 30,
            color: '#667eea'
        });
        
        // Group nodes
        dashboardData.grupoPerf.data.forEach((grupo, idx) => {
            const nodeId = `grupo-${idx}`;
            nodes.push({
                id: nodeId,
                label: grupo.grupo_operativo,
                size: Math.sqrt(grupo.total_evaluaciones) * 2,
                color: getColorByScore(parseFloat(grupo.promedio))
            });
            
            links.push({
                source: 'central',
                target: nodeId,
                value: grupo.total_evaluaciones
            });
        });
        
        // Add some inter-group connections
        for (let i = 0; i < nodes.length - 1; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                if (Math.random() > 0.7 && nodes[i].id !== 'central' && nodes[j].id !== 'central') {
                    links.push({
                        source: nodes[i].id,
                        target: nodes[j].id,
                        value: Math.random() * 10
                    });
                }
            }
        }
        
        // D3 Force Simulation
        const width = container.offsetWidth;
        const height = 400;
        
        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));
        
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .style('stroke', '#999')
            .style('stroke-opacity', 0.6)
            .style('stroke-width', d => Math.sqrt(d.value));
        
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('r', d => d.size)
            .style('fill', d => d.color)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        const label = svg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .text(d => d.label)
            .style('font-size', '12px')
            .style('text-anchor', 'middle');
        
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            label
                .attr('x', d => d.x)
                .attr('y', d => d.y + 4);
        });
        
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
        
        chartInstances['network-graph'] = { type: 'd3', instance: svg };
        
    } catch (error) {
        console.error('Error creating network graph:', error);
    }
}

function create3DScatter() {
    try {
        const container = document.getElementById('3d-scatter');
        if (!container || !dashboardData.sucursalPerf?.data) return;
        
        const data = dashboardData.sucursalPerf.data.slice(0, 50);
        
        const trace = {
            type: 'scatter3d',
            mode: 'markers',
            x: data.map(d => d.total_evaluaciones),
            y: data.map(d => parseFloat(d.promedio)),
            z: data.map(() => Math.random() * 50 + 50), // Simulated third dimension
            marker: {
                size: 8,
                color: data.map(d => parseFloat(d.promedio)),
                colorscale: 'Viridis',
                showscale: true,
                colorbar: {
                    title: 'Performance %'
                }
            },
            text: data.map(d => d.sucursal_clean),
            hovertemplate: '%{text}<br>Evaluaciones: %{x}<br>Performance: %{y:.1f}%<br>Índice: %{z:.1f}<extra></extra>'
        };
        
        const layout = {
            height: 400,
            scene: {
                xaxis: { title: 'Total Evaluaciones' },
                yaxis: { title: 'Performance (%)' },
                zaxis: { title: 'Índice Compuesto' },
                camera: {
                    eye: { x: 1.5, y: 1.5, z: 0.5 }
                }
            },
            margin: { t: 0, b: 0, l: 0, r: 0 }
        };
        
        Plotly.newPlot(container, [trace], layout, { responsive: true });
        chartInstances['3d-scatter'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating 3D scatter:', error);
    }
}

function createChordDiagram() {
    try {
        const container = document.getElementById('chord-diagram');
        if (!container || !dashboardData.grupoPerf?.data) return;
        
        // Create chord diagram showing relationships between grupos
        const grupos = dashboardData.grupoPerf.data.slice(0, 6);
        const matrix = [];
        
        // Create relationship matrix
        for (let i = 0; i < grupos.length; i++) {
            matrix[i] = [];
            for (let j = 0; j < grupos.length; j++) {
                if (i === j) {
                    matrix[i][j] = 0;
                } else {
                    matrix[i][j] = Math.floor(Math.random() * 50) + 10;
                }
            }
        }
        
        // Use D3 to create chord diagram
        const width = container.offsetWidth;
        const height = 400;
        const outerRadius = Math.min(width, height) * 0.5 - 40;
        const innerRadius = outerRadius - 30;
        
        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', `translate(${width/2},${height/2})`);
        
        const chord = d3.chord()
            .padAngle(0.05)
            .sortSubgroups(d3.descending);
        
        const arc = d3.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius);
        
        const ribbon = d3.ribbon()
            .radius(innerRadius);
        
        const color = d3.scaleOrdinal()
            .domain(d3.range(grupos.length))
            .range(['#667eea', '#f093fb', '#00aaff', '#00ff88', '#ffaa00', '#ff4444']);
        
        const chords = chord(matrix);
        
        // Add groups
        const group = svg.append('g')
            .selectAll('g')
            .data(chords.groups)
            .enter().append('g');
        
        group.append('path')
            .style('fill', d => color(d.index))
            .style('stroke', d => d3.rgb(color(d.index)).darker())
            .attr('d', arc);
        
        // Add ribbons
        svg.append('g')
            .attr('fill-opacity', 0.67)
            .selectAll('path')
            .data(chords)
            .enter().append('path')
            .attr('d', ribbon)
            .style('fill', d => color(d.target.index))
            .style('stroke', d => d3.rgb(color(d.target.index)).darker());
        
        // Add labels
        group.append('text')
            .each(d => { d.angle = (d.startAngle + d.endAngle) / 2; })
            .attr('dy', '.35em')
            .attr('transform', d => `
                rotate(${(d.angle * 180 / Math.PI - 90)})
                translate(${outerRadius + 10})
                ${d.angle > Math.PI ? 'rotate(180)' : ''}
            `)
            .style('text-anchor', d => d.angle > Math.PI ? 'end' : null)
            .style('font-size', '12px')
            .text((d, i) => grupos[i].grupo_operativo);
        
        chartInstances['chord-diagram'] = { type: 'd3', instance: svg };
        
    } catch (error) {
        console.error('Error creating chord diagram:', error);
    }
}

function createAlluvialDiagram() {
    try {
        const container = document.getElementById('alluvial-diagram');
        if (!container) return;
        
        // Create flow data
        const data = {
            type: "sankey",
            orientation: "h",
            node: {
                pad: 15,
                thickness: 30,
                line: {
                    color: "black",
                    width: 0.5
                },
                label: ["Q1 Bajo", "Q1 Medio", "Q1 Alto", "Q2 Bajo", "Q2 Medio", "Q2 Alto", "Q3 Bajo", "Q3 Medio", "Q3 Alto"],
                color: ["#ff4444", "#ffaa00", "#00ff88", "#ff4444", "#ffaa00", "#00ff88", "#ff4444", "#ffaa00", "#00ff88"]
            },
            link: {
                source: [0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
                target: [3, 4, 3, 4, 5, 4, 5, 6, 7, 6, 7, 7, 8],
                value: [8, 4, 2, 8, 4, 2, 8, 4, 2, 8, 12, 2, 16]
            }
        };
        
        const layout = {
            title: null,
            height: 400,
            font: { size: 12 },
            margin: { t: 20, b: 20 }
        };
        
        Plotly.newPlot(container, [data], layout, { responsive: true });
        chartInstances['alluvial-diagram'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating alluvial diagram:', error);
    }
}

function createPolarChart() {
    try {
        const container = document.getElementById('polar-chart');
        if (!container || !dashboardData.areas?.data) return;
        
        const areas = dashboardData.areas.data.slice(0, 12);
        
        const data = [{
            type: 'scatterpolar',
            r: areas.map(a => parseFloat(a.promedio)),
            theta: areas.map((a, i) => i * 30),
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.3)',
            line: { color: '#667eea' },
            name: 'Performance'
        }, {
            type: 'scatterpolar',
            r: areas.map(() => 85),
            theta: areas.map((a, i) => i * 30),
            mode: 'lines',
            line: { color: '#ff4444', dash: 'dash' },
            name: 'Meta'
        }];
        
        const layout = {
            polar: {
                radialaxis: {
                    visible: true,
                    range: [0, 100]
                },
                angularaxis: {
                    tickmode: 'array',
                    tickvals: areas.map((a, i) => i * 30),
                    ticktext: areas.map(a => a.area.substring(0, 10))
                }
            },
            height: 400,
            showlegend: true
        };
        
        Plotly.newPlot(container, data, layout, { responsive: true });
        chartInstances['polar-chart'] = { type: 'plotly', instance: container };
        
    } catch (error) {
        console.error('Error creating polar chart:', error);
    }
}

// Utility Functions
function getColorByScore(score) {
    if (score >= 95) return '#00ff88';
    if (score >= 85) return '#00aaff';
    if (score >= 75) return '#ffaa00';
    return '#ff4444';
}

function getColorByIndex(index) {
    const colors = ['#667eea', '#f093fb', '#00aaff', '#00ff88', '#ffaa00', '#ff4444'];
    return colors[index % colors.length];
}

function showLoading(show) {
    const loader = document.getElementById('loading-overlay');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

function exportChart(chartId) {
    const chartInfo = chartInstances[chartId];
    if (!chartInfo) return;
    
    try {
        if (chartInfo.type === 'plotly') {
            Plotly.downloadImage(chartInfo.instance, {
                format: 'png',
                width: 1200,
                height: 800,
                filename: `chart-${chartId}-${Date.now()}`
            });
        } else if (chartInfo.type === 'apex') {
            chartInfo.instance.dataURI().then(({ imgURI }) => {
                const link = document.createElement('a');
                link.href = imgURI;
                link.download = `chart-${chartId}-${Date.now()}.png`;
                link.click();
            });
        } else {
            showNotification('Export not available for this chart type', 'warning');
        }
    } catch (error) {
        console.error('Error exporting chart:', error);
        showNotification('Error al exportar el gráfico', 'error');
    }
}

// Initialize after all functions are defined
console.log('✅ Gráficos Avanzados Demo JavaScript cargado');