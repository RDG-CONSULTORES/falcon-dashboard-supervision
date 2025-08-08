// Dashboard Metabase - Telegram Mini App JavaScript
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Global variables
let currentQuarter = 'ALL';
let currentYear = 2025;
let currentFilters = {
    quarter: 'ALL',
    year: '2025',
    estado: '',
    grupo: ''
};

// Función para mostrar debug en pantalla
function addDebugMessage(message) {
    const debugContent = document.getElementById('debug-content');
    if (debugContent) {
        const timestamp = new Date().toLocaleTimeString();
        debugContent.innerHTML += `<br>[${timestamp}] ${message}`;
        debugContent.scrollTop = debugContent.scrollHeight;
    }
    console.log(message); // También en consola por si acaso
}

// Función helper para fetch con headers correctos para Telegram
function telegramFetch(url, timeoutMs = 10000) {
    const fetchOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
        }
    };
    
    addDebugMessage(`📡 Fetch a: ${url} (timeout: ${timeoutMs}ms)`);
    
    // Promise que se resuelve con timeout
    const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
            reject(new Error(`Request timeout después de ${timeoutMs}ms`));
        }, timeoutMs);
    });
    
    // Race entre fetch y timeout
    return Promise.race([
        fetch(url, fetchOptions),
        timeoutPromise
    ]);
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Verificar que Chart.js está disponible
    const chartAvailable = typeof Chart !== 'undefined';
    addDebugMessage(`📊 Chart.js disponible: ${chartAvailable}`);
    
    if (chartAvailable) {
        addDebugMessage(`📊 Chart.js version: ${Chart.version}`);
    } else {
        addDebugMessage('❌ Chart.js NO se cargó correctamente');
    }
    
    // Test básico de conectividad
    addDebugMessage(`🌐 Location: ${window.location.href}`);
    addDebugMessage(`📱 Telegram WebApp: ${typeof window.Telegram !== 'undefined'}`);
    
    // Determinar URL correcta para API calls
    const baseUrl = 'https://5b00ea7515d5.ngrok-free.app';
    addDebugMessage(`🔗 Base URL configurada: ${baseUrl}`);
    
    // Test simple de fetch
    addDebugMessage(`🧪 Probando conexión a: ${baseUrl}/api/health`);
    
    telegramFetch(`${baseUrl}/api/health`)
        .then(res => {
            addDebugMessage(`🏥 Health check status: ${res.status} ${res.statusText}`);
            addDebugMessage(`🏥 Response headers: ${JSON.stringify([...res.headers.entries()])}`);
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            return res.json();
        })
        .then(data => {
            addDebugMessage(`✅ API respondió: ${data.status} - DB: ${data.database}`);
            addDebugMessage(`✅ Data completa: ${JSON.stringify(data)}`);
        })
        .catch(err => {
            addDebugMessage(`❌ Error health check: ${err.name} - ${err.message}`);
            addDebugMessage(`🔍 Tipo de error: ${typeof err}`);
            addDebugMessage(`🔍 Stack trace: ${err.stack}`);
        });
    
    initializeDashboard();
});

async function initializeDashboard() {
    try {
        showLoading(true);
        updateConnectionStatus('loading');
        addDebugMessage('🚀 Iniciando dashboard...');
        
        // Initialize filters
        addDebugMessage('📋 Inicializando filtros...');
        await initializeFilters();
        addDebugMessage('✅ Filtros inicializados');
        
        // Esperar a que se cargue el GeoJSON
        addDebugMessage('🗺️ Cargando mapa de México...');
        await loadMexicoGeoJSON();
        addDebugMessage('✅ Mapa cargado');
        
        // Load initial data
        addDebugMessage('📊 Cargando datos iniciales...');
        await loadAllData();
        addDebugMessage('✅ Datos cargados');
        
        // Setup event listeners
        setupEventListeners();
        addDebugMessage('✅ Event listeners configurados');
        
        updateConnectionStatus('connected');
        addDebugMessage('✅ Dashboard conectado exitosamente');
        
    } catch (error) {
        addDebugMessage(`❌ Error inicializando: ${error.message}`);
        console.error('Error inicializando dashboard:', error);
        updateConnectionStatus('error');
        showError('Error al cargar el dashboard. Por favor, intente nuevamente.');
    } finally {
        showLoading(false);
    }
}

