// ApexCharts Integration for Dashboard - Modern Design
// Reemplaza los gráficos de barras y líneas de Plotly con ApexCharts

// Configuración global de colores y estilos
const dashboardTheme = {
    colors: {
        primary: ['#667eea', '#764ba2'],
        success: ['#48bb78', '#38a169'],
        warning: ['#f6ad55', '#ed8936'],
        danger: ['#fc8181', '#f56565'],
        info: ['#63b3ed', '#4299e1'],
        gradient: {
            excellent: ['#0d47a1', '#1976d2'],
            good: ['#1976d2', '#42a5f5'],
            average: ['#42a5f5', '#90caf9'],
            poor: ['#90caf9', '#ffcdd2']
        }
    },
    borderRadius: 12,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    animations: {
        enabled: true,
        easing: 'easeinout',
        speed: 800,
        delay: 150
    }
};

// Función para obtener color basado en rendimiento
function getPerformanceColor(value) {
    if (value >= 95) return dashboardTheme.colors.gradient.excellent;
    if (value >= 85) return dashboardTheme.colors.gradient.good;
    if (value >= 75) return dashboardTheme.colors.gradient.average;
    return dashboardTheme.colors.gradient.poor;
}

// 1. GRÁFICO DE ESTADOS - Reemplaza updateEstadosChart
function updateEstadosChartApex(data) {
    console.log('📊 Updating Estados chart with ApexCharts:', data.length, 'estados');
    
    const container = document.getElementById('estados-chart');
    if (!container) {
        console.error('❌ Container estados-chart not found');
        return;
    }

    // Limpiar contenedor
    container.innerHTML = '';

    if (!data || data.length === 0) {
        container.innerHTML = '<p style="text-align:center; padding:20px;">No hay datos de estados disponibles</p>';
        return;
    }

    try {
        // Ordenar y tomar los primeros 10 estados
        const topEstados = data
            .sort((a, b) => b.promedio - a.promedio)
            .slice(0, 10);

        const options = {
            series: [{
                name: 'Promedio de Rendimiento',
                data: topEstados.map(d => ({
                    x: d.estado,
                    y: Math.round(d.promedio * 100) / 100,
                    fillColor: {
                        type: 'gradient',
                        gradient: {
                            shade: 'light',
                            type: 'vertical',
                            shadeIntensity: 0.25,
                            gradientToColors: [getPerformanceColor(d.promedio)[1]],
                            inverseColors: false,
                            opacityFrom: 0.85,
                            opacityTo: 0.95,
                            stops: [0, 100]
                        }
                    }
                }))
            }],
            chart: {
                type: 'bar',
                height: 320,
                toolbar: { show: false },
                fontFamily: dashboardTheme.fontFamily,
                animations: dashboardTheme.animations,
                background: 'transparent'
            },
            plotOptions: {
                bar: {
                    borderRadius: dashboardTheme.borderRadius,
                    columnWidth: '70%',
                    distributed: true,
                    dataLabels: {
                        position: 'top'
                    }
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function(val) {
                    return val.toFixed(1) + '%';
                },
                offsetY: -25,
                style: {
                    fontSize: '12px',
                    fontWeight: 600,
                    colors: ['#333']
                }
            },
            legend: { show: false },
            xaxis: {
                categories: topEstados.map(d => d.estado),
                labels: {
                    style: {
                        fontSize: '11px',
                        fontWeight: 600,
                        colors: '#666'
                    },
                    rotate: -45
                },
                axisBorder: { show: false },
                axisTicks: { show: false }
            },
            yaxis: {
                min: 0,
                max: 100,
                labels: {
                    formatter: function(val) {
                        return val.toFixed(0) + '%';
                    },
                    style: {
                        fontSize: '11px',
                        colors: '#666'
                    }
                },
                title: {
                    text: 'Promedio (%)',
                    style: {
                        fontSize: '12px',
                        fontWeight: 600,
                        color: '#666'
                    }
                }
            },
            grid: {
                borderColor: '#f1f1f1',
                strokeDashArray: 3,
                yaxis: {
                    lines: { show: true }
                },
                xaxis: {
                    lines: { show: false }
                }
            },
            tooltip: {
                theme: 'dark',
                style: {
                    fontSize: '12px'
                },
                y: {
                    formatter: function(val) {
                        return val.toFixed(1) + '%';
                    }
                },
                custom: function({series, seriesIndex, dataPointIndex, w}) {
                    const data = topEstados[dataPointIndex];
                    return `
                        <div style="padding: 10px; border-radius: 8px;">
                            <strong>${data.estado}</strong><br>
                            <span style="color: #667eea;">●</span> Promedio: <strong>${data.promedio.toFixed(1)}%</strong><br>
                            <span style="color: #999;">Sucursales: ${data.total_sucursales || 'N/A'}</span>
                        </div>
                    `;
                }
            },
            responsive: [{
                breakpoint: 768,
                options: {
                    chart: { height: 280 },
                    plotOptions: {
                        bar: { columnWidth: '80%' }
                    },
                    xaxis: {
                        labels: { rotate: -90 }
                    }
                }
            }]
        };

        const chart = new ApexCharts(container, options);
        chart.render();
        
        console.log('✅ Estados chart updated successfully with ApexCharts');

    } catch (error) {
        console.error('❌ Error updating estados chart with ApexCharts:', error);
        container.innerHTML = '<p style="text-align:center; padding:20px;">Error al cargar el gráfico de estados</p>';
    }
}

// 2. GRÁFICO DE GRUPOS - Reemplaza updateGruposChart
function updateGruposChartApex(data) {
    console.log('🏢 Updating Grupos chart with ApexCharts:', data.length, 'grupos');
    
    const container = document.getElementById('grupos-chart');
    if (!container) {
        console.error('❌ Container grupos-chart not found');
        return;
    }

    container.innerHTML = '';

    if (!data || data.length === 0) {
        container.innerHTML = '<p style="text-align:center; padding:20px;">No hay datos de grupos disponibles</p>';
        return;
    }

    try {
        // Tomar todos los grupos y ordenar
        const sortedGrupos = data.sort((a, b) => b.promedio - a.promedio);

        const options = {
            series: [{
                name: 'Promedio de Grupo',
                data: sortedGrupos.map(d => ({
                    x: d.grupo_operativo || 'Sin Grupo',
                    y: Math.round(d.promedio * 100) / 100,
                    fillColor: {
                        type: 'gradient',
                        gradient: {
                            shade: 'light',
                            type: 'horizontal',
                            shadeIntensity: 0.25,
                            gradientToColors: [getPerformanceColor(d.promedio)[1]],
                            inverseColors: false,
                            opacityFrom: 0.85,
                            opacityTo: 0.95
                        }
                    }
                }))
            }],
            chart: {
                type: 'bar',
                height: 320,
                toolbar: { show: false },
                fontFamily: dashboardTheme.fontFamily,
                animations: dashboardTheme.animations,
                background: 'transparent'
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    borderRadius: dashboardTheme.borderRadius,
                    barHeight: '60%',
                    distributed: true,
                    dataLabels: {
                        position: 'center'
                    }
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function(val) {
                    return val.toFixed(1) + '%';
                },
                style: {
                    fontSize: '13px',
                    fontWeight: 600,
                    colors: ['#fff']
                },
                dropShadow: {
                    enabled: true,
                    top: 0,
                    left: 0,
                    blur: 3,
                    opacity: 0.8
                }
            },
            legend: { show: false },
            xaxis: {
                min: 0,
                max: 100,
                labels: {
                    formatter: function(val) {
                        return val.toFixed(0) + '%';
                    },
                    style: {
                        fontSize: '11px',
                        colors: '#666'
                    }
                },
                axisBorder: { show: false },
                axisTicks: { show: false }
            },
            yaxis: {
                labels: {
                    style: {
                        fontSize: '11px',
                        fontWeight: 500,
                        colors: '#666'
                    }
                }
            },
            grid: {
                borderColor: '#f1f1f1',
                strokeDashArray: 3,
                xaxis: {
                    lines: { show: true }
                },
                yaxis: {
                    lines: { show: false }
                }
            },
            tooltip: {
                theme: 'dark',
                style: {
                    fontSize: '12px'
                },
                x: {
                    show: false
                },
                y: {
                    formatter: function(val) {
                        return val.toFixed(1) + '%';
                    }
                },
                custom: function({series, seriesIndex, dataPointIndex, w}) {
                    const data = sortedGrupos[dataPointIndex];
                    return `
                        <div style="padding: 10px; border-radius: 8px;">
                            <strong>${data.grupo_operativo || 'Sin Grupo'}</strong><br>
                            <span style="color: #667eea;">●</span> Promedio: <strong>${data.promedio.toFixed(1)}%</strong><br>
                            <span style="color: #999;">Sucursales: ${data.total_sucursales || 'N/A'}</span>
                        </div>
                    `;
                }
            },
            responsive: [{
                breakpoint: 768,
                options: {
                    chart: { height: 400 }
                }
            }]
        };

        const chart = new ApexCharts(container, options);
        chart.render();
        
        console.log('✅ Grupos chart updated successfully with ApexCharts');

    } catch (error) {
        console.error('❌ Error updating grupos chart with ApexCharts:', error);
        container.innerHTML = '<p style="text-align:center; padding:20px;">Error al cargar el gráfico de grupos</p>';
    }
}

// 3. GRÁFICO DE RANKING DE SUCURSALES - Reemplaza updateSucursalesRanking
function updateSucursalesRankingApex(data) {
    console.log('🏆 Updating Sucursales ranking with ApexCharts:', data.length, 'sucursales');
    
    const container = document.getElementById('sucursales-ranking');
    if (!container) {
        console.error('❌ Container sucursales-ranking not found');
        return;
    }

    container.innerHTML = '';

    if (!data || data.length === 0) {
        container.innerHTML = '<p style="text-align:center; padding:20px;">No hay datos de ranking disponibles</p>';
        return;
    }

    try {
        // Aplicar filtros activos y tomar top 15
        let filteredData = [...data];
        
        if (window.currentFilters && window.currentFilters.estado) {
            filteredData = filteredData.filter(d => d.estado === window.currentFilters.estado);
        }
        
        if (window.currentFilters && window.currentFilters.grupo) {
            filteredData = filteredData.filter(d => d.grupo_operativo === window.currentFilters.grupo);
        }
        
        const topSucursales = filteredData
            .sort((a, b) => b.promedio - a.promedio)
            .slice(0, 15);

        const options = {
            series: [{
                name: 'Calificación',
                data: topSucursales.map(d => ({
                    x: d.sucursal || 'Sin Nombre',
                    y: Math.round(d.promedio * 100) / 100,
                    fillColor: {
                        type: 'gradient',
                        gradient: {
                            shade: 'light',
                            type: 'vertical',
                            shadeIntensity: 0.25,
                            gradientToColors: [getPerformanceColor(d.promedio)[1]],
                            inverseColors: false,
                            opacityFrom: 0.85,
                            opacityTo: 0.95
                        }
                    }
                }))
            }],
            chart: {
                type: 'bar',
                height: 420,
                toolbar: { show: false },
                fontFamily: dashboardTheme.fontFamily,
                animations: dashboardTheme.animations,
                background: 'transparent'
            },
            plotOptions: {
                bar: {
                    borderRadius: dashboardTheme.borderRadius,
                    columnWidth: '80%',
                    distributed: true,
                    dataLabels: {
                        position: 'top'
                    }
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function(val) {
                    return val.toFixed(1) + '%';
                },
                offsetY: -20,
                style: {
                    fontSize: '11px',
                    fontWeight: 600,
                    colors: ['#333']
                }
            },
            legend: { show: false },
            xaxis: {
                categories: topSucursales.map(d => d.sucursal || 'Sin Nombre'),
                labels: {
                    style: {
                        fontSize: '10px',
                        fontWeight: 500,
                        colors: '#666'
                    },
                    rotate: -45,
                    maxHeight: 60
                },
                axisBorder: { show: false },
                axisTicks: { show: false }
            },
            yaxis: {
                min: 0,
                max: 100,
                labels: {
                    formatter: function(val) {
                        return val.toFixed(0) + '%';
                    },
                    style: {
                        fontSize: '11px',
                        colors: '#666'
                    }
                },
                title: {
                    text: 'Calificación (%)',
                    style: {
                        fontSize: '12px',
                        fontWeight: 600,
                        color: '#666'
                    }
                }
            },
            grid: {
                borderColor: '#f1f1f1',
                strokeDashArray: 3,
                yaxis: {
                    lines: { show: true }
                },
                xaxis: {
                    lines: { show: false }
                }
            },
            tooltip: {
                theme: 'dark',
                style: {
                    fontSize: '12px'
                },
                y: {
                    formatter: function(val) {
                        return val.toFixed(1) + '%';
                    }
                },
                custom: function({series, seriesIndex, dataPointIndex, w}) {
                    const data = topSucursales[dataPointIndex];
                    return `
                        <div style="padding: 10px; border-radius: 8px;">
                            <strong>${data.sucursal || 'Sin Nombre'}</strong><br>
                            <span style="color: #667eea;">●</span> Calificación: <strong>${data.promedio.toFixed(1)}%</strong><br>
                            <span style="color: #999;">Estado: ${data.estado || 'N/A'}</span><br>
                            <span style="color: #999;">Grupo: ${data.grupo_operativo || 'N/A'}</span>
                        </div>
                    `;
                }
            },
            responsive: [{
                breakpoint: 768,
                options: {
                    chart: { height: 350 },
                    plotOptions: {
                        bar: { columnWidth: '90%' }
                    },
                    xaxis: {
                        labels: { rotate: -90 }
                    }
                }
            }]
        };

        const chart = new ApexCharts(container, options);
        chart.render();
        
        console.log('✅ Sucursales ranking updated successfully with ApexCharts');

    } catch (error) {
        console.error('❌ Error updating sucursales ranking with ApexCharts:', error);
        container.innerHTML = '<p style="text-align:center; padding:20px;">Error al cargar el ranking de sucursales</p>';
    }
}

// 4. GRÁFICO DE RANKING DE ESTADOS - Nuevo para el dashboard
function updateEstadosRankingApex(data) {
    console.log('📊 Updating Estados ranking with ApexCharts:', data.length, 'estados');
    
    const container = document.getElementById('estados-ranking');
    if (!container) {
        console.error('❌ Container estados-ranking not found');
        return;
    }

    container.innerHTML = '';

    if (!data || data.length === 0) {
        container.innerHTML = '<p style="text-align:center; padding:20px;">No hay datos de estados disponibles</p>';
        return;
    }

    try {
        // Ordenar todos los estados
        const rankedEstados = data.sort((a, b) => b.promedio - a.promedio);

        const options = {
            series: [{
                name: 'Ranking',
                data: rankedEstados.map((d, index) => ({
                    x: `#${index + 1} ${d.estado}`,
                    y: Math.round(d.promedio * 100) / 100,
                    fillColor: {
                        type: 'gradient',
                        gradient: {
                            shade: 'light',
                            type: 'horizontal',
                            shadeIntensity: 0.25,
                            gradientToColors: [getPerformanceColor(d.promedio)[1]],
                            inverseColors: false,
                            opacityFrom: 0.85,
                            opacityTo: 0.95
                        }
                    }
                }))
            }],
            chart: {
                type: 'bar',
                height: 380,
                toolbar: { show: false },
                fontFamily: dashboardTheme.fontFamily,
                animations: {
                    ...dashboardTheme.animations,
                    dynamicAnimation: {
                        enabled: true,
                        speed: 350
                    }
                },
                background: 'transparent'
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    borderRadius: dashboardTheme.borderRadius,
                    barHeight: '65%',
                    distributed: true,
                    dataLabels: {
                        position: 'center'
                    }
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function(val) {
                    return val.toFixed(1) + '%';
                },
                style: {
                    fontSize: '12px',
                    fontWeight: 600,
                    colors: ['#fff']
                },
                dropShadow: {
                    enabled: true,
                    blur: 3,
                    opacity: 0.8
                }
            },
            legend: { show: false },
            xaxis: {
                min: 0,
                max: 100,
                labels: {
                    formatter: function(val) {
                        return val.toFixed(0) + '%';
                    },
                    style: {
                        fontSize: '11px',
                        colors: '#666'
                    }
                }
            },
            yaxis: {
                labels: {
                    style: {
                        fontSize: '10px',
                        fontWeight: 500,
                        colors: '#666'
                    }
                }
            },
            grid: {
                borderColor: '#f1f1f1',
                strokeDashArray: 3
            },
            tooltip: {
                theme: 'dark',
                x: { show: false },
                y: {
                    formatter: function(val) {
                        return val.toFixed(1) + '%';
                    }
                },
                custom: function({series, seriesIndex, dataPointIndex, w}) {
                    const data = rankedEstados[dataPointIndex];
                    return `
                        <div style="padding: 10px; border-radius: 8px;">
                            <strong>Posición #${dataPointIndex + 1}</strong><br>
                            <strong>${data.estado}</strong><br>
                            <span style="color: #667eea;">●</span> Promedio: <strong>${data.promedio.toFixed(1)}%</strong><br>
                            <span style="color: #999;">Sucursales: ${data.total_sucursales || 'N/A'}</span>
                        </div>
                    `;
                }
            }
        };

        const chart = new ApexCharts(container, options);
        chart.render();
        
        console.log('✅ Estados ranking updated successfully with ApexCharts');

    } catch (error) {
        console.error('❌ Error updating estados ranking with ApexCharts:', error);
        container.innerHTML = '<p style="text-align:center; padding:20px;">Error al cargar el ranking de estados</p>';
    }
}

// Exportar funciones para uso global
console.log('🔧 Exporting ApexCharts integration functions...');

// Funciones globales para uso directo
window.updateEstadosChartApex = updateEstadosChartApex;
window.updateGruposChartApex = updateGruposChartApex;
window.updateSucursalesRankingApex = updateSucursalesRankingApex;
window.updateEstadosRankingApex = updateEstadosRankingApex;

// También exportar como objeto para compatibilidad
window.apexChartsIntegration = {
    updateEstadosChartApex,
    updateGruposChartApex,
    updateSucursalesRankingApex,
    updateEstadosRankingApex,
    dashboardTheme,
    getPerformanceColor
};

console.log('✅ ApexCharts integration functions exported successfully');