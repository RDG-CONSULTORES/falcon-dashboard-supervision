import os
import logging
from telegram import Update, WebAppInfo, MenuButtonWebApp, ReplyKeyboardRemove
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

¡Listo para tu presentación! 🚀
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text message - redirect to dashboard."""
    await update.message.reply_text(
        "📊 Usa el botón *'📊 Abrir Dashboard Analytics'* en el menú inferior para acceder al dashboard.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )

async def post_init(application: Application) -> None:
    """Configure the Web App menu button after bot initialization."""
    bot = application.bot
    
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    logger.info("🤖 Starting Telegram Bot with Web App support...")
    logger.info(f"📊 Dashboard URL: {WEBAPP_URL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()