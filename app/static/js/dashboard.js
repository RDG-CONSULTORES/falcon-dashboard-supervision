// Initialize Telegram Web App
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Chart.js default configuration
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--telegram-text');

// Global variables
let charts = {};
let currentData = {};
let refreshInterval;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeFilters();
    initializeCharts();
    loadAllData();
    setupEventListeners();
    
    // Set up auto-refresh every 5 minutes
    refreshInterval = setInterval(loadAllData, 300000);
});

// Initialize filters
async function initializeFilters() {
    try {
        // Set default dates (last 30 days)
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        document.getElementById('fecha-inicio').value = thirtyDaysAgo.toISOString().split('T')[0];
        document.getElementById('fecha-fin').value = today.toISOString().split('T')[0];
        
        // Load filter options
        const [sucursalesRes, gruposRes, areasRes] = await Promise.all([
            fetch('/api/sucursales'),
            fetch('/api/grupos'),
            fetch('/api/areas')
        ]);
        
        const sucursalesData = await sucursalesRes.json();
        const gruposData = await gruposRes.json();
        const areasData = await areasRes.json();
        
        // Populate sucursales
        const sucursalSelect = document.getElementById('sucursal-filter');
        sucursalesData.data.forEach(sucursal => {
            const option = document.createElement('option');
            option.value = sucursal;
            option.textContent = sucursal;
            sucursalSelect.appendChild(option);
        });
        
        // Populate grupos
        const grupoSelect = document.getElementById('grupo-filter');
        gruposData.data.forEach(grupo => {
            const option = document.createElement('option');
            option.value = grupo;
            option.textContent = grupo;
            grupoSelect.appendChild(option);
        });
        
        // Populate areas
        const areaSelect = document.getElementById('area-filter');
        areasData.data.forEach(area => {
            const option = document.createElement('option');
            option.value = area;
            option.textContent = area;
            areaSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error initializing filters:', error);
    }
}

// Initialize all charts
function initializeCharts() {
    // Sucursal performance chart
    const sucursalCtx = document.getElementById('sucursalChart').getContext('2d');
    charts.sucursal = new Chart(sucursalCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Promedio (%)',
                data: [],
                backgroundColor: 'rgba(0, 136, 204, 0.8)',
                borderColor: '#0088cc',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });

    // Grupo operativo chart
    const grupoCtx = document.getElementById('grupoChart').getContext('2d');
    charts.grupo = new Chart(grupoCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#0088cc',
                    '#4caf50',
                    '#ff9800',
                    '#f44336',
                    '#9c27b0',
                    '#00bcd4',
                    '#ffc107'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });

    // Area evaluation chart
    const areaCtx = document.getElementById('areaChart').getContext('2d');
    charts.area = new Chart(areaCtx, {
        type: 'horizontalBar',
        data: {
            labels: [],
            datasets: [{
                label: 'Promedio (%)',
                data: [],
                backgroundColor: 'rgba(76, 175, 80, 0.8)',
                borderColor: '#4caf50',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });

    // Trends chart
    const trendsCtx = document.getElementById('trendsChart').getContext('2d');
    charts.trends = new Chart(trendsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Promedio Diario (%)',
                data: [],
                borderColor: '#0088cc',
                backgroundColor: 'rgba(0, 136, 204, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Load all data
async function loadAllData() {
    try {
        showLoading(true);
        updateConnectionStatus('loading');
        
        const filters = getFilters();
        
        // Fetch all data in parallel
        const [summaryRes, sucursalRes, grupoRes, areaRes, trendsRes, metricsRes] = await Promise.all([
            fetch('/api/summary'),
            fetch(`/api/performance/sucursal?${new URLSearchParams(filters)}`),
            fetch(`/api/performance/grupo?${new URLSearchParams(filters)}`),
            fetch(`/api/performance/area?${new URLSearchParams(filters)}`),
            fetch(`/api/trends?${new URLSearchParams(filters)}`),
            fetch(`/api/metrics?${new URLSearchParams(filters)}`)
        ]);

        // Parse responses
        const summaryData = await summaryRes.json();
        const sucursalData = await sucursalRes.json();
        const grupoData = await grupoRes.json();
        const areaData = await areaRes.json();
        const trendsData = await trendsRes.json();
        const metricsData = await metricsRes.json();

        // Store data globally
        currentData = {
            summary: summaryData.data,
            sucursal: sucursalData.data,
            grupo: grupoData.data,
            area: areaData.data,
            trends: trendsData.data,
            metrics: metricsData.data
        };

        // Update UI
        updateSummaryCards(summaryData.data);
        updateCharts();
        updateDataTable(metricsData.data);
        updateConnectionStatus('connected');

    } catch (error) {
        console.error('Error loading data:', error);
        updateConnectionStatus('error');
        showError('Error al cargar los datos. Por favor, inténtelo nuevamente.');
    } finally {
        showLoading(false);
    }
}

// Get current filters
function getFilters() {
    return {
        sucursal: document.getElementById('sucursal-filter').value,
        grupo: document.getElementById('grupo-filter').value,
        area: document.getElementById('area-filter').value,
        fecha_inicio: document.getElementById('fecha-inicio').value,
        fecha_fin: document.getElementById('fecha-fin').value
    };
}

// Update summary cards
function updateSummaryCards(summary) {
    if (!summary) return;
    
    document.getElementById('total-sucursales').textContent = summary.total_sucursales || 0;
    document.getElementById('promedio-general').textContent = summary.promedio_general ? 
        summary.promedio_general.toFixed(1) + '%' : 'N/A';
    document.getElementById('total-evaluaciones').textContent = summary.total_evaluaciones || 0;
    
    if (summary.top_sucursales && summary.top_sucursales.length > 0) {
        const best = summary.top_sucursales[0];
        document.getElementById('mejor-sucursal').textContent = best.sucursal || 'N/A';
        document.getElementById('mejor-sucursal-score').textContent = best.promedio ? 
            best.promedio.toFixed(1) + '%' : 'N/A';
    }
}

// Update all charts
function updateCharts() {
    updateSucursalChart();
    updateGrupoChart();
    updateAreaChart();
    updateTrendsChart();
}

// Update sucursal chart
function updateSucursalChart() {
    if (!currentData.sucursal) return;
    
    const sortedData = currentData.sucursal.sort((a, b) => b.promedio - a.promedio);
    const labels = sortedData.map(item => item.sucursal_clean);
    const data = sortedData.map(item => item.promedio);
    
    charts.sucursal.data.labels = labels;
    charts.sucursal.data.datasets[0].data = data;
    charts.sucursal.update();
}

// Update grupo chart
function updateGrupoChart() {
    if (!currentData.grupo) return;
    
    const labels = currentData.grupo.map(item => item.grupo_operativo);
    const data = currentData.grupo.map(item => item.promedio);
    
    charts.grupo.data.labels = labels;
    charts.grupo.data.datasets[0].data = data;
    charts.grupo.update();
}

// Update area chart
function updateAreaChart() {
    if (!currentData.area) return;
    
    const sortedData = currentData.area.sort((a, b) => a.promedio - b.promedio);
    const labels = sortedData.map(item => item.area_evaluacion);
    const data = sortedData.map(item => item.promedio);
    
    charts.area.data.labels = labels;
    charts.area.data.datasets[0].data = data;
    charts.area.update();
}

// Update trends chart
function updateTrendsChart() {
    if (!currentData.trends) return;
    
    const labels = currentData.trends.map(item => {
        const date = new Date(item.fecha_supervision);
        return date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' });
    });
    const data = currentData.trends.map(item => item.promedio_dia);
    
    charts.trends.data.labels = labels;
    charts.trends.data.datasets[0].data = data;
    charts.trends.update();
}

// Update data table
function updateDataTable(data) {
    const tbody = document.getElementById('data-table-body');
    tbody.innerHTML = '';
    
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No hay datos disponibles</td></tr>';
        return;
    }
    
    data.slice(0, 100).forEach(item => {
        const row = document.createElement('tr');
        const date = new Date(item.fecha_supervision);
        const scoreClass = getScoreClass(item.porcentaje);
        
        row.innerHTML = `
            <td>${date.toLocaleDateString('es-ES')}</td>
            <td>${item.sucursal_clean || 'N/A'}</td>
            <td>${item.grupo_operativo || 'N/A'}</td>
            <td>${item.area_evaluacion || 'N/A'}</td>
            <td><span class="${scoreClass}">${item.porcentaje?.toFixed(1)}%</span></td>
        `;
        tbody.appendChild(row);
    });
}

// Get score class for styling
function getScoreClass(score) {
    if (score >= 90) return 'score-excellent';
    if (score >= 80) return 'score-good';
    if (score >= 70) return 'score-average';
    return 'score-poor';
}

// Update connection status
function updateConnectionStatus(status) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    statusDot.classList.remove('connected', 'error');
    
    switch (status) {
        case 'connected':
            statusDot.classList.add('connected');
            statusText.textContent = 'Conectado';
            break;
        case 'error':
            statusDot.classList.add('error');
            statusText.textContent = 'Error de conexión';
            break;
        case 'loading':
            statusText.textContent = 'Cargando...';
            break;
        default:
            statusText.textContent = 'Desconectado';
    }
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = show ? 'flex' : 'none';
}

// Show error message
function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-modal').style.display = 'block';
}

// Export data
async function exportData(format) {
    try {
        const filters = getFilters();
        filters.format = format;
        
        const response = await fetch(`/api/export?${new URLSearchParams(filters)}`);
        
        if (format === 'csv') {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `supervision_data_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `supervision_data_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            window.URL.revokeObjectURL(url);
        }
        
        tg.showAlert('Datos exportados correctamente');
    } catch (error) {
        console.error('Error exporting data:', error);
        showError('Error al exportar los datos');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Apply filters button
    document.getElementById('apply-filters').addEventListener('click', loadAllData);
    
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadAllData);
    
    // Time range selector
    document.getElementById('time-range').addEventListener('change', (e) => {
        const days = parseInt(e.target.value);
        const today = new Date();
        const startDate = new Date(today.getTime() - (days * 24 * 60 * 60 * 1000));
        
        document.getElementById('fecha-inicio').value = startDate.toISOString().split('T')[0];
        document.getElementById('fecha-fin').value = today.toISOString().split('T')[0];
        
        loadAllData();
    });
    
    // Export buttons
    document.getElementById('export-csv').addEventListener('click', () => exportData('csv'));
    document.getElementById('export-json').addEventListener('click', () => exportData('json'));
    
    // Close modal
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('error-modal').style.display = 'none';
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('error-modal');
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Handle Telegram theme changes
    tg.onEvent('themeChanged', updateThemeColors);
}

// Update theme colors
function updateThemeColors() {
    const root = document.documentElement;
    const tgTheme = tg.themeParams;
    
    Object.entries(tgTheme).forEach(([key, value]) => {
        if (value) {
            root.style.setProperty(`--tg-theme-${key.replace(/_/g, '-')}`, value);
        }
    });
    
    // Update Chart.js colors
    Chart.defaults.color = getComputedStyle(root).getPropertyValue('--telegram-text');
    Object.values(charts).forEach(chart => chart.update());
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});