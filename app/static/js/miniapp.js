// Initialize Telegram Web App
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Configure Chart.js for mobile
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--telegram-text');
Chart.defaults.font.size = 11;
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

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
        
        // Load filter options from coordinates data
        try {
            const coordsRes = await fetch('/api/coordinates?year=2025&limit=100');
            const coordsData = await coordsRes.json();
            
            if (coordsData && coordsData.length > 0) {
                // Extract unique values
                const sucursales = [...new Set(coordsData.map(item => item.sucursal_clean))].sort();
                const estados = [...new Set(coordsData.map(item => item.estado))].sort();
                const municipios = [...new Set(coordsData.map(item => item.municipio))].sort();
                
                // Populate sucursales
                const sucursalSelect = document.getElementById('sucursal-filter');
                sucursales.forEach(sucursal => {
                    const option = document.createElement('option');
                    option.value = sucursal;
                    option.textContent = sucursal;
                    sucursalSelect.appendChild(option);
                });
                
                // Populate estados (as grupos)
                const grupoSelect = document.getElementById('grupo-filter');
                estados.forEach(estado => {
                    const option = document.createElement('option');
                    option.value = estado;
                    option.textContent = estado;
                    grupoSelect.appendChild(option);
                });
                
                // Populate municipios (as areas)
                const areaSelect = document.getElementById('area-filter');
                municipios.forEach(municipio => {
                    const option = document.createElement('option');
                    option.value = municipio;
                    option.textContent = municipio;
                    areaSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading filter options:', error);
        }
        
    } catch (error) {
        console.error('Error initializing filters:', error);
    }
}

// Initialize all charts - optimized for mobile
function initializeCharts() {
    // Common mobile chart options
    const mobileOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    font: { size: 10 },
                    padding: 8,
                    usePointStyle: true,
                    pointStyle: 'circle'
                }
            },
            tooltip: {
                titleFont: { size: 11 },
                bodyFont: { size: 10 },
                padding: 8
            }
        },
        scales: {
            x: {
                ticks: {
                    font: { size: 9 },
                    maxRotation: 45,
                    minRotation: 0
                },
                grid: { display: false }
            },
            y: {
                ticks: {
                    font: { size: 9 }
                },
                grid: { color: 'rgba(0,0,0,0.1)' }
            }
        }
    };

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
            ...mobileOptions,
            plugins: {
                ...mobileOptions.plugins,
                legend: { display: false }
            },
            scales: {
                ...mobileOptions.scales,
                y: {
                    ...mobileOptions.scales.y,
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        ...mobileOptions.scales.y.ticks,
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
            ...mobileOptions,
            plugins: {
                ...mobileOptions.plugins,
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { size: 9 },
                        padding: 6,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    ...mobileOptions.plugins.tooltip,
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
        type: 'bar',
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
            ...mobileOptions,
            indexAxis: 'y',
            plugins: {
                ...mobileOptions.plugins,
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        font: { size: 9 },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                y: {
                    ticks: {
                        font: { size: 9 }
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
                fill: true,
                pointRadius: 2,
                pointHoverRadius: 4
            }]
        },
        options: {
            ...mobileOptions,
            plugins: {
                ...mobileOptions.plugins,
                legend: { display: false }
            },
            scales: {
                ...mobileOptions.scales,
                x: {
                    ...mobileOptions.scales.x,
                    ticks: {
                        font: { size: 8 },
                        maxRotation: 45,
                        maxTicksLimit: 6
                    }
                },
                y: {
                    ...mobileOptions.scales.y,
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        ...mobileOptions.scales.y.ticks,
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
        
        // Add year parameter to filters
        const apiFilters = { ...filters, year: 2025, quarter: 'Q1' };
        
        // Fetch all data in parallel using working legacy endpoints
        const [kpisRes, coordsRes] = await Promise.all([
            fetch(`/api/kpis?${new URLSearchParams(apiFilters)}`),
            fetch(`/api/coordinates?${new URLSearchParams({ ...apiFilters, limit: 50 })}`)
        ]);

        // Parse responses
        const kpisData = await kpisRes.json();
        const coordsData = await coordsRes.json();

        // Store data globally
        currentData = {
            summary: kpisData || {},
            sucursal: coordsData || [],
            grupo: [],
            area: [],
            trends: [],
            metrics: coordsData || []
        };

        // Update UI
        updateSummaryCards(kpisData);
        updateCharts();
        updateDataTable(coordsData?.slice(0, 50));
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
    
    document.getElementById('total-sucursales').textContent = summary.sucursales || 0;
    document.getElementById('promedio-general').textContent = summary.promedio ? 
        parseFloat(summary.promedio).toFixed(1) + '%' : 'N/A';
    document.getElementById('total-evaluaciones').textContent = summary.supervisiones ? 
        parseInt(summary.supervisiones).toLocaleString() : 0;
    
    // Get best performing branch from coordinates data
    const coordsData = currentData.metrics || [];
    if (coordsData.length > 0) {
        const sortedBranches = coordsData.sort((a, b) => parseFloat(b.promedio_porcentaje) - parseFloat(a.promedio_porcentaje));
        const best = sortedBranches[0];
        document.getElementById('mejor-sucursal').textContent = best.sucursal_clean || 'N/A';
        document.getElementById('mejor-sucursal-score').textContent = best.promedio_porcentaje ? 
            parseFloat(best.promedio_porcentaje).toFixed(1) + '%' : 'N/A';
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
    if (!currentData.sucursal || currentData.sucursal.length === 0) return;
    
    const sortedData = currentData.sucursal.sort((a, b) => parseFloat(b.promedio_porcentaje) - parseFloat(a.promedio_porcentaje));
    // Show only top 10 for mobile
    const topData = sortedData.slice(0, 10);
    const labels = topData.map(item => item.sucursal_clean);
    const data = topData.map(item => parseFloat(item.promedio_porcentaje));
    
    charts.sucursal.data.labels = labels;
    charts.sucursal.data.datasets[0].data = data;
    charts.sucursal.update();
}

// Update grupo chart
function updateGrupoChart() {
    // Group data by estado from coordinates
    if (!currentData.sucursal || currentData.sucursal.length === 0) return;
    
    const stateGroups = {};
    currentData.sucursal.forEach(item => {
        const state = item.estado;
        if (!stateGroups[state]) {
            stateGroups[state] = [];
        }
        stateGroups[state].push(parseFloat(item.promedio_porcentaje));
    });
    
    const labels = Object.keys(stateGroups);
    const data = labels.map(state => {
        const scores = stateGroups[state];
        return scores.reduce((sum, score) => sum + score, 0) / scores.length;
    });
    
    charts.grupo.data.labels = labels;
    charts.grupo.data.datasets[0].data = data;
    charts.grupo.update();
}

// Update area chart
function updateAreaChart() {
    // Group data by municipio from coordinates
    if (!currentData.sucursal || currentData.sucursal.length === 0) return;
    
    const municipioGroups = {};
    currentData.sucursal.forEach(item => {
        const municipio = item.municipio;
        if (!municipioGroups[municipio]) {
            municipioGroups[municipio] = [];
        }
        municipioGroups[municipio].push(parseFloat(item.promedio_porcentaje));
    });
    
    const labels = Object.keys(municipioGroups).slice(0, 10); // Top 10 municipios
    const data = labels.map(municipio => {
        const scores = municipioGroups[municipio];
        return scores.reduce((sum, score) => sum + score, 0) / scores.length;
    });
    
    charts.area.data.labels = labels;
    charts.area.data.datasets[0].data = data;
    charts.area.update();
}

// Update trends chart
function updateTrendsChart() {
    // Create a simple trend showing performance distribution
    if (!currentData.sucursal || currentData.sucursal.length === 0) return;
    
    const performanceRanges = {
        'Excelente (90-100%)': 0,
        'Bueno (80-89%)': 0,
        'Regular (70-79%)': 0,
        'Bajo (<70%)': 0
    };
    
    currentData.sucursal.forEach(item => {
        const score = parseFloat(item.promedio_porcentaje);
        if (score >= 90) performanceRanges['Excelente (90-100%)']++;
        else if (score >= 80) performanceRanges['Bueno (80-89%)']++;
        else if (score >= 70) performanceRanges['Regular (70-79%)']++;
        else performanceRanges['Bajo (<70%)']++;
    });
    
    const labels = Object.keys(performanceRanges);
    const data = Object.values(performanceRanges);
    
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
    
    data.slice(0, 50).forEach(item => {
        const row = document.createElement('tr');
        const scoreClass = getScoreClass(parseFloat(item.promedio_porcentaje));
        
        row.innerHTML = `
            <td>2025</td>
            <td>${item.sucursal_clean || 'N/A'}</td>
            <td>${item.estado || 'N/A'}</td>
            <td>${item.municipio || 'N/A'}</td>
            <td><span class="${scoreClass}">${parseFloat(item.promedio_porcentaje).toFixed(1)}%</span></td>
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
            statusText.textContent = 'Error';
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