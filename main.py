#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

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
    if context.bot_data.get('notes') == None:
        context.bot_data['notes'] = {}
    context.bot_data['notes'][str(len(context.bot_data['notes'])+1)] = {context.user_data['current_note_name']: update.message.text}
    return _to_main_menu(update, context, 'Заметка добавлена')

def list_notes(update, context):
    notes = context.bot_data.get('notes')
    if not notes:
        return _to_main_menu(update, context, 'Заметок нет')
    
    notes_list = ""
    for i in range(1, len(notes.items()) + 1):
        notes_list += f"{i}. {list(notes[str(i)].keys())[0]}\n"
    
    return _to_main_menu(update, context, notes_list)

def show_note(update, context):
    notes = context.bot_data.get('notes')
    if not notes:
        return _to_main_menu(update, context, 'Такой заметки нет!')

    note_entry = notes.get(update.message.text)
    if not note_entry:
        return _to_main_menu(update, context, 'Такой заметки нет!')

    note = list(note_entry.values())[0]
    return _to_main_menu(update, context, note)

def _to_main_menu(update, context, text):
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=MAIN_MENU)
    return States.MAIN_MENU

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', start)],

        states = {
            States.MAIN_MENU: [
                CallbackQueryHandler(start_add, pattern=ADD_COMMAND),
                CallbackQueryHandler(list_notes, pattern=LIST_COMMAND),
                MessageHandler(Filters.regex(r"(\d)*"), show_note)
            ],
            States.ADD_NAME: [
                MessageHandler(Filters.text, add_name)
            ],
            States.ADD_CONTENT: [
                MessageHandler(Filters.text, add_content)
            ]
        },

        fallbacks = [
            CommandHandler('cancel', start)
        ]
    )

    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()