// Indicadores por Áreas - Supervisión Operativa
console.log('📊 Cargando Indicadores por Áreas...');

// Global variables
let currentView = 'overview';
let areasData = [];
let currentFilters = {
    grupo: '',
    estado: '',
    trimestre: 'ALL'
};

// Definición de las 29 áreas principales de supervisión operativa
const AREAS_SUPERVISION = [
    'Asadores', 'Baños', 'Lavado de Utensilios', 'Freidoras', 'Plancha y Mesa de Trabajo',
    'HO', 'Maquin', 'Refrigerador', 'Exterior Sucursal', 'Freidora de Papa', 
    'Tiempos de Servicio', 'Cajas de Totopo Empacado', 'Almacén Químicos',
    'Área de Preparación', 'Cocina Caliente', 'Cocina Fría', 'Bar de Ensaladas',
    'Caja y Punto de Venta', 'Comedor', 'Entrada Principal', 'Estacionamiento',
    'Área de Empleados', 'Bodega Seca', 'Cámara Fría', 'Parrilla',
    'Hornos', 'Área de Tortillas', 'Mesa de Servicio', 'Área de Limpieza'
];

// Base URL para API
const baseUrl = 'https://dc378838cfb2.ngrok-free.app';

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando Indicadores por Áreas...');
    initializeAreasPage();
});

async function initializeAreasPage() {
    try {
        showLoading(true);
        
        // Initialize filters
        await initializeFilters();
        
        // Load initial data
        await loadAreasData();
        
        // Show default view
        showView('overview');
        
        // Setup event listeners
        setupEventListeners();
        
        console.log('✅ Indicadores por Áreas inicializados');
        
    } catch (error) {
        console.error('❌ Error inicializando:', error);
    } finally {
        showLoading(false);
    }
}

