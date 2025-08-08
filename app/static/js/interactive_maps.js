// Opciones de Mapas Interactivos para México

// 1. MAPA CON ESTADOS RESALTABLES (Click para activar/desactivar)
function createHighlightableMap(estadosData, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Estados activos en el estudio
    const activeStates = new Set();
    estadosData.forEach(estado => activeStates.add(estado.estado));
    
    // Obtener GeoJSON
    const geoJson = getMexicoAngelGeoJSON();
    
    // Crear dos capas: estados inactivos y estados activos
    const inactiveTrace = {
        type: 'choropleth',
        locationmode: 'geojson-id',
        geojson: geoJson,
        locations: [],
        z: [],
        text: [],
        colorscale: [[0, '#e0e0e0'], [1, '#e0e0e0']], // Gris para inactivos
        showscale: false,
        hovertemplate: '%{text}<extra></extra>',
        marker: {
            line: { color: 'white', width: 1 }
        }
    };
    
    const activeTrace = {
        type: 'choropleth',
        locationmode: 'geojson-id',
        geojson: geoJson,
        locations: [],
        z: [],
        text: [],
        customdata: [],
        colorscale: [
            [0, '#ffcdd2'],
            [0.3, '#90caf9'],
            [0.6, '#42a5f5'],
            [0.8, '#1976d2'],
            [1, '#0d47a1']
        ],
        colorbar: {
            title: 'Promedio (%)',
            thickness: 15,
            len: 0.7
        },
        hovertemplate: '%{text}<extra></extra>',
        marker: {
            line: { color: 'white', width: 2 }
        }
    };
    
    // Mapear datos
    const stateDataMap = {};
    estadosData.forEach(d => {
        stateDataMap[d.estado] = d;
    });
    
    // Procesar features del GeoJSON
    geoJson.features.forEach(feature => {
        const stateName = feature.properties.estado || feature.properties.name;
        const featureId = feature.id || stateName;
        
        if (activeStates.has(stateName)) {
            // Estado activo en el estudio
            const data = stateDataMap[stateName];
            activeTrace.locations.push(featureId);
            activeTrace.z.push(data.promedio);
            activeTrace.text.push(`<b>${stateName}</b><br>Promedio: ${data.promedio.toFixed(1)}%<br>Sucursales: ${data.total_sucursales}<br><i>Click para filtrar</i>`);
            activeTrace.customdata.push(stateName);
        } else {
            // Estado no incluido en el estudio
            inactiveTrace.locations.push(featureId);
            inactiveTrace.z.push(0);
            inactiveTrace.text.push(`<b>${stateName}</b><br><i>No incluido en el estudio</i>`);
        }
    });
    
    const layout = {
        geo: {
            scope: 'north america',
            showframe: false,
            showcoastlines: false,
            projection: { type: 'mercator' },
            center: { lat: 23.6345, lon: -102.5528 },
            lonaxis: { range: [-117, -87] },
            lataxis: { range: [14, 33] },
            bgcolor: '#f5f5f5'
        },
        height: 400,
        margin: { t: 30, b: 10, l: 10, r: 10 },
        title: {
            text: `Estados en el Estudio (${activeStates.size} de 32)`,
            font: { size: 16 }
        },
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#f5f5f5'
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d']
    };
    
    Plotly.newPlot(containerId, [inactiveTrace, activeTrace], layout, config);
    
    // Agregar interactividad
    container.on('plotly_click', function(data) {
        if (data.points[0].curveNumber === 1 && data.points[0].customdata) {
            const selectedState = data.points[0].customdata;
            // Actualizar filtro
            document.getElementById('estado-filter').value = selectedState;
            currentFilters.estado = selectedState;
            loadAllData();
            showNotification(`Filtrando por: ${selectedState}`);
        }
    });
}

