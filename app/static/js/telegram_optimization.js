// Optimizaciones específicas para Telegram Mini App

console.log('📱 Inicializando optimizaciones para Telegram Mini App...');

// Detectar si estamos en Telegram
const isTelegramWebApp = window.Telegram && window.Telegram.WebApp;

if (isTelegramWebApp) {
    console.log('✅ Ejecutándose en Telegram Mini App');
    
    // Configurar tema de Telegram
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    // Aplicar colores del tema de Telegram a ApexCharts
    if (tg.colorScheme) {
        console.log('🎨 Aplicando tema de Telegram:', tg.colorScheme);
        
        // Actualizar variables CSS según el tema
        const root = document.documentElement;
        
        if (tg.colorScheme === 'dark') {
            root.style.setProperty('--telegram-bg', tg.themeParams.bg_color || '#1a1a1a');
            root.style.setProperty('--telegram-text', tg.themeParams.text_color || '#ffffff');
            root.style.setProperty('--telegram-secondary-bg', tg.themeParams.secondary_bg_color || '#2a2a2a');
        } else {
            root.style.setProperty('--telegram-bg', tg.themeParams.bg_color || '#ffffff');
            root.style.setProperty('--telegram-text', tg.themeParams.text_color || '#000000');
            root.style.setProperty('--telegram-secondary-bg', tg.themeParams.secondary_bg_color || '#f5f5f5');
        }
    }
    
    // Optimizar rendimiento para dispositivos móviles
    const optimizeForMobile = () => {
        // Reducir animaciones en dispositivos lentos
        if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
            console.log('📱 Dispositivo de recursos limitados, optimizando...');
            
            // Desactivar algunas animaciones complejas
            const style = document.createElement('style');
            style.textContent = `
                .apexcharts-canvas {
                    animation-duration: 0.3s !important;
                }
                .loading-spinner {
                    animation-duration: 2s !important;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Optimizar scroll en iOS
        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
            console.log('🍎 Dispositivo iOS detectado, aplicando optimizaciones...');
            document.body.style.webkitOverflowScrolling = 'touch';
        }
    };
    
    // Manejo de eventos táctiles mejorado
    const optimizeTouchEvents = () => {
        // Mejorar responsividad de botones
        const buttons = document.querySelectorAll('.btn, .filter-select, .modern-button');
        buttons.forEach(btn => {
            btn.style.touchAction = 'manipulation';
        });
        
        // Prevenir zoom accidental en gráficos
        document.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });
        
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(e) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    };
    
    // Aplicar optimizaciones cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            optimizeForMobile();
            optimizeTouchEvents();
        });
    } else {
        optimizeForMobile();
        optimizeTouchEvents();
    }
    
    // Notificar a Telegram cuando el contenido esté listo
    const notifyTelegramWhenReady = () => {
        let attemptCount = 0;
        const maxAttempts = 15; // 30 seconds max
        
        // Esperar a que los gráficos se carguen
        const checkGraphicsLoaded = () => {
            attemptCount++;
            console.log(`📊 Checking graphics... attempt ${attemptCount}/${maxAttempts}`);
            
            const charts = document.querySelectorAll('.apexcharts-canvas, .plotly, .plotly-graph-div');
            const loadedCharts = Array.from(charts).filter(chart => 
                chart.children.length > 0 || chart.innerHTML.includes('svg') || chart.offsetWidth > 0
            );
            
            console.log(`📈 Found ${charts.length} chart containers, ${loadedCharts.length} loaded`);
            
            if (loadedCharts.length > 0) {
                console.log('✅ Gráficos cargados, notificando a Telegram...');
                try {
                    if (tg.MainButton) {
                        tg.MainButton.setText('✅ Dashboard Listo');
                        tg.MainButton.show();
                        
                        if (tg.HapticFeedback) {
                            tg.HapticFeedback.notificationOccurred('success');
                        }
                        
                        setTimeout(() => {
                            tg.MainButton.hide();
                        }, 3000);
                    }
                } catch (error) {
                    console.error('❌ Error with Telegram MainButton:', error);
                }
                clearInterval(checkInterval);
                return true;
            }
            
            if (attemptCount >= maxAttempts) {
                console.log('⏰ Max attempts reached, stopping check');
                clearInterval(checkInterval);
                return false;
            }
            
            return false;
        };
        
        // Verificar cada 2 segundos hasta que los gráficos estén listos
        const checkInterval = setInterval(checkGraphicsLoaded, 2000);
        
        // Initial check
        checkGraphicsLoaded();
    };
    
    // Inicializar notificación
    setTimeout(notifyTelegramWhenReady, 3000);
    
} else {
    console.log('🌐 Ejecutándose en navegador web estándar');
    
    // Aplicar estilos para navegador web
    const style = document.createElement('style');
    style.textContent = `
        body {
            max-width: 400px;
            margin: 0 auto;
            background: #f5f5f5;
        }
        .dashboard-container {
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            background: white;
            min-height: 100vh;
        }
    `;
    document.head.appendChild(style);
}

// Funciones de utilidad para mejorar la experiencia
window.telegramUtils = {
    // Función para mostrar notificaciones optimizadas
    showNotification: (message, type = 'info') => {
        if (isTelegramWebApp) {
            // Usar HapticFeedback de Telegram
            const tg = window.Telegram.WebApp;
            if (type === 'success') {
                tg.HapticFeedback.notificationOccurred('success');
            } else if (type === 'error') {
                tg.HapticFeedback.notificationOccurred('error');
            } else {
                tg.HapticFeedback.impactOccurred('light');
            }
            
            // Mostrar en la barra de estado de Telegram si es posible
            console.log(`📱 Telegram: ${message}`);
        } else {
            // Fallback para navegador web
            console.log(`🌐 Web: ${message}`);
        }
    },
    
    // Función para optimizar imágenes y gráficos según la conexión
    optimizeForConnection: () => {
        if (navigator.connection) {
            const connection = navigator.connection;
            console.log('🌐 Tipo de conexión:', connection.effectiveType);
            
            if (connection.effectiveType === '2g' || connection.effectiveType === 'slow-2g') {
                console.log('📡 Conexión lenta detectada, aplicando optimizaciones...');
                
                // Reducir calidad de gráficos
                const style = document.createElement('style');
                style.textContent = `
                    .apexcharts-canvas {
                        animation: none !important;
                        transition: none !important;
                    }
                    .chart-plot canvas {
                        image-rendering: -webkit-optimize-contrast !important;
                    }
                `;
                document.head.appendChild(style);
            }
        }
    }
};

// Aplicar optimizaciones de conexión
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.telegramUtils.optimizeForConnection);
} else {
    window.telegramUtils.optimizeForConnection();
}

console.log('✅ Optimizaciones de Telegram Mini App cargadas');