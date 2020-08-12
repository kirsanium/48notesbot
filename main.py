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

from bot import NotesBot
from dbservice import PostgresSettings

def main():
    pg_settings = PostgresSettings(
        os.getenv('DBNAME'),
        os.getenv('DBUSER'),
        os.getenv('DBPASSWORD'),
        os.getenv('DBPORT')
    )

    web_token = os.getenv('WEB_TOKEN')
    web_port = int(os.getenv('PORT', 5000))
    webhook_url = os.getenv('WEBHOOK_URL').strip('/')
    
    updater = Updater(web_token, use_context=True)
    dp = updater.dispatcher
    notes_bot = NotesBot(pg_settings)
    conv_handler = ConversationHandler(
        entry_points = notes_bot.get_entrypoints(),
        states = notes_bot.get_states(),
        fallbacks = notes_bot.get_fallbacks()
    )

    dp.add_handler(conv_handler)

    environment = os.getenv('ENVIRONMENT', 'dev')

    if environment == 'dev':
        updater.start_polling()
    elif environment == 'prod':
        updater.start_webhook(listen="0.0.0.0",
                            port=int(web_port),
                            url_path=web_token)
        updater.bot.setWebhook(f"{webhook_url}/{web_token}")
    else:
        updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()