// 2. MAPA DE BURBUJAS (Tamaño según número de sucursales)
function createBubbleMap(sucursalesData, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Agrupar por estado y calcular centros
    const stateGroups = {};
    sucursalesData.forEach(suc => {
        if (!stateGroups[suc.estado]) {
            stateGroups[suc.estado] = {
                sucursales: [],
                lat_sum: 0,
                lon_sum: 0,
                count: 0,
                promedio_sum: 0
            };
        }
        if (suc.latitud && suc.longitud) {
            stateGroups[suc.estado].sucursales.push(suc);
            stateGroups[suc.estado].lat_sum += suc.latitud;
            stateGroups[suc.estado].lon_sum += suc.longitud;
            stateGroups[suc.estado].promedio_sum += suc.promedio;
            stateGroups[suc.estado].count++;
        }
    });
    
    // Crear datos para las burbujas
    const bubbleData = [];
    Object.entries(stateGroups).forEach(([estado, data]) => {
        if (data.count > 0) {
            bubbleData.push({
                estado: estado,
                lat: data.lat_sum / data.count,
                lon: data.lon_sum / data.count,
                count: data.count,
                promedio: data.promedio_sum / data.count
            });
        }
    });
    
    const trace = {
        type: 'scattermapbox',
        mode: 'markers+text',
        lat: bubbleData.map(d => d.lat),
        lon: bubbleData.map(d => d.lon),
        text: bubbleData.map(d => d.estado),
        textposition: 'top center',
        marker: {
            size: bubbleData.map(d => Math.sqrt(d.count) * 10),
            color: bubbleData.map(d => d.promedio),
            colorscale: [
                [0, '#ffcdd2'],
                [0.3, '#90caf9'],
                [0.6, '#42a5f5'],
                [0.8, '#1976d2'],
                [1, '#0d47a1']
            ],
            colorbar: {
                title: 'Promedio (%)',
                thickness: 15
            },
            opacity: 0.7,
            line: {
                color: 'white',
                width: 2
            }
        },
        customdata: bubbleData.map(d => d.estado),
        hovertemplate: '<b>%{text}</b><br>' +
                      'Sucursales: %{marker.size:,.0f}<br>' +
                      'Promedio: %{marker.color:.1f}%<br>' +
                      '<i>Click para filtrar</i>' +
                      '<extra></extra>'
    };
    
    const layout = {
        mapbox: {
            style: 'open-street-map',
            center: { lat: 23.6345, lon: -102.5528 },
            zoom: 4.5
        },
        height: 400,
        margin: { t: 30, b: 10, l: 10, r: 10 },
        title: {
            text: 'Distribución de Sucursales por Estado',
            font: { size: 16 }
        }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };
    
    Plotly.newPlot(containerId, [trace], layout, config);
    
    // Interactividad
    container.on('plotly_click', function(data) {
        if (data.points[0].customdata) {
            const selectedState = data.points[0].customdata;
            document.getElementById('estado-filter').value = selectedState;
            currentFilters.estado = selectedState;
            loadAllData();
            showNotification(`Filtrando por: ${selectedState}`);
        }
    });
}

// 3. MAPA DE CALOR (Heatmap)
function createHeatmap(sucursalesData, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const validData = sucursalesData.filter(d => 
        d.latitud && d.longitud && !isNaN(d.latitud) && !isNaN(d.longitud)
    );
    
    const trace = {
        type: 'densitymapbox',
        lat: validData.map(d => d.latitud),
        lon: validData.map(d => d.longitud),
        z: validData.map(d => d.promedio),
        radius: 20,
        colorscale: [
            [0, 'rgba(255, 205, 210, 0)'],
            [0.2, 'rgba(144, 202, 249, 0.5)'],
            [0.4, 'rgba(66, 165, 245, 0.7)'],
            [0.6, 'rgba(25, 118, 210, 0.8)'],
            [0.8, 'rgba(13, 71, 161, 0.9)'],
            [1, 'rgba(13, 71, 161, 1)']
        ],
        showscale: true,
        colorbar: {
            title: 'Densidad de<br>Rendimiento',
            thickness: 15
        },
        hovertemplate: 'Densidad: %{z}<extra></extra>'
    };
    
    const layout = {
        mapbox: {
            style: 'open-street-map',
            center: { lat: 23.6345, lon: -102.5528 },
            zoom: 4.5
        },
        height: 400,
        margin: { t: 30, b: 10, l: 10, r: 10 },
        title: {
            text: 'Mapa de Calor - Rendimiento por Zona',
            font: { size: 16 }
        }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };
    
    Plotly.newPlot(containerId, [trace], layout, config);
}

// 4. MAPA COMPARATIVO (Antes/Después o Trimestre vs Trimestre)
function createComparativeMap(estadosDataQ1, estadosDataQ2, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const geoJson = getMexicoAngelGeoJSON();
    
    // Calcular diferencias
    const differences = {};
    estadosDataQ2.forEach(estado => {
        const q1Data = estadosDataQ1.find(e => e.estado === estado.estado);
        if (q1Data) {
            differences[estado.estado] = {
                diff: estado.promedio - q1Data.promedio,
                q1: q1Data.promedio,
                q2: estado.promedio
            };
        }
    });
    
    const locations = [];
    const values = [];
    const text = [];
    
    geoJson.features.forEach(feature => {
        const stateName = feature.properties.estado || feature.properties.name;
        if (differences[stateName]) {
            locations.push(feature.id || stateName);
            values.push(differences[stateName].diff);
            text.push(`<b>${stateName}</b><br>` +
                     `Q1: ${differences[stateName].q1.toFixed(1)}%<br>` +
                     `Q2: ${differences[stateName].q2.toFixed(1)}%<br>` +
                     `Cambio: ${differences[stateName].diff > 0 ? '+' : ''}${differences[stateName].diff.toFixed(1)}%`);
        }
    });
    
    const trace = {
        type: 'choropleth',
        locationmode: 'geojson-id',
        geojson: geoJson,
        locations: locations,
        z: values,
        text: text,
        hovertemplate: '%{text}<extra></extra>',
        colorscale: [
            [0, '#d32f2f'],
            [0.4, '#f44336'],
            [0.5, '#ffffff'],
            [0.6, '#4caf50'],
            [1, '#388e3c']
        ],
        zmid: 0,
        colorbar: {
            title: 'Cambio (%)',
            thickness: 15,
            tickmode: 'linear',
            dtick: 5
        },
        marker: {
            line: { color: 'white', width: 1 }
        }
    };
    
    const layout = {
        geo: {
            scope: 'north america',
            showframe: false,
            showcoastlines: false,
            projection: { type: 'mercator' },
            center: { lat: 23.6345, lon: -102.5528 },
            lonaxis: { range: [-117, -87] },
            lataxis: { range: [14, 33] },
            bgcolor: '#f5f5f5'
        },
        height: 400,
        margin: { t: 40, b: 10, l: 10, r: 10 },
        title: {
            text: 'Comparación Q1 vs Q2 - Cambio en Rendimiento',
            font: { size: 16 }
        }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };
    
    Plotly.newPlot(containerId, [trace], layout, config);
}

