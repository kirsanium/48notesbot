from enum import Enum
class States(Enum):
    MAIN_MENU = 1
    ADD_NAME = 2
    ADD_CONTENT = 3
    LIST = 4
    DELETE = 5

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

ADD_COMMAND = "/add"
LIST_COMMAND = "/list"
DELETE_COMMAND = "/delete"

KEYBOARD = [
    [InlineKeyboardButton("Добавить заметку", callback_data=ADD_COMMAND)],
    [InlineKeyboardButton("Список заметок", callback_data=LIST_COMMAND)],
    [InlineKeyboardButton("Удалить заметку", callback_data=DELETE_COMMAND)]
]

MAIN_MENU = InlineKeyboardMarkup(KEYBOARD)

class NotesBot:
    def _to_main_menu(self, update, context, text):
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=MAIN_MENU)
        return States.MAIN_MENU
    
    def start(self, update, context):
        if context.bot_data.get('notes') is None:
            context.bot_data['notes'] = {}
        return self._to_main_menu(update, context, 'Добро пожаловать в 48notes!')

    def begin_add(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название заметки")
        return States.ADD_NAME

    def add_name(self, update, context):
        context.user_data['current_note_name'] = update.message.text
        update.message.reply_text("Введите текст заметки")
        return States.ADD_CONTENT

    def add_content(self, update, context):
        try:
            new_note_number = len(context.bot_data['notes'])+1
            context.bot_data['notes'][str(new_note_number)] = {context.user_data['current_note_name']: update.message.text}
            return self._to_main_menu(update, context, 'Заметка добавлена')
        except KeyError:
            return self._to_main_menu(update, context, 'Ошибка при добавлении заметки')

    def list_notes(self, update, context):
        try:
            notes = context.bot_data['notes']
            notes_list = self._build_notes_list(notes)
            return self._to_main_menu(update, context, notes_list)
        except KeyError:
            return self._to_main_menu(update, context, 'Заметок нет')

    def begin_delete(self, update, context):
        try:
            notes = context.bot_data['notes']
            context.bot.send_message(chat_id=update.effective_chat.id, text=self._build_notes_list(notes))
            context.bot.send_message(chat_id=update.effective_chat.id, text="Введите номер заметки, либо `0` для отмены")
            return States.DELETE
        except KeyError:
            return self._to_main_menu(update, context, 'Заметок нет')

    def delete_note(self, update, context):
        key_to_remove = update.message.text
        if key_to_remove == "0":
            return self._to_main_menu(update, context, "Удаление отменено.")
        try:
            del context.bot_data['notes'][key_to_remove]
            self.fix_notes_dict(context, key_to_remove)
            return self._to_main_menu(update, context, 'Заметка удалена.')
        except KeyError:
            return self._to_main_menu(update, context, 'Такой заметки нет!')

    def fix_notes_dict(self, context, removed_key):
        notes = context.bot_data['notes']
        items_len = len(notes.items())
        if items_len == 0:
            return
        upper_bound = items_len + 1
        for i in range(int(removed_key), upper_bound):
            context.bot_data['notes'][str(i)] = context.bot_data['notes'][str(i+1)]
        del context.bot_data['notes'][str(upper_bound)]

    def _build_notes_list(self, notes):
        notes_list = ""
        for i in range(1, len(notes.items()) + 1):
            notes_list += f"{i}. {list(notes[str(i)].keys())[0]}\n"

        if notes_list == "":
            notes_list = "Заметок нет"
        return notes_list

    def show_note(self, update, context):
        try:
            note = list(context.bot_data['notes'][update.message.text].values())[0]
            return self._to_main_menu(update, context, note)
        except KeyError:
            return self._to_main_menu(update, context, 'Такой заметки нет!')
    
    def get_states(self):
        return {
            States.MAIN_MENU: [
                CallbackQueryHandler(self.begin_add, pattern=ADD_COMMAND),
                CallbackQueryHandler(self.list_notes, pattern=LIST_COMMAND),
                CallbackQueryHandler(self.begin_delete, pattern=DELETE_COMMAND),
                MessageHandler(Filters.regex(r"(\d)*"), self.show_note)
            ],
            States.ADD_NAME: [
                MessageHandler(Filters.text, self.add_name)
            ],
            States.ADD_CONTENT: [
                MessageHandler(Filters.text, self.add_content)
            ],
            States.DELETE: [
                MessageHandler(Filters.regex(r"(\d)*"), self.delete_note)
            ]
        }

    def get_entrypoints(self):
        return [CommandHandler('start', self.start)]

    def get_fallbacks(self):
        return [CommandHandler('cancel', self.start)]

    def get_all_handlers(self):
        return [
            ConversationHandler(
                entry_points = self.get_entrypoints(),
                states = self.get_states(),
                fallbacks = self.get_fallbacks()
            )
        ]
