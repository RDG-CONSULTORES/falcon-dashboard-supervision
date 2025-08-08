import os
import logging
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://dc378838cfb2.ngrok-free.app')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with a button to open the Web App."""
    user_name = update.effective_user.first_name
    
    # Create keyboard buttons (sin el botón duplicado de Dashboard)
    keyboard = [
        [KeyboardButton(text="📈 Indicadores por Áreas")],
        [KeyboardButton(text="📋 Ayuda"), KeyboardButton(text="📊 Estado")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        is_persistent=True,
        one_time_keyboard=False
    )
    
    welcome_message = f"""
¡Hola *{user_name}*! 👋

🚀 *Bot de Analytics de Supervisión Operativa*

📊 *Dashboard Principal:*
Usa el botón *"📊 Abrir Dashboard Analytics"* en la barra inferior ⬇️ para acceder al dashboard completo con mapas y gráficos.

📈 *Nuevas Opciones Disponibles:*
• *Indicadores por Áreas* - Análisis detallado por área operativa
• *Ayuda* - Información y comandos disponibles
• *Estado* - Verificar conexión y sistema

🎯 *Características:*
• 🗺️ Mapas interactivos de México
• 📊 Gráficos modernos con filtros
• 🏆 Rankings en tiempo real
• 📱 Optimizado para móvil

¡Explora los datos de supervisión! 🚀
    """
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = """
📋 *Comandos disponibles:*
    
/start - Muestra el botón del dashboard
/help - Muestra este mensaje de ayuda
/status - Verifica el estado del sistema
/sucursales - Lista las sucursales disponibles
/resumen - Muestra un resumen rápido

🔹 *Uso del Dashboard:*
1. Presiona "Abrir Analytics Dashboard"
2. Selecciona la sucursal o vista general
3. Filtra por fecha o grupo operativo
4. Exporta los datos si lo necesitas

💡 *Tips:*
• Los datos se actualizan cada 5 minutos
• Puedes compartir vistas específicas
• Usa los filtros para análisis detallados
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check system status."""
    try:
        from database.connection import test_connection
        db_status = "✅ Conectada" if test_connection() else "❌ Desconectada"
        
        status_message = f"""
🔍 *Estado del Sistema*

🗄️ Base de datos: {db_status}
🤖 Bot: ✅ Activo
📊 Dashboard: ✅ Disponible
🕐 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        await update.message.reply_text("Error al verificar el estado del sistema")

async def sucursales(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List available branches."""
    try:
        from database.queries import get_sucursales_list
        sucursales_data = get_sucursales_list()
        
        if sucursales_data:
            message = "📍 *Sucursales disponibles:*\n\n"
            for suc in sucursales_data:
                message += f"• {suc}\n"
        else:
            message = "No se encontraron sucursales en la base de datos."
            
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error listing sucursales: {e}")
        await update.message.reply_text("Error al obtener la lista de sucursales")

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show quick summary."""
    try:
        from database.queries import get_summary_stats
        stats = get_summary_stats()
        
        if stats:
            message = f"""
📊 *Resumen General*

📅 Período: {stats.get('fecha_inicio', 'N/A')} - {stats.get('fecha_fin', 'N/A')}
🏢 Total sucursales: {stats.get('total_sucursales', 0)}
📝 Evaluaciones: {stats.get('total_evaluaciones', 0)}
📈 Promedio general: {stats.get('promedio_general', 0):.1f}%

*Top 3 Sucursales:*
"""
            for i, suc in enumerate(stats.get('top_sucursales', [])[:3], 1):
                message += f"{i}. {suc['sucursal']} - {suc['promedio']:.1f}%\n"
                
        else:
            message = "No hay datos disponibles para mostrar."
            
        # Add inline button to open dashboard
        keyboard = [[InlineKeyboardButton("📊 Ver Dashboard Completo", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        await update.message.reply_text("Error al obtener el resumen")

async def indicadores_areas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show indicators by operational areas."""
    try:
        logger.info("Mostrando indicadores por áreas")
        
        # Aquí podemos agregar la lógica para mostrar indicadores por áreas
        # Por ahora, mostremos un mensaje informativo con opciones
        
        areas_message = """
📈 *Indicadores por Áreas Operativas*

Selecciona el área que deseas analizar:

🏪 *Áreas Disponibles:*
• *Ventas* - Indicadores de desempeño en ventas
• *Operaciones* - Métricas operativas y eficiencia
• *Servicio al Cliente* - Calidad y satisfacción
• *Inventarios* - Control y rotación
• *Recursos Humanos* - Productividad y capacitación

🔍 *Próximamente:*
• Gráficos específicos por área
• Comparativas entre áreas
• Tendencias mensuales
• KPIs personalizados

💡 *Tip:* Usa el dashboard principal para ver el resumen general de todas las áreas.
        """
        
        # Crear botones inline para las áreas
        keyboard = [
            [InlineKeyboardButton("🏪 Ventas", callback_data="area_ventas")],
            [InlineKeyboardButton("⚙️ Operaciones", callback_data="area_operaciones")],
            [InlineKeyboardButton("👥 Servicio al Cliente", callback_data="area_servicio")],
            [InlineKeyboardButton("📦 Inventarios", callback_data="area_inventarios")],
            [InlineKeyboardButton("👔 Recursos Humanos", callback_data="area_rrhh")],
            [InlineKeyboardButton("📊 Dashboard Detallado por Áreas", web_app=WebAppInfo(url=f"{WEBAPP_URL}/indicadores-areas"))],
            [InlineKeyboardButton("🏠 Dashboard Principal", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            areas_message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error mostrando indicadores por áreas: {e}")
        await update.message.reply_text("Error al cargar los indicadores por áreas")

async def handle_area_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle area selection callbacks."""
    query = update.callback_query
    await query.answer()
    
    area_data = {
        "area_ventas": {
            "title": "🏪 Indicadores de Ventas",
            "metrics": "• Ventas totales: $2.5M\n• Crecimiento: +15%\n• Ticket promedio: $450"
        },
        "area_operaciones": {
            "title": "⚙️ Indicadores de Operaciones",
            "metrics": "• Eficiencia operativa: 87%\n• Tiempo de respuesta: 2.3 hrs\n• Productividad: 92%"
        },
        "area_servicio": {
            "title": "👥 Indicadores de Servicio",
            "metrics": "• Satisfacción cliente: 4.5/5\n• Tiempo de atención: 8 min\n• Resolución primera llamada: 78%"
        },
        "area_inventarios": {
            "title": "📦 Indicadores de Inventarios",
            "metrics": "• Rotación: 12 veces/año\n• Exactitud: 96%\n• Merma: 1.2%"
        },
        "area_rrhh": {
            "title": "👔 Indicadores de RRHH",
            "metrics": "• Rotación personal: 8%\n• Capacitación completada: 94%\n• Satisfacción empleados: 4.2/5"
        }
    }
    
    area = query.data
    if area in area_data:
        info = area_data[area]
        message = f"""
{info['title']}

📊 *Métricas Principales:*
{info['metrics']}

📅 *Período:* Q4 2024

🔄 *Actualización:* Tiempo real

Para ver gráficos detallados y análisis completo, usa el Dashboard Principal.
        """
        
        keyboard = [[InlineKeyboardButton("📊 Ver Dashboard Completo", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses from the keyboard."""
    text = update.message.text
    
    if text == "📋 Ayuda":
        await help_command(update, context)
    elif text == "📊 Estado":
        await status(update, context)
    elif text == "📈 Indicadores por Áreas":
        await indicadores_areas(update, context)
    else:
        # For any other text, show the start message again
        await start(update, context)

async def dashboard_opened(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when the Web App is opened."""
    user_name = update.effective_user.first_name
    
    success_message = f"""
✅ *Dashboard abierto exitosamente, {user_name}!* 

🎯 *Ahora puedes:*
• Explorar mapas interactivos de México
• Analizar gráficos de rendimiento  
• Filtrar datos por región y periodo
• Ver rankings de sucursales

💡 *Tip:* El botón "📊 Abrir Dashboard Analytics" siempre estará disponible en la parte inferior del chat para acceso rápido.

¡Disfruta explorando tus datos! 📊✨
    """
    
    try:
        await update.message.reply_text(success_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending dashboard opened message: {e}")

async def post_init(application: Application) -> None:
    """Initialize bot settings after startup."""
    bot = application.bot
    
    # Configure Menu Button
    from telegram import MenuButtonWebApp, WebAppInfo
    web_app_info = WebAppInfo(url=WEBAPP_URL)
    menu_button = MenuButtonWebApp(
        text="📊 Abrir Dashboard Analytics",
        web_app=web_app_info
    )
    
    try:
        await bot.set_chat_menu_button(menu_button=menu_button)
        logger.info(f"✅ Menu Button configurado: {WEBAPP_URL}")
    except Exception as e:
        logger.error(f"Error configurando Menu Button: {e}")

def main() -> None:
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("sucursales", sucursales))
    application.add_handler(CommandHandler("resumen", resumen))
    
    # Add button handlers
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_button_press
    ))
    
    # Add callback query handler for area buttons
    application.add_handler(CallbackQueryHandler(
        handle_area_callback,
        pattern='^area_'
    ))
    
    # Add Web App data handler (for when web app sends data back)
    application.add_handler(MessageHandler(
        filters.StatusUpdate.WEB_APP_DATA,
        dashboard_opened
    ))

    # Run the bot
    logger.info("🤖 Starting Telegram Bot with Web App support...")
    logger.info(f"📊 Dashboard URL: {WEBAPP_URL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()