// 5. MAPA CON ANIMACIÓN TEMPORAL
function createAnimatedMap(historicalData, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const geoJson = getMexicoAngelGeoJSON();
    
    // Organizar datos por trimestre
    const quarterData = {};
    historicalData.forEach(d => {
        if (!quarterData[d.quarter]) {
            quarterData[d.quarter] = [];
        }
        quarterData[d.quarter].push(d);
    });
    
    // Crear frames para animación
    const frames = [];
    const sliderSteps = [];
    
    Object.keys(quarterData).sort().forEach((quarter, idx) => {
        const data = quarterData[quarter];
        const locations = [];
        const values = [];
        const text = [];
        
        data.forEach(estado => {
            locations.push(estado.estado);
            values.push(estado.promedio);
            text.push(`${estado.estado}<br>Promedio: ${estado.promedio.toFixed(1)}%`);
        });
        
        frames.push({
            name: quarter,
            data: [{
                type: 'choropleth',
                locationmode: 'geojson-id',
                geojson: geoJson,
                locations: locations,
                z: values,
                text: text
            }]
        });
        
        sliderSteps.push({
            label: quarter,
            method: 'animate',
            args: [[quarter], {
                mode: 'immediate',
                transition: { duration: 300 },
                frame: { duration: 300 }
            }]
        });
    });
    
    const firstQuarter = Object.keys(quarterData).sort()[0];
    const initialData = quarterData[firstQuarter];
    
    const trace = {
        type: 'choropleth',
        locationmode: 'geojson-id',
        geojson: geoJson,
        locations: initialData.map(d => d.estado),
        z: initialData.map(d => d.promedio),
        text: initialData.map(d => `${d.estado}<br>Promedio: ${d.promedio.toFixed(1)}%`),
        hovertemplate: '%{text}<extra></extra>',
        colorscale: [
            [0, '#ffcdd2'],
            [0.3, '#90caf9'],
            [0.6, '#42a5f5'],
            [0.8, '#1976d2'],
            [1, '#0d47a1']
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
            projection: { type: 'mercator' },
            center: { lat: 23.6345, lon: -102.5528 },
            lonaxis: { range: [-117, -87] },
            lataxis: { range: [14, 33] },
            bgcolor: '#f5f5f5'
        },
        height: 450,
        margin: { t: 50, b: 100, l: 10, r: 10 },
        title: {
            text: 'Evolución Temporal del Rendimiento',
            font: { size: 16 }
        },
        updatemenus: [{
            type: 'buttons',
            showactive: false,
            y: 1,
            yanchor: 'top',
            xanchor: 'left',
            x: 0.1,
            buttons: [{
                label: 'Play',
                method: 'animate',
                args: [null, {
                    fromcurrent: true,
                    transition: { duration: 300 },
                    frame: { duration: 500 }
                }]
            }, {
                label: 'Pause',
                method: 'animate',
                args: [[null], {
                    mode: 'immediate',
                    transition: { duration: 0 },
                    frame: { duration: 0 }
                }]
            }]
        }],
        sliders: [{
            active: 0,
            yanchor: 'top',
            xanchor: 'left',
            currentvalue: {
                font: { size: 16 },
                prefix: 'Trimestre: ',
                visible: true,
                xanchor: 'right'
            },
            transition: { duration: 300 },
            pad: { b: 10, t: 50 },
            len: 0.9,
            x: 0.1,
            y: 0,
            steps: sliderSteps
        }]
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };
    
    Plotly.newPlot(containerId, [trace], layout, config).then(function() {
        Plotly.addFrames(containerId, frames);
    });
}

// Función de utilidad para mostrar notificaciones
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'map-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(0, 136, 204, 0.9);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Exportar funciones para uso global
window.interactiveMaps = {
    createHighlightableMap,
    createBubbleMap,
    createHeatmap,
    createComparativeMap,
    createAnimatedMap
};