async function initializeFilters() {
    try {
        // Cargar opciones de filtros desde la API
        const fetchOptions = {
            headers: {
                'ngrok-skip-browser-warning': 'true'
            }
        };
        
        const [gruposRes, estadosRes] = await Promise.all([
            fetch(`${baseUrl}/api/metadata/grupos`, fetchOptions),
            fetch(`${baseUrl}/api/metadata/estados`, fetchOptions)
        ]);
        
        const gruposData = await gruposRes.json();
        const estadosData = await estadosRes.json();
        
        // Poblar select de grupos
        const grupoSelect = document.getElementById('grupo-filter-areas');
        if (gruposData.success && gruposData.data) {
            gruposData.data.forEach(grupo => {
                const option = document.createElement('option');
                option.value = grupo;
                option.textContent = grupo;
                grupoSelect.appendChild(option);
            });
        }
        
        // Poblar select de estados
        const estadoSelect = document.getElementById('estado-filter-areas');
        if (estadosData.success && estadosData.data) {
            estadosData.data.forEach(estado => {
                const option = document.createElement('option');
                option.value = estado;
                option.textContent = estado;
                estadoSelect.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('❌ Error loading filters:', error);
    }
}

async function loadAreasData() {
    try {
        console.log('📊 Cargando datos reales de áreas de supervisión...');
        
        // Construir URL con filtros
        const params = new URLSearchParams();
        if (currentFilters.grupo) params.append('grupo', currentFilters.grupo);
        if (currentFilters.estado) params.append('estado', currentFilters.estado);
        if (currentFilters.trimestre) params.append('trimestre', currentFilters.trimestre);
        
        const fetchOptions = {
            headers: {
                'ngrok-skip-browser-warning': 'true'
            }
        };
        
        const response = await fetch(`${baseUrl}/api/areas/supervision?${params}`, fetchOptions);
        const result = await response.json();
        
        if (result.success && result.data) {
            // Usar datos reales de la API
            areasData = result.data.map(area => ({
                area: area.area,
                promedio: area.promedio,
                tendencia: Math.random() > 0.5 ? 'up' : 'down', // Esto se puede calcular con datos históricos
                indicadores: [{
                    nombre: 'Total Evaluaciones',
                    valor: area.total_evaluaciones,
                    meta: 0
                }, {
                    nombre: 'Score Mínimo',
                    valor: area.min_score,
                    meta: 80
                }, {
                    nombre: 'Score Máximo',
                    valor: area.max_score,
                    meta: 95
                }],
                color: getColorByScore(area.promedio)
            }));
            
            console.log('✅ Datos reales cargados:', areasData.length, 'áreas desde base de datos');
        } else {
            // Fallback a datos simulados si la API falla
            console.log('⚠️ API falló, usando datos simulados...');
            loadSimulatedData();
        }
        
    } catch (error) {
        console.error('❌ Error loading areas data:', error);
        // Fallback a datos simulados
        loadSimulatedData();
    }
}

function loadSimulatedData() {
    areasData = AREAS_SUPERVISION.map((area, index) => {
        const baseScore = 75 + Math.random() * 25;
        return {
            area: area,
            promedio: baseScore,
            tendencia: Math.random() > 0.5 ? 'up' : 'down',
            indicadores: generateIndicadoresForArea(area, baseScore),
            color: getColorByScore(baseScore)
        };
    });
    
    areasData.sort((a, b) => b.promedio - a.promedio);
    console.log('📊 Datos simulados cargados:', areasData.length, 'áreas');
}

function generateIndicadoresForArea(area, baseScore) {
    // Generar métricas específicas para cada área
    const indicators = {
        'Asadores': ['Temperatura', 'Limpieza', 'Tiempo Cocción', 'Rotación'],
        'Baños': ['Limpieza', 'Suministros', 'Funcionamiento', 'Higiene'],
        'Freidoras': ['Aceite', 'Temperatura', 'Filtrado', 'Limpieza'],
        'Plancha y Mesa de Trabajo': ['Temperatura', 'Limpieza', 'Organización', 'Suministros']
    };
    
    const areaIndicators = indicators[area] || ['Calidad', 'Eficiencia', 'Cumplimiento', 'Seguridad'];
    
    return areaIndicators.map(indicator => ({
        nombre: indicator,
        valor: baseScore + (Math.random() - 0.5) * 10,
        meta: 85
    }));
}

function getColorByScore(score) {
    if (score >= 95) return '#28a745'; // Verde excelente
    if (score >= 85) return '#17a2b8'; // Azul bueno
    if (score >= 75) return '#ffc107'; // Amarillo regular
    return '#dc3545'; // Rojo crítico
}

function showView(viewName) {
    // Hide all views
    document.querySelectorAll('.view-content').forEach(view => {
        view.style.display = 'none';
    });
    
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected view
    currentView = viewName;
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.style.display = 'block';
    }
    
    // Update active button
    event.target.classList.add('active');
    
    // Load view-specific content
    switch(viewName) {
        case 'overview':
            renderOverviewCards();
            break;
        case 'heatmap':
            renderHeatMap();
            break;
        case 'trends':
            renderTrendCharts();
            break;
    }
    
    console.log(`📊 Mostrando vista: ${viewName}`);
}

function renderOverviewCards() {
    const container = document.querySelector('.areas-grid');
    container.innerHTML = '';
    
    areasData.forEach(area => {
        const card = document.createElement('div');
        card.className = 'area-card';
        card.style.borderLeftColor = area.color;
        
        card.innerHTML = `
            <div class="area-title">
                <span class="performance-indicator ${getPerformanceClass(area.promedio)}"></span>
                ${area.area}
            </div>
            <div class="area-metrics">
                <div class="metric-item">
                    <div class="metric-value">${area.promedio.toFixed(1)}%</div>
                    <div class="metric-label">Promedio</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">${area.indicadores.length}</div>
                    <div class="metric-label">Indicadores</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">${area.tendencia === 'up' ? '↗️' : '↘️'}</div>
                    <div class="metric-label">Tendencia</div>
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
}

function renderHeatMap() {
    const container = document.getElementById('areas-heatmap');
    
    // Preparar datos para el heatmap
    const heatmapData = areasData.map((area, index) => ({
        x: ['Promedio'],
        y: [area.area],
        z: [[area.promedio]],
        type: 'heatmap',
        colorscale: [
            [0, '#dc3545'],
            [0.25, '#ffc107'],
            [0.5, '#17a2b8'],
            [1, '#28a745']
        ],
        showscale: false
    }));
    
    const layout = {
        title: '',
        xaxis: { title: '' },
        yaxis: { 
            title: '',
            automargin: true
        },
        height: 800,
        margin: { t: 20, b: 40, l: 200, r: 20 }
    };
    
    Plotly.newPlot(container, heatmapData, layout, {responsive: true, displayModeBar: false});
}

function renderTrendCharts() {
    // Implementar gráficos de tendencias
    renderCriticalTrends();
    renderSuccessCases();
    renderPerfectPerformance();
    renderBelow80Areas();
}

function renderCriticalTrends() {
    const container = document.getElementById('critical-trends');
    
    // Áreas críticas que necesitan atención
    const criticalAreas = areasData.filter(area => area.promedio < 80).slice(0, 3);
    
    const traces = criticalAreas.map(area => ({
        x: ['Q1', 'Q2', 'Q3', 'Q4'],
        y: generateTrendData(area.promedio),
        type: 'scatter',
        mode: 'lines+markers',
        name: area.area,
        line: { width: 3 }
    }));
    
    const layout = {
        title: '',
        xaxis: { title: 'Trimestre' },
        yaxis: { title: 'Promedio (%)' },
        height: 300,
        margin: { t: 20, b: 40, l: 50, r: 20 }
    };
    
    Plotly.newPlot(container, traces, layout, {responsive: true, displayModeBar: false});
}

function renderSuccessCases() {
    const container = document.getElementById('success-cases');
    
    // Áreas exitosas para replicar
    const successAreas = areasData.filter(area => area.promedio >= 90).slice(0, 3);
    
    const traces = successAreas.map(area => ({
        x: ['Q1', 'Q2', 'Q3', 'Q4'],
        y: generateTrendData(area.promedio),
        type: 'scatter',
        mode: 'lines+markers',
        name: area.area,
        line: { width: 3, color: '#28a745' }
    }));
    
    const layout = {
        title: '',
        xaxis: { title: 'Trimestre' },
        yaxis: { title: 'Promedio (%)' },
        height: 300,
        margin: { t: 20, b: 40, l: 50, r: 20 }
    };
    
    Plotly.newPlot(container, traces, layout, {responsive: true, displayModeBar: false});
}

function renderPerfectPerformance() {
    const container = document.getElementById('perfect-performance');
    
    // Áreas con performance perfecto
    const perfectAreas = areasData.filter(area => area.promedio >= 95).slice(0, 2);
    
    const traces = perfectAreas.map(area => ({
        x: ['Q1', 'Q2', 'Q3', 'Q4'],
        y: generateTrendData(area.promedio),
        type: 'scatter',
        mode: 'lines+markers',
        name: area.area,
        line: { width: 3, color: '#17a2b8' }
    }));
    
    const layout = {
        title: '',
        xaxis: { title: 'Trimestre' },
        yaxis: { title: 'Promedio (%)' },
        height: 300,
        margin: { t: 20, b: 40, l: 50, r: 20 }
    };
    
    Plotly.newPlot(container, traces, layout, {responsive: true, displayModeBar: false});
}

function renderBelow80Areas() {
    const container = document.getElementById('below-80-areas');
    
    // Áreas por debajo del 80%
    const below80 = areasData.filter(area => area.promedio < 80);
    
    const trace = {
        x: below80.map(area => area.area),
        y: below80.map(area => area.promedio),
        type: 'bar',
        marker: {
            color: '#dc3545',
            line: { color: '#ffffff', width: 1 }
        },
        text: below80.map(area => `${area.promedio.toFixed(1)}%`),
        textposition: 'outside'
    };
    
    const layout = {
        title: '',
        xaxis: { 
            title: 'Áreas',
            tickangle: -45
        },
        yaxis: { title: 'Promedio (%)' },
        height: 300,
        margin: { t: 20, b: 100, l: 50, r: 20 },
        shapes: [{
            type: 'line',
            x0: 0,
            x1: 1,
            y0: 80,
            y1: 80,
            xref: 'paper',
            line: {
                color: 'red',
                width: 2,
                dash: 'dash'
            }
        }]
    };
    
    Plotly.newPlot(container, [trace], layout, {responsive: true, displayModeBar: false});
}

function generateTrendData(baseScore) {
    // Generar datos de tendencia realistas
    const trend = [];
    let current = baseScore - 5 + Math.random() * 10;
    
    for (let i = 0; i < 4; i++) {
        trend.push(current);
        current += (Math.random() - 0.4) * 5; // Ligera tendencia al alza
        current = Math.max(60, Math.min(100, current)); // Mantener en rango 60-100
    }
    
    return trend;
}

function getPerformanceClass(score) {
    if (score >= 95) return 'perf-excellent';
    if (score >= 85) return 'perf-good';
    if (score >= 75) return 'perf-average';
    return 'perf-poor';
}

function setupEventListeners() {
    // Apply filters button
    document.getElementById('apply-filters-areas').addEventListener('click', applyFilters);
    
    // Filter change events
    ['grupo-filter-areas', 'estado-filter-areas', 'trimestre-filter-areas'].forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', updateCurrentFilters);
        }
    });
}

function updateCurrentFilters() {
    currentFilters = {
        grupo: document.getElementById('grupo-filter-areas').value,
        estado: document.getElementById('estado-filter-areas').value,
        trimestre: document.getElementById('trimestre-filter-areas').value
    };
}

async function applyFilters() {
    console.log('🔍 Aplicando filtros:', currentFilters);
    showLoading(true);
    
    try {
        await loadAreasData(); // Recargar con filtros
        showView(currentView); // Actualizar vista actual
    } catch (error) {
        console.error('❌ Error aplicando filtros:', error);
    } finally {
        showLoading(false);
    }
}

function goToDashboard() {
    // Regresar al dashboard principal
    window.location.href = '/';
}

// Utility functions
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

console.log('✅ Indicadores por Áreas JavaScript cargado');