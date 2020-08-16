from enum import Enum
class States(Enum):
    MAIN_MENU = 1
    ADD_NAME = 2
    ADD_CONTENT = 3
    LIST = 4
    DELETE = 5
    START_EDIT = 6
    EDIT = 7

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dbservice import PostgresService
from note import Note

ADD_COMMAND = "/add"
LIST_COMMAND = "/list"
DELETE_COMMAND = "/delete"
EDIT_COMMAND = "/edit"

KEYBOARD = [
    [InlineKeyboardButton("Добавить заметку", callback_data=ADD_COMMAND)],
    [InlineKeyboardButton("Редактировать заметку", callback_data=EDIT_COMMAND)],
    [InlineKeyboardButton("Список заметок", callback_data=LIST_COMMAND)],
    [InlineKeyboardButton("Удалить заметку", callback_data=DELETE_COMMAND)]
]

MAIN_MENU = InlineKeyboardMarkup(KEYBOARD)

class NotesBot:
    def __init__(self, pg_settings):
        self.dbservice = PostgresService(pg_settings)

    def _to_main_menu(self, update, context, text):
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=MAIN_MENU)
        return States.MAIN_MENU
    
    def start(self, update, context):
        self._fetch_notes(context)
        return self._to_main_menu(update, context, 'Добро пожаловать в 48notes!')

    def begin_add(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название заметки")
        return States.ADD_NAME

    def add_name(self, update, context):
        context.user_data['current_note_name'] = update.message.text
        update.message.reply_text("Введите текст заметки")
        return States.ADD_CONTENT

    def add_content(self, update, context):
        title = context.user_data['current_note_name']
        content = update.message.text
        note = Note(title=title, content=content, id="")
        self.dbservice.add_note(note)
        self._fetch_notes(context)
        return self._to_main_menu(update, context, 'Заметка добавлена')

    def list_notes(self, update, context):
        notes_list = self._get_notes_list(context)
        if not notes_list:
            notes_list = "Заметок нет"
        return self._to_main_menu(update, context, notes_list)

    def begin_delete(self, update, context):
        self._ask_to_choose_note(update, context)
        return States.DELETE

    def delete_note(self, update, context):
        note_num = update.message.text
        if note_num == "0":
            return self._to_main_menu(update, context, "Удаление отменено.")
        notes_map = self._get_notes_map(context)
        note_id = notes_map.get(note_num)
        if not note_id:
            return self._to_main_menu(update, context, 'Такой заметки нет!')
        deleted = self.dbservice.delete_note(note_id)
        self._fetch_notes(context)
        if deleted:
            return self._to_main_menu(update, context, 'Заметка удалена.')
        else:
            return self._to_main_menu(update, context, 'Такой заметки нет!')

    def begin_edit(self, update, context):
        self._ask_to_choose_note(update, context)
        return States.START_EDIT

    def ask_for_new_content(self, update, context):
        note_num = update.message.text
        if note_num == "0":
            return self._to_main_menu(update, context, "Редактирование отменено.")
        notes_map = self._get_notes_map(context)
        note_id = notes_map.get(note_num)
        if not note_id:
            return self._to_main_menu(update, context, 'Такой заметки нет!')

        context.user_data['edit_note_id'] = note_id
        note = self.dbservice.get_note(note_id)
        context.bot.send_message(chat_id=update.effective_chat.id, text=note.content)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Введите новое содержание заметки')
        return States.EDIT

    def edit_note(self, update, context):
        note_id = context.user_data['edit_note_id']
        edited = self.dbservice.edit_note(note_id, update.message.text)
        if edited:
            return self._to_main_menu(update, context, 'Заметка отредактирована')
        else:
            return self._to_main_menu(update, context, 'Такой заметки нет!')

    def _ask_to_choose_note(self, update, context):
        notes_list = self._get_notes_list(context)
        if not notes_list:
            return self._to_main_menu(update, context, 'Заметок нет')
        context.bot.send_message(chat_id=update.effective_chat.id, text=notes_list)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите номер заметки, либо `0` для отмены")

    def _get_notes_list(self, context):
        notes = self._fetch_notes(context)
        notes_list = self._build_notes_list(notes)
        return notes_list

    def _fetch_notes(self, context):
        notes = self.dbservice.get_notes()
        context.user_data["notes_map"] = self._build_notes_mapping(notes)
        return notes

    def _get_notes_map(self, context):
        return context.user_data["notes_map"]

    def _build_notes_list(self, notes):
        notes_list = ""
        i = 1
        for note in notes:
            notes_list += f"{i}. {note.title}\n"
            i += 1
        return notes_list

    def _build_notes_mapping(self, notes):
        notes_dict = {}
        i = 1
        for note in notes:
            notes_dict[str(i)] = f"{note.id}"
            i += 1
        return notes_dict

    def show_note(self, update, context):
        notes_map = self._get_notes_map(context)
        note_id = notes_map[update.message.text]
        note = self.dbservice.get_note(note_id)
        if note:
            return self._to_main_menu(update, context, note.content)
        else:
            return self._to_main_menu(update, context, 'Такой заметки нет!')
    
    def get_states(self):
        return {
            States.MAIN_MENU: [
                CallbackQueryHandler(self.begin_add, pattern=ADD_COMMAND),
                CallbackQueryHandler(self.list_notes, pattern=LIST_COMMAND),
                CallbackQueryHandler(self.begin_delete, pattern=DELETE_COMMAND),
                CallbackQueryHandler(self.begin_edit, pattern=EDIT_COMMAND),
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
            ],
            States.START_EDIT: [
                MessageHandler(Filters.regex(r"(\d)*"), self.ask_for_new_content)
            ],
            States.EDIT: [
                MessageHandler(Filters.text, self.edit_note)
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
