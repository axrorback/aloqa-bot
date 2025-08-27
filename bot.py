import logging
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
import os
from dotenv import load_dotenv
API_TOKEN = os.getenv('TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')  #  Telegram ID ni yuklaymiz .envdan

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")  # aiogram 3.7.x dan shunday beriladi bot obyekti beriladi kop hollarda unutyapmanda negadir shuni esdan chiqmasin keyingigi safar hopmi?!
)
dp = Dispatcher()

with open("locales.json", "r", encoding="utf-8") as f:
    LOCALES = json.load(f)

with open("about.json", "r", encoding="utf-8") as f:
    ABOUT = json.load(f)

user_lang = {}   # {user_id: "uz"}
user_modes = {}  # {user_id: "anonim" | "ochiq"}
user_message_map = {}  # xabarlar


# Til tanlash menyusi
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 Uzbek"), KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English"), KeyboardButton(text="🇹🇷 Türkçe")],
            [KeyboardButton(text="🇸🇦 العربية")]
        ],
        resize_keyboard=True
    )
    await message.answer("Tilni tanlang / Choose a language:", reply_markup=kb)


@dp.message(lambda m: m.text in ["🇺🇿 Uzbek", "🇷🇺 Русский", "🇬🇧 English", "🇹🇷 Türkçe", "🇸🇦 العربية"])
async def set_language(message: Message):
    langs = {
        "🇺🇿 Uzbek": "uz",
        "🇷🇺 Русский": "ru",
        "🇬🇧 English": "en",
        "🇹🇷 Türkçe": "tr",
        "🇸🇦 العربية": "ar"
    }
    user_lang[message.from_user.id] = langs[message.text]
    lang = user_lang[message.from_user.id]

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LOCALES[lang]["anon"]), KeyboardButton(text=LOCALES[lang]["open"])],
            [KeyboardButton(text=LOCALES[lang]["about"])]
        ],
        resize_keyboard=True
    )
    await message.answer(LOCALES[lang]["choose_mode"], reply_markup=kb)


# Foydalanuvchi habar → admin’ga uzatish
@dp.message(lambda m: m.text and not m.reply_to_message)
async def set_mode_or_about(message: Message):
    lang = user_lang.get(message.from_user.id, "uz")

    if message.text == LOCALES[lang]["anon"]:
        user_modes[message.from_user.id] = "anonim"
        await message.answer(LOCALES[lang]["anon_chosen"])

    elif message.text == LOCALES[lang]["open"]:
        user_modes[message.from_user.id] = "ochiq"
        await message.answer(LOCALES[lang]["open_chosen"])

    elif message.text == LOCALES[lang]["about"]:
        photo = FSInputFile("about.jpeg")
        caption = f"👤 <b>{ABOUT[lang]['name']}</b>\n\n{ABOUT[lang]['bio']}"
        await message.answer_photo(photo=photo, caption=caption)

    else:
        mode = user_modes.get(message.from_user.id, "anonim")

        if mode == "anonim":
            text = f"📩 <b>Anonim xabar</b>:\n\n{message.text}"
        else:
            text = (f"📩 <b>Ochiq xabar</b>:\n\n{message.text}\n\n"
                    f"👤 <b>Ism:</b> {message.from_user.full_name}\n"
                    f"🔗 @{message.from_user.username if message.from_user.username else 'yo‘q'}\n"
                    f"🆔 {message.from_user.id}")

        sent = await bot.send_message(ADMIN_ID, text)

        user_message_map[sent.message_id] = message.from_user.id
        user_message_map[message.message_id] = message.from_user.id

        user_message_map[message.from_user.id] = message.message_id

        await message.answer("✅ Xabaringiz admin’ga yuborildi. Tez orada javob olasiz.")


@dp.message(lambda m: m.chat.id == ADMIN_ID and m.reply_to_message)
async def reply_to_user(message: Message):
    reply_msg_id = message.reply_to_message.message_id
    if reply_msg_id in user_message_map:
        user_id = user_message_map[reply_msg_id]

        user_original_msg_id = user_message_map.get(user_id)

        if user_original_msg_id:
            await bot.send_message(
                user_id,
                f"📨 Admin:\n\n{message.text}",
                reply_to_message_id=user_original_msg_id
            )
        else:
            await bot.send_message(user_id, f"📨 Admin:\n\n{message.text}")

        await message.answer("✅ Javob foydalanuvchiga yuborildi.")
    else:
        await message.answer("❗ Bu xabar kimga tegishli ekanini topib bo‘lmadi.")




async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
