from googletrans import Translator
from telebot.async_telebot import AsyncTeleBot
import asyncio
from telebot.types import InlineQuery, InputTextMessageContent
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types
import sqlite3
import os

bot = AsyncTeleBot("7058120983:AAGtoU5v4aYb4Zq-2BIq4lPhd5BzrnYesas", parse_mode=None)
languages = []
def get_language_code(input_lang):
    conn = sqlite3.connect('languages.db')
    c = conn.cursor()

    c.execute("SELECT code FROM languages WHERE code = ?", (input_lang,))
    result = c.fetchone()
    if result:
        conn.close()
        return result[0]

    c.execute("SELECT code FROM languages WHERE name LIKE ?", ('%' + input_lang + '%',))
    result = c.fetchone()
    if result:
        conn.close()
        return result[0]

    conn.close()
    return None

@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id, text=f'Привет {message.from_user.first_name}')
    await asyncio.sleep(0.5)
    await bot.send_message(message.chat.id, text=f'Это бот-переводчик. Введите язык на английском, с которого нужно перевести текст (например, ru, russian):')

@bot.message_handler(commands=['help'])
async def send_welcome(message):
    await bot.send_message(message.chat.id, '''/start - перезапустить бота
/help - помощь
/languages - список доступных языков''')

@bot.message_handler(commands=['languages'])
async def show_languages(message):
    conn = sqlite3.connect('languages.db')
    c = conn.cursor()
    c.execute("SELECT name FROM languages")
    result = c.fetchall()
    languages = "\n".join([row[0] for row in result])
    conn.close()

    with open("languages.txt", "w") as file:
        file.write(languages)

    with open("languages.txt", "rb") as file:
        await bot.send_message(message.chat.id, 'Вот все доступные языки:')
        await bot.send_document(message.chat.id, file)

    os.remove("languages.txt")


@bot.message_handler(func=lambda message: True)
async def get_from_language(message):
    global languages
    if len(languages) == 0:
        language_code = get_language_code(message.text.lower())
        if language_code:
            languages.append(language_code)
            await bot.send_message(message.chat.id, "Введите язык, на который нужно перевести (например, en):")
        else:
            await bot.send_message(message.chat.id, "Язык не найден. Пожалуйста, попробуйте снова.")
    elif len(languages) == 1:
        language_code = get_language_code(message.text.lower())
        if language_code:
            languages.append(language_code)
            await bot.send_message(message.chat.id, "Теперь введите текст для перевода:")
        else:
            await bot.send_message(message.chat.id, "Язык не найден. Пожалуйста, попробуйте снова.")
    else:
        translator = Translator()
        send = translator.translate(message.text, src=languages[0], dest=languages[1])
        await bot.send_message(message.chat.id, f"Переведенный текст: {send.text}")
        await asyncio.sleep(0.5)
        await bot.send_message(message.chat.id,
                               text=f'Хотите еще что-то перевести?',
                               reply_markup=create_translation_keyboard())
        languages = []

def create_translation_keyboard():
    keyboard = InlineKeyboardMarkup()
    translate_button = InlineKeyboardButton(text="Перевести текст еще", callback_data="translate_more")
    keyboard.add(translate_button)
    return keyboard

@bot.callback_query_handler(func=lambda call: call.data == "translate_more")
async def translate_more(call):
    await bot.send_message(call.message.chat.id, "Введите язык, с которого нужно перевести текст (например, ru, russian):")



@bot.message_handler(content_types=['photo'])
async def handle_image(message):
    translator = Translator()
    chat_id = message.chat.id
    photo = message.photo[-1].file_id
    caption = message.caption

    lang = translator.detect(caption)
    lang = lang.lang

    if lang == 'ru':
        send = translator.translate(caption)

    else:
        send = translator.translate(caption, dest='ru')
    await bot.send_photo(chat_id, photo, caption=send.text)




@bot.inline_handler(lambda query: True)
async def inline_query(query):
    results = []
    translator = Translator()
    text = query.query.strip()

    if not text:
        return

    lang = translator.detect(text)
    lang = lang.lang

    if lang == 'ru':
        send = translator.translate(text)
        results.append(types.InlineQueryResultArticle(
            id='1', title=send.text, input_message_content=types.InputTextMessageContent(
                message_text=send.text)))

    else:
        send = translator.translate(text, dest='ru')
        results.append(types.InlineQueryResultArticle(
            id='1', title=send.text, input_message_content=types.InputTextMessageContent(
                message_text=send.text)))

    await bot.answer_inline_query(query.id, results)

asyncio.run(bot.infinity_polling())