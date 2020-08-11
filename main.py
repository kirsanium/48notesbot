import logging
import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# dotenv
from dotenv import load_dotenv
load_dotenv()

# env
WEB_TOKEN = os.getenv('WEB_TOKEN')
PORT = int(os.getenv('PORT', 5000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL').strip('/')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

from bot import NotesBot

def main():
    updater = Updater(WEB_TOKEN, use_context=True)
    dp = updater.dispatcher
    notes_bot = NotesBot()
    conv_handler = ConversationHandler(
        entry_points = notes_bot.get_entrypoints(),
        states = notes_bot.get_states(),
        fallbacks = notes_bot.get_fallbacks()
    )

    dp.add_handler(conv_handler)

    if ENVIRONMENT == 'dev':
        updater.start_polling()
    elif ENVIRONMENT == 'prod':
        updater.start_webhook(listen="0.0.0.0",
                            port=int(PORT),
                            url_path=WEB_TOKEN)
        updater.bot.setWebhook(f"{WEBHOOK_URL}/{WEB_TOKEN}")
    else:
        updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()