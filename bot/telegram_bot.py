import os
import logging
from telegram import Update, WebAppInfo, MenuButtonWebApp, ReplyKeyboardRemove, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://falcon-dashboard-supervision.onrender.com')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a simple welcome message - only Web App button available."""
    user_name = update.effective_user.first_name
    
    welcome_message = f"""
¡Hola *{user_name}*! 👋

📊 *Dashboard Supervisión Operativa*

Usa el botón *"📊 Abrir Dashboard Analytics"* en el menú inferior para acceder al dashboard con datos reales.

✨ *Funciones:*
• Mapas interactivos de sucursales
• KPIs y métricas en tiempo real  
• 29 indicadores por áreas
• Datos reales de PostgreSQL

💡 *Comandos disponibles:*
• `/clean` - Eliminar botones del teclado

¡Listo para tu presentación! 🚀
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True)
    )

async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Eliminar completamente los botones del teclado."""
    # Force remove keyboard with remove_keyboard=True
    await update.message.reply_text(
        "🧹 *Eliminando botones del teclado...*",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True)
    )
    
    # Send confirmation message
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✅ *Botones eliminados completamente*\n\nSi aún ves botones abajo, cierra y vuelve a abrir el chat del bot.\n\nSolo disponible: botón azul *'📊 Abrir Dashboard Analytics'*",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text message - redirect to dashboard."""
    await update.message.reply_text(
        "📊 Usa el botón *'📊 Abrir Dashboard Analytics'* en el menú inferior para acceder al dashboard.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True)
    )

async def post_init(application: Application) -> None:
    """Configure the Web App menu button and bot commands after bot initialization."""
    bot = application.bot
    
    # Configure bot commands list
    commands = [
        BotCommand("start", "Iniciar el bot y acceder al dashboard"),
        BotCommand("clean", "Eliminar botones del teclado completamente")
    ]
    
    try:
        await bot.set_my_commands(commands)
        logger.info("✅ Comandos del bot configurados")
    except Exception as e:
        logger.error(f"Error configurando comandos: {e}")
    
    # Configure the menu button to open the Web App
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

    # Add only essential handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clean", clean))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    logger.info("🤖 Starting Telegram Bot with Web App support...")
    logger.info(f"📊 Dashboard URL: {WEBAPP_URL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()