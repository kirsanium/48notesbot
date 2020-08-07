import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

TOKEN = '1281871705:AAF6UCdQ0h-j_JI-mvljMsFJzPzmrVEocsM'

ADD_COMMAND = "/add"
LIST_COMMAND = "/list"
DELETE_COMMAND = "/delete"

KEYBOARD = [
    [InlineKeyboardButton("Добавить заметку", callback_data=ADD_COMMAND)],
    [InlineKeyboardButton("Список заметок", callback_data=LIST_COMMAND)],
    [InlineKeyboardButton("Удалить заметку", callback_data=DELETE_COMMAND)]
]

MAIN_MENU = InlineKeyboardMarkup(KEYBOARD)

from enum import Enum
class States(Enum):
    MAIN_MENU = 1
    ADD_NAME = 2
    ADD_CONTENT = 3
    LIST = 4
    DELETE = 5

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    return _to_main_menu(update, context, 'Добро пожаловать в 48notes!')

def start_add(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название заметки")
    return States.ADD_NAME

def add_name(update, context):
    context.user_data['current_note_name'] = update.message.text
    update.message.reply_text("Введите текст заметки")
    return States.ADD_CONTENT

def add_content(update, context):
    if context.bot_data.get('notes') is None:
        context.bot_data['notes'] = {}
    context.bot_data['notes'][str(len(context.bot_data['notes'])+1)] = {context.user_data['current_note_name']: update.message.text}
    return _to_main_menu(update, context, 'Заметка добавлена')

def list_notes(update, context):
    try:
        notes = context.bot_data['notes']
        notes_list = _build_notes_list(notes)
        return _to_main_menu(update, context, notes_list)
    except KeyError:
        return _to_main_menu(update, context, 'Заметок нет')

def start_delete(update, context):
    try:
        notes = context.bot_data['notes']
        context.bot.send_message(chat_id=update.effective_chat.id, text=_build_notes_list(notes))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите номер заметки, либо `0` для отмены")
        return States.DELETE
    except KeyError:
        return _to_main_menu(update, context, 'Заметок нет')

def delete_note(update, context):
    key_to_remove = update.message.text
    if key_to_remove == "0":
        return _to_main_menu(update, context, "Удаление отменено.")
    try:
        del context.bot_data['notes'][key_to_remove]
        fix_notes_dict(context, key_to_remove)
        return _to_main_menu(update, context, 'Заметка удалена.')
    except KeyError:
        return _to_main_menu(update, context, 'Такой заметки нет!')

def fix_notes_dict(context, removed_key):
    notes = context.bot_data['notes']
    upper_bound = len(notes.items()) + 1
    for i in range(int(removed_key), upper_bound):
        context.bot_data['notes'][str(i)] = context.bot_data['notes'][str(i+1)]
    del context.bot_data['notes'][str(upper_bound)]

def _build_notes_list(notes):
    notes_list = ""
    for i in range(1, len(notes.items()) + 1):
        notes_list += f"{i}. {list(notes[str(i)].keys())[0]}\n"

    if notes_list == "":
        notes_list = "Заметок нет"
    return notes_list

def show_note(update, context):
    try:
        note = list(context.bot_data['notes'][update.message.text].values())[0]
        return _to_main_menu(update, context, note)
    except KeyError:
        return _to_main_menu(update, context, 'Такой заметки нет!')

def _to_main_menu(update, context, text):
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=MAIN_MENU)
    return States.MAIN_MENU

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', start)],

        states = {
            States.MAIN_MENU: [
                CallbackQueryHandler(start_add, pattern=ADD_COMMAND),
                CallbackQueryHandler(list_notes, pattern=LIST_COMMAND),
                CallbackQueryHandler(start_delete, pattern=DELETE_COMMAND),
                MessageHandler(Filters.regex(r"(\d)*"), show_note)
            ],
            States.ADD_NAME: [
                MessageHandler(Filters.text, add_name)
            ],
            States.ADD_CONTENT: [
                MessageHandler(Filters.text, add_content)
            ],
            States.DELETE: [
                MessageHandler(Filters.regex(r"(\d)*"), delete_note)
            ]
        },

        fallbacks = [
            CommandHandler('cancel', start)
        ]
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()