async function initializeFilters() {
    try {
        // Determinar la URL base
        const baseUrl = 'https://5b00ea7515d5.ngrok-free.app';
        addDebugMessage(`🔗 Usando base URL para filtros: ${baseUrl}`);
        
        // Load metadata
        
        const [estadosRes, gruposRes] = await Promise.all([
            telegramFetch(`${baseUrl}/api/metadata/estados`).catch(err => {
                addDebugMessage(`❌ Error fetching estados: ${err.name} - ${err.message}`);
                throw err;
            }),
            telegramFetch(`${baseUrl}/api/metadata/grupos`).catch(err => {
                addDebugMessage(`❌ Error fetching grupos: ${err.name} - ${err.message}`);
                throw err;
            })
        ]);
        
        addDebugMessage(`📡 Respuesta filtros: Estados=${estadosRes.status}, Grupos=${gruposRes.status}`);
        
        const estadosData = await estadosRes.json();
        const gruposData = await gruposRes.json();
        
        // Populate estados filter
        const estadoSelect = document.getElementById('estado-filter');
        estadosData.data.forEach(estado => {
            const option = document.createElement('option');
            option.value = estado;
            option.textContent = estado;
            estadoSelect.appendChild(option);
        });
        
        // Populate grupos filter
        const grupoSelect = document.getElementById('grupo-filter');
        gruposData.data.forEach(grupo => {
            const option = document.createElement('option');
            option.value = grupo;
            option.textContent = grupo;
            grupoSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error cargando filtros:', error);
    }
}

async function loadAllData() {
    try {
        showLoading(true);
        addDebugMessage('🔄 Iniciando carga de datos...');
        
        const params = new URLSearchParams(currentFilters);
        addDebugMessage(`🔗 Parámetros: ${params.toString()}`);
        
        // Determinar la URL base
        const baseUrl = 'https://5b00ea7515d5.ngrok-free.app';
        addDebugMessage(`🌍 Base URL: ${baseUrl}`);
        
        // Fetch all data in parallel
        addDebugMessage('📡 Haciendo llamadas a API...');
        
        const [kpisRes, estadosRes, sucursalesRes, gruposRes, rankingRes] = await Promise.all([
            telegramFetch(`${baseUrl}/api/kpis?${params}`).catch(err => {
                addDebugMessage(`❌ Error KPIs: ${err.name} - ${err.message}`);
                throw err;
            }),
            telegramFetch(`${baseUrl}/api/estados?${params}`).catch(err => {
                addDebugMessage(`❌ Error Estados: ${err.name} - ${err.message}`);
                throw err;
            }),
            telegramFetch(`${baseUrl}/api/sucursales/coordinates?${params}`).catch(err => {
                addDebugMessage(`❌ Error Sucursales: ${err.name} - ${err.message}`);
                throw err;
            }),
            telegramFetch(`${baseUrl}/api/grupos?${params}`).catch(err => {
                addDebugMessage(`❌ Error Grupos: ${err.name} - ${err.message}`);
                throw err;
            }),
            telegramFetch(`${baseUrl}/api/sucursales/ranking?${params}`).catch(err => {
                addDebugMessage(`❌ Error Ranking: ${err.name} - ${err.message}`);
                throw err;
            })
        ]);
        
        addDebugMessage(`📊 Respuestas: KPIs=${kpisRes.status}, Estados=${estadosRes.status}, Sucursales=${sucursalesRes.status}`);
        
        // Check if all responses are OK
        if (!kpisRes.ok || !estadosRes.ok || !sucursalesRes.ok || !gruposRes.ok || !rankingRes.ok) {
            throw new Error(`HTTP Error: ${kpisRes.status || estadosRes.status || sucursalesRes.status || gruposRes.status || rankingRes.status}`);
        }
        
        const [kpisData, estadosData, sucursalesData, gruposData, rankingData] = await Promise.all([
            kpisRes.json(),
            estadosRes.json(),
            sucursalesRes.json(),
            gruposRes.json(),
            rankingRes.json()
        ]);
        
        console.log('Datos cargados:', { kpisData, estadosData, sucursalesData, gruposData, rankingData });
        
        // Update UI components with error handling
        try {
            updateKPIs(kpisData.data);
        } catch (e) {
            console.error('Error updating KPIs:', e);
        }
        
        try {
            updateMexicoChoropleth(estadosData.data);
        } catch (e) {
            console.error('Error updating Mexico map:', e);
        }
        
        try {
            updatePinMap(sucursalesData.data);
        } catch (e) {
            console.error('Error updating pin map:', e);
        }
        
        try {
            updateEstadosChart(estadosData.data);
        } catch (e) {
            console.error('Error updating estados chart:', e);
        }
        
        try {
            updateGruposChart(gruposData.data);
        } catch (e) {
            console.error('Error updating grupos chart:', e);
        }
        
        try {
            updateSucursalesRanking(rankingData.data);
        } catch (e) {
            console.error('Error updating ranking chart:', e);
        }
        
        try {
            updateMetricsExtra(estadosData.data);
        } catch (e) {
            console.error('Error updating extra metrics:', e);
        }
        
    } catch (error) {
        console.error('Error cargando datos:', error);
        showError('Error al cargar los datos. Por favor, intente nuevamente.');
    } finally {
        showLoading(false);
    }
}

function updateKPIs(kpis) {
    // Promedio General
    document.getElementById('promedio-general').textContent = `${kpis.promedio_general || 0}%`;
    document.getElementById('periodo-actual').textContent = kpis.periodo || 'Q3 2025';
    
    const cambioPromedio = document.getElementById('cambio-promedio');
    const cambioIndicator = cambioPromedio.querySelector('.change-indicator');
    const cambioValue = kpis.cambio_promedio || 0;
    
    cambioIndicator.textContent = `${cambioValue >= 0 ? '+' : ''}${cambioValue}%`;
    cambioIndicator.className = `change-indicator ${cambioValue >= 0 ? 'positive' : 'negative'}`;
    
    // Supervisiones
    document.getElementById('num-supervisiones').textContent = (kpis.num_supervisiones || 0).toLocaleString();
    
    const cambioSupervisiones = document.getElementById('cambio-supervisiones');
    const cambioSupIndicator = cambioSupervisiones.querySelector('.change-indicator');
    const cambioSupValue = kpis.cambio_supervisiones || 0;
    
    cambioSupIndicator.textContent = `${cambioSupValue >= 0 ? '+' : ''}${cambioSupValue}%`;
    cambioSupIndicator.className = `change-indicator ${cambioSupValue >= 0 ? 'positive' : 'negative'}`;
    
    // Meta
    document.getElementById('meta-valor').textContent = `${kpis.meta || 84.54}%`;
    
    const metaStatus = document.getElementById('meta-status');
    const statusIndicator = metaStatus.querySelector('.status-indicator');
    const statusText = metaStatus.querySelector('.status-text');
    
    if (kpis.cumple_meta) {
        statusIndicator.textContent = '✅';
        statusIndicator.className = 'status-indicator success';
        statusText.textContent = 'Meta cumplida';
    } else {
        statusIndicator.textContent = '⚠️';
        statusIndicator.className = 'status-indicator warning';
        statusText.textContent = 'Por debajo de meta';
    }
    
    // Cobertura
    document.getElementById('num-sucursales').textContent = kpis.num_sucursales || 0;
    document.getElementById('num-estados').textContent = `${kpis.num_estados || 0} estados`;
}

// Cargar GeoJSON de México
let mexicoGeoJSON = null;

async function loadMexicoGeoJSON() {
    try {
        addDebugMessage('🗺️ Descargando GeoJSON de México...');
        const response = await fetch('https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Modificar el GeoJSON para que use el nombre del estado como ID
        mexicoGeoJSON = {
            type: "FeatureCollection",
            features: data.features.map(feature => ({
                ...feature,
                id: feature.properties.name, // Usar el nombre como ID
                properties: {
                    ...feature.properties,
                    estado: feature.properties.name // Asegurar que tengamos 'estado'
                }
            }))
        };
        
        addDebugMessage('✅ GeoJSON cargado exitosamente');
        console.log('Estados encontrados:', mexicoGeoJSON.features.map(f => f.properties.name));
    } catch (error) {
        addDebugMessage(`⚠️ Error cargando GeoJSON: ${error.message} - Continuando sin mapa`);
        console.error('Error cargando GeoJSON:', error);
    }
}

// Cargar GeoJSON al iniciar
loadMexicoGeoJSON();

function updateMexicoChoropleth(estadosData) {
    // Si no tenemos GeoJSON, usar mapa simple
    if (!mexicoGeoJSON) {
        console.warn('GeoJSON no disponible, usando mapa simple');
        updateSimpleMap(estadosData);
        return;
    }
    
    // Mapeo de nombres para coincidir con el GeoJSON
    const nombreMapping = {
        'Coahuila': 'Coahuila',
        'Coahuila de Zaragoza': 'Coahuila',
        'Nuevo León': 'Nuevo León',
        'Tamaulipas': 'Tamaulipas',
        'Durango': 'Durango',
        'Sinaloa': 'Sinaloa',
        'Michoacán': 'Michoacán',
        'Michoacán de Ocampo': 'Michoacán',
        'Querétaro': 'Querétaro'
    };
    
    // Crear un mapa de valores normalizados
    const valoresNormalizados = {};
    const datosNormalizados = estadosData.map(estado => {
        const nombreNormalizado = nombreMapping[estado.estado] || estado.estado;
        valoresNormalizados[nombreNormalizado] = estado.promedio;
        return {
            ...estado,
            estadoNormalizado: nombreNormalizado
        };
    });
    
    // Obtener todos los estados del GeoJSON
    const estadosGeoJSON = mexicoGeoJSON.features.map(f => f.properties.name);
    
    // Crear arrays de locations y z values que coincidan
    const locations = [];
    const zValues = [];
    const customData = [];
    
    // Incluir TODOS los estados del GeoJSON, tengan o no datos
    estadosGeoJSON.forEach(estadoGeo => {
        const estadoData = datosNormalizados.find(e => e.estadoNormalizado === estadoGeo);
        
        locations.push(estadoGeo);
        
        if (estadoData) {
            // Si tenemos datos, usar los valores reales
            zValues.push(estadoData.promedio);
            customData.push({
                sucursales: estadoData.total_sucursales,
                supervisiones: estadoData.total_supervisiones,
                hasData: true
            });
        } else {
            // Si no hay datos, usar valores predeterminados
            zValues.push(0); // 0 se mostrará en gris
            customData.push({
                sucursales: 0,
                supervisiones: 0,
                hasData: false
            });
        }
    });
    
    console.log('Estados coincidentes:', locations);
    console.log('Valores:', zValues);
    
    const data = [{
        type: 'choropleth',
        locationmode: 'geojson-id',
        geojson: mexicoGeoJSON,
        locations: locations,
        z: zValues,
        customdata: customData,
        colorscale: [
            [0, '#e0e0e0'],     // Gris para sin datos (valor 0)
            [0.01, '#f5f5f5'],  // Gris muy claro para valores muy bajos
            [0.7, '#90caf9'],   // Azul muy claro
            [0.75, '#64b5f6'],  // Azul claro
            [0.8, '#42a5f5'],   // Azul medio claro
            [0.85, '#1e88e5'],  // Azul medio
            [0.9, '#1976d2'],   // Azul medio oscuro
            [0.95, '#1565c0'],  // Azul oscuro
            [1, '#0d47a1']      // Azul muy oscuro
        ],
        zmin: 0,
        zmax: 100,
        hoverinfo: 'text',
        hovertext: locations.map((loc, i) => 
            customData[i].hasData 
                ? `<b>${loc}</b><br>Performance: ${zValues[i].toFixed(1)}%<br>Sucursales: ${customData[i].sucursales}<br>Supervisiones: ${customData[i].supervisiones}`
                : `<b>${loc}</b><br>Sin datos disponibles`
        ),
        showscale: false,
        marker: {
            line: {
                color: '#666666',
                width: 0.5
            }
        }
    }];
    
    const layout = {
        title: {
            text: 'Mapa de México - Performance por Estado',
            font: { size: 14, color: '#333' },
            x: 0.5
        },
        geo: {
            fitbounds: 'locations',
            visible: false,
            bgcolor: '#f8f9fa',
            projection: {
                type: 'mercator'
            },
            center: {
                lat: 23.5,
                lon: -102
            },
            lonaxis: {
                range: [-118, -86]
            },
            lataxis: {
                range: [14, 33]
            }
        },
        margin: { l: 0, r: 0, t: 40, b: 0 },
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#f8f9fa',
        font: { size: 12 },
        width: null,
        height: 400
    };
    
    const config = {
        displayModeBar: false,
        responsive: true
    };
    
    Plotly.newPlot('mexico-choropleth', data, layout, config);
}

function updateSimpleMap(estadosData) {
    // Mapa simple cuando no hay GeoJSON
    const data = [{
        type: 'scatter',
        mode: 'markers+text',
        x: estadosData.map((_, i) => i % 3),
        y: estadosData.map((_, i) => Math.floor(i / 3)),
        text: estadosData.map(e => `${e.estado}<br>${e.promedio.toFixed(1)}%`),
        marker: {
            size: 50,
            color: estadosData.map(e => {
                if (e.promedio >= 95) return '#0d47a1';
                if (e.promedio >= 90) return '#1565c0';
                if (e.promedio >= 85) return '#1976d2';
                if (e.promedio >= 80) return '#1e88e5';
                if (e.promedio >= 75) return '#42a5f5';
                if (e.promedio >= 70) return '#64b5f6';
                return '#90caf9';
            }),
            line: {
                color: '#ffffff',
                width: 2
            }
        },
        textposition: 'center',
        textfont: {
            size: 11,
            color: '#ffffff',
            family: 'Arial'
        },
        hoverinfo: 'text',
        hovertext: estadosData.map(e => 
            `<b>${e.estado}</b><br>` +
            `Performance: ${e.promedio.toFixed(1)}%<br>` +
            `Sucursales: ${e.total_sucursales}<br>` +
            `Supervisiones: ${e.total_supervisiones}`
        )
    }];
    
    const layout = {
        title: {
            text: 'Estados de México - Vista Simplificada',
            font: { size: 14, color: '#333' },
            x: 0.5
        },
        xaxis: { visible: false },
        yaxis: { visible: false },
        margin: { l: 10, r: 10, t: 50, b: 10 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    const config = {
        displayModeBar: false,
        responsive: true
    };
    
    Plotly.newPlot('mexico-choropleth', data, layout, config);
}

// Función removida - ya no necesitamos la lista de estados

function updatePinMap(sucursalesData) {
    // Crear scatter plot con coordenadas mejoradas
    const lats = sucursalesData.map(s => s.latitud);
    const lons = sucursalesData.map(s => s.longitud);
    const texts = sucursalesData.map(s => 
        `<b>${s.sucursal}</b><br>Estado: ${s.estado}<br>Grupo: ${s.grupo_operativo}<br>Performance: ${s.promedio}%<br>Supervisiones: ${s.total_supervisiones}`
    );
    
    // Colores mejorados con gradientes
    const colors = sucursalesData.map(s => {
        if (s.promedio >= 95) return '#0d47a1';      // Azul muy oscuro
        if (s.promedio >= 90) return '#1565c0';      // Azul oscuro
        if (s.promedio >= 85) return '#1976d2';      // Azul medio
        if (s.promedio >= 80) return '#1e88e5';      // Azul claro
        if (s.promedio >= 75) return '#42a5f5';      // Azul muy claro
        if (s.promedio >= 70) return '#64b5f6';      // Azul pastel
        return '#90caf9';                            // Azul muy pastel
    });
    
    // Tamaños variables basados en número de supervisiones
    const sizes = sucursalesData.map(s => {
        const supervisiones = s.total_supervisiones || 1;
        return Math.max(8, Math.min(20, 8 + (supervisiones * 2))); // Entre 8 y 20 píxeles
    });
    
    const data = [{
        // Sombra inferior para efecto gota
        type: 'scattermapbox',
        lat: lats.map(lat => lat - 0.008), // Offset menor para sombra
        lon: lons.map(lon => lon + 0.005),
        mode: 'markers',
        marker: {
            size: sizes.map(s => s * 0.8),
            color: 'rgba(0,0,0,0.35)',
            opacity: 0.6,
            symbol: 'circle'
        },
        hoverinfo: 'skip',
        showlegend: false
    }, {
        // Punto principal tipo gota
        type: 'scattermapbox',
        lat: lats,
        lon: lons,
        mode: 'markers',
        marker: {
            size: sizes,
            color: colors,
            opacity: 0.85,
            symbol: 'circle',
            line: {
                color: '#ffffff',
                width: 2
            }
        },
        text: texts,
        hoverinfo: 'text',
        hovertemplate: '%{text}<extra></extra>'
    }, {
        // Punto central brillante
        type: 'scattermapbox',
        lat: lats,
        lon: lons,
        mode: 'markers',
        marker: {
            size: sizes.map(s => s * 0.5),
            color: colors.map(c => c),
            opacity: 1.0,
            symbol: 'circle',
            line: {
                color: '#ffffff',
                width: 1
            }
        },
        hoverinfo: 'skip',
        showlegend: false
    }];
    
    const layout = {
        title: {
            text: 'Ubicación de Sucursales',
            font: { size: 14, color: '#333' }
        },
        mapbox: {
            style: 'open-street-map',
            center: { lat: 25.8, lon: -100.5 },
            zoom: 5
        },
        margin: { l: 0, r: 0, t: 40, b: 0 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { size: 12 }
    };
    
    const config = {
        displayModeBar: false,
        responsive: true
    };
    
    Plotly.newPlot('pin-map', data, layout, config);
}

// Variables para almacenar instancias de Chart.js
let estadosChart = null;
let gruposChart = null;
let sucursalesChart = null;

function updateEstadosChart(estadosData) {
    addDebugMessage(`🎯 updateEstadosChart llamada con ${estadosData?.length || 0} estados`);
    
    // Verificar que tenemos datos
    if (!estadosData || estadosData.length === 0) {
        addDebugMessage('⚠️ No hay datos de estados para mostrar');
        return;
    }
    
    // Verificar que el elemento canvas existe
    const canvas = document.getElementById('estados-chart');
    if (!canvas) {
        addDebugMessage('❌ Canvas estados-chart no encontrado');
        return;
    }
    
    addDebugMessage(`✅ Canvas encontrado: ${canvas.offsetWidth}x${canvas.offsetHeight}px`);
    
    // Ordenar por performance
    const sortedData = [...estadosData].sort((a, b) => b.promedio - a.promedio);
    console.log('Datos ordenados:', sortedData);
    
    // Destruir chart anterior si existe
    if (estadosChart) {
        estadosChart.destroy();
    }
    
    const ctx = canvas.getContext('2d');
    
    // Generar colores sin gradientes para evitar errores
    const backgroundColors = sortedData.map(e => {
        if (e.promedio >= 95) return '#0d47a1';      // Azul oscuro
        if (e.promedio >= 90) return '#1565c0';      // Azul medio oscuro
        if (e.promedio >= 85) return '#1976d2';      // Azul medio
        if (e.promedio >= 80) return '#1e88e5';      // Azul claro
        if (e.promedio >= 75) return '#42a5f5';      // Azul muy claro
        if (e.promedio >= 70) return '#64b5f6';      // Azul pastel
        return '#90caf9';                            // Azul muy pastel
    });
    
    try {
        estadosChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedData.map(e => e.estado),
                datasets: [{
                    label: 'Performance (%)',
                    data: sortedData.map(e => e.promedio),
                    backgroundColor: backgroundColors,
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(255,255,255,0.95)',
                    titleColor: '#333',
                    bodyColor: '#666',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            const dataIndex = context.dataIndex;
                            const estado = sortedData[dataIndex];
                            return [
                                `Performance: ${estado.promedio.toFixed(1)}%`,
                                `Sucursales: ${estado.total_sucursales}`,
                                `Supervisiones: ${estado.total_supervisiones}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: Math.max(...sortedData.map(e => e.promedio)) + 5,
                    grid: {
                        color: '#f0f0f0',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#666',
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#333',
                        font: {
                            size: 11,
                            weight: '500'
                        }
                    }
                }
            },
            animation: {
                duration: 1200,
                easing: 'easeOutQuart'
            },
            elements: {
                bar: {
                    borderRadius: 8
                }
            }
        });
        
        addDebugMessage('✅ Estados chart creado exitosamente');
        
    } catch (error) {
        addDebugMessage(`❌ Error creando chart de estados: ${error.message}`);
        
        // Fallback: mostrar una lista simple
        canvas.style.display = 'none';
        const fallbackDiv = document.createElement('div');
        fallbackDiv.innerHTML = `
            <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
                <h4>Estados (Chart.js no disponible)</h4>
                ${sortedData.slice(0, 5).map(e => 
                    `<div style="margin: 5px 0; padding: 10px; background: white; border-radius: 4px;">
                        ${e.estado}: ${e.promedio.toFixed(1)}%
                    </div>`
                ).join('')}
            </div>
        `;
        canvas.parentNode.appendChild(fallbackDiv);
        addDebugMessage('📋 Fallback mostrado para estados');
    }
}

function updateGruposChart(gruposData) {
    // Ordenar por performance y tomar top 12 para mejor visualización
    const sortedData = [...gruposData].sort((a, b) => b.promedio - a.promedio).slice(0, 12);
    
    // Destruir chart anterior si existe
    if (gruposChart) {
        gruposChart.destroy();
    }
    
    const ctx = document.getElementById('grupos-chart').getContext('2d');
    
    // Truncar nombres largos para mejor visualización
    const truncateText = (text, maxLength = 18) => {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    };
    
    // Generar colores simples para evitar errores
    const backgroundColors = sortedData.map(g => {
        if (g.promedio >= 95) return '#0d47a1';      // Azul intenso
        if (g.promedio >= 90) return '#1565c0';      // Azul vibrante
        if (g.promedio >= 85) return '#1976d2';      // Azul medio
        if (g.promedio >= 80) return '#1e88e5';      // Azul claro
        if (g.promedio >= 75) return '#42a5f5';      // Azul suave
        if (g.promedio >= 70) return '#64b5f6';      // Azul pastel
        return '#90caf9';                            // Azul muy suave
    });
    
    gruposChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedData.map(g => truncateText(g.grupo_operativo)),
            datasets: [{
                label: 'Performance (%)',
                data: sortedData.map(g => g.promedio),
                backgroundColor: backgroundColors,
                borderColor: '#ffffff',
                borderWidth: 2,
                borderRadius: 10,
                borderSkipped: false,
                hoverBackgroundColor: backgroundColors.map(color => color),
                hoverBorderColor: '#333',
                hoverBorderWidth: 3
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(255,255,255,0.98)',
                    titleColor: '#333',
                    bodyColor: '#666',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    cornerRadius: 12,
                    displayColors: false,
                    padding: 12,
                    titleFont: {
                        size: 13,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 12
                    },
                    callbacks: {
                        title: function(context) {
                            const dataIndex = context[0].dataIndex;
                            return sortedData[dataIndex].grupo_operativo; // Nombre completo
                        },
                        label: function(context) {
                            const dataIndex = context.dataIndex;
                            const grupo = sortedData[dataIndex];
                            return [
                                `Performance: ${grupo.promedio.toFixed(1)}%`,
                                `Sucursales: ${grupo.total_sucursales}`,
                                `Supervisiones: ${grupo.total_supervisiones}`,
                                `Estados: ${grupo.estados_presentes}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: Math.max(...sortedData.map(g => g.promedio)) + 5,
                    grid: {
                        color: '#f5f5f5',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#666',
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#333',
                        font: {
                            size: 10,
                            weight: '500'
                        }
                    }
                }
            },
            animation: {
                duration: 1400,
                easing: 'easeOutCubic',
                delay: (context) => {
                    return context.dataIndex * 100; // Animación escalonada
                }
            },
            elements: {
                bar: {
                    borderRadius: 10
                }
            }
        }
    });
}

function updateSucursalesRanking(rankingData) {
    // Tomar top 20 por defecto para mejor visualización
    const topData = rankingData.slice(0, 20);
    
    // Destruir chart anterior si existe
    if (sucursalesChart) {
        sucursalesChart.destroy();
    }
    
    const ctx = document.getElementById('sucursales-ranking').getContext('2d');
    
    // Truncar nombres largos de sucursales
    const truncateText = (text, maxLength = 12) => {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    };
    
    // Generar colores simples más dinámicos
    const backgroundColors = topData.map((s, index) => {
        // Colores especiales para top 3
        if (index === 0) return '#ff6b35'; // Oro
        if (index === 1) return '#c0c0c0'; // Plata
        if (index === 2) return '#cd7f32'; // Bronce
        
        // Colores por performance para el resto
        if (s.promedio >= 98) return '#0d47a1';
        if (s.promedio >= 95) return '#1565c0';
        if (s.promedio >= 90) return '#1976d2';
        if (s.promedio >= 85) return '#1e88e5';
        if (s.promedio >= 80) return '#42a5f5';
        if (s.promedio >= 75) return '#64b5f6';
        return '#90caf9';
    });
    
    sucursalesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topData.map(s => truncateText(s.sucursal)),
            datasets: [{
                label: 'Performance (%)',
                data: topData.map(s => s.promedio),
                backgroundColor: backgroundColors,
                borderColor: '#ffffff',
                borderWidth: 2,
                borderRadius: {
                    topLeft: 12,
                    topRight: 12,
                    bottomLeft: 0,
                    bottomRight: 0
                },
                borderSkipped: false,
                hoverBackgroundColor: backgroundColors.map(color => color),
                hoverBorderColor: '#333',
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(255,255,255,0.98)',
                    titleColor: '#333',
                    bodyColor: '#666',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    cornerRadius: 12,
                    displayColors: false,
                    padding: 15,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 12
                    },
                    callbacks: {
                        title: function(context) {
                            const dataIndex = context[0].dataIndex;
                            return `#${dataIndex + 1} ${topData[dataIndex].sucursal}`;
                        },
                        label: function(context) {
                            const dataIndex = context.dataIndex;
                            const sucursal = topData[dataIndex];
                            return [
                                `Performance: ${sucursal.promedio.toFixed(1)}%`,
                                `Estado: ${sucursal.estado}`,
                                `Grupo: ${sucursal.grupo_operativo}`,
                                `Supervisiones: ${sucursal.total_supervisiones}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#333',
                        font: {
                            size: 9,
                            weight: '500'
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    max: Math.max(...topData.map(s => s.promedio)) + 5,
                    grid: {
                        color: '#f8f8f8',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#666',
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            animation: {
                duration: 1600,
                easing: 'easeOutBounce',
                delay: (context) => {
                    return context.dataIndex * 80; // Animación escalonada más rápida
                }
            },
            elements: {
                bar: {
                    borderRadius: 12
                }
            }
        }
    });
}

function updateMetricsExtra(estadosData) {
    if (estadosData.length === 0) return;
    
    const promedios = estadosData.map(e => e.promedio);
    const promedioNacional = promedios.reduce((a, b) => a + b, 0) / promedios.length;
    
    const mejorEstado = estadosData.reduce((max, estado) => 
        estado.promedio > max.promedio ? estado : max
    );
    
    const peorEstado = estadosData.reduce((min, estado) => 
        estado.promedio < min.promedio ? estado : min
    );
    
    const rango = Math.max(...promedios) - Math.min(...promedios);
    
    // Update UI
    document.getElementById('promedio-nacional').textContent = `${promedioNacional.toFixed(1)}%`;
    document.getElementById('mejor-estado').textContent = `${mejorEstado.estado} (${mejorEstado.promedio}%)`;
    document.getElementById('peor-estado').textContent = `${peorEstado.estado} (${peorEstado.promedio}%)`;
    document.getElementById('rango-performance').textContent = `${rango.toFixed(1)}%`;
}

function setupEventListeners() {
    // Apply filters
    document.getElementById('apply-filters').addEventListener('click', () => {
        currentFilters = {
            quarter: document.getElementById('quarter-filter').value,
            year: '2025',
            estado: document.getElementById('estado-filter').value,
            grupo: document.getElementById('grupo-filter').value
        };
        loadAllData();
    });
    
    // Ranking controls
    document.getElementById('show-top-10').addEventListener('click', () => updateRankingView(10));
    document.getElementById('show-top-25').addEventListener('click', () => updateRankingView(25));
    document.getElementById('show-all').addEventListener('click', () => updateRankingView(100));
    
    // Export buttons
    document.getElementById('export-pdf').addEventListener('click', () => exportData('pdf'));
    document.getElementById('export-excel').addEventListener('click', () => exportData('excel'));
    document.getElementById('export-json').addEventListener('click', () => exportData('json'));
    
    // Close modal
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('error-modal').style.display = 'none';
    });
}

async function updateRankingView(limit) {
    try {
        const params = new URLSearchParams({...currentFilters, limit});
        const response = await fetch(`/api/sucursales/ranking?${params}`);
        const data = await response.json();
        
        updateSucursalesRanking(data.data);
        
        // Update button states
        document.querySelectorAll('.ranking-controls .btn').forEach(btn => btn.classList.remove('active'));
        if (limit === 10) document.getElementById('show-top-10').classList.add('active');
        else if (limit === 25) document.getElementById('show-top-25').classList.add('active');
        else document.getElementById('show-all').classList.add('active');
        
    } catch (error) {
        console.error('Error actualizando ranking:', error);
    }
}

function updateConnectionStatus(status) {
    const statusDot = document.getElementById('connection-status');
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

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = show ? 'flex' : 'none';
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-modal').style.display = 'block';
}

async function exportData(format) {
    try {
        const params = new URLSearchParams({...currentFilters, format});
        const response = await fetch(`/api/export?${params}`);
        
        if (format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            downloadBlob(blob, `dashboard_data_${new Date().toISOString().split('T')[0]}.json`);
        } else {
            const blob = await response.blob();
            downloadBlob(blob, `dashboard_data_${new Date().toISOString().split('T')[0]}.${format}`);
        }
        
        tg.showAlert('Datos exportados correctamente');
        
    } catch (error) {
        console.error('Error exportando datos:', error);
        showError('Error al exportar los datos');
    }
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Handle Telegram theme changes
tg.onEvent('themeChanged', () => {
    const root = document.documentElement;
    const tgTheme = tg.themeParams;
    
    Object.entries(tgTheme).forEach(([key, value]) => {
        if (value) {
            root.style.setProperty(`--tg-theme-${key.replace(/_/g, '-')}`, value);
        }
    });
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    // Cleanup if needed
});