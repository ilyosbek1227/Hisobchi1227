
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

client = MongoClient(MONGO_URL)
db = client['finance_bot']
collection = db['records']

logging.basicConfig(level=logging.INFO)

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("➕ Daromat", "➖ Harajat").add("📊 Hisobot")

income_menu = ReplyKeyboardMarkup(resize_keyboard=True)
income_menu.add("Maosh", "Uydan", "Qo'shimcha").add("🔙 Orqaga")

expense_menu = ReplyKeyboardMarkup(resize_keyboard=True)
expense_menu.add("Yo'l Kiro", "Ovqatlanish", "Ilm-Fan")
expense_menu.add("Uy uchun", "Kiyinish", "Shaxsiy").add("🔙 Orqaga")

report_menu = ReplyKeyboardMarkup(resize_keyboard=True)
report_menu.add("Kunlik", "Oylik", "Yillik").add("🔙 Orqaga")

user_state = {}

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=main_menu)

@dp.message_handler(lambda m: m.text in ["➕ Daromat", "➖ Harajat", "📊 Hisobot"])
async def main_menu_handler(message: types.Message):
    user_id = message.from_user.id
    if message.text == "➕ Daromat":
        user_state[user_id] = {"type": "income"}
        await message.answer("Daromat turini tanlang:", reply_markup=income_menu)
    elif message.text == "➖ Harajat":
        user_state[user_id] = {"type": "expense"}
        await message.answer("Harajat turini tanlang:", reply_markup=expense_menu)
    elif message.text == "📊 Hisobot":
        await message.answer("Hisobot turini tanlang:", reply_markup=report_menu)

@dp.message_handler(lambda m: m.text in ["Maosh", "Uydan", "Qo'shimcha", "Yo'l Kiro", "Ovqatlanish", "Ilm-Fan", "Uy uchun", "Kiyinish", "Shaxsiy"])
async def category_handler(message: types.Message):
    user_id = message.from_user.id
    category = message.text
    user_state[user_id]["category"] = category
    await message.answer("Miqdorni kiriting (raqam):")

@dp.message_handler(lambda m: m.text.isdigit())
async def amount_handler(message: types.Message):
    user_id = message.from_user.id
    amount = int(message.text)
    user_state[user_id]["amount"] = amount
    await message.answer("Izoh (ixtiyoriy, yo'q bo'lsa 'yoq' deb yozing):")

@dp.message_handler()
async def note_handler(message: types.Message):
    user_id = message.from_user.id
    if message.text == "🔙 Orqaga":
        await message.answer("Asosiy menyu:", reply_markup=main_menu)
        return

    state = user_state.get(user_id)
    if not state:
        await message.answer("Iltimos, menyudan boshlang:", reply_markup=main_menu)
        return

    note = message.text if message.text.lower() != 'yoq' else ""
    record = {
        "user_id": user_id,
        "type": state["type"],
        "category": state["category"],
        "amount": state["amount"],
        "note": note,
        "date": datetime.now()
    }
    collection.insert_one(record)
    user_state.pop(user_id)
    await message.answer("Ma'lumot saqlandi! ✅", reply_markup=main_menu)

@dp.message_handler(lambda m: m.text in ["Kunlik", "Oylik", "Yillik"])
async def report_handler(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now()
    query = {"user_id": user_id}

    if message.text == "Kunlik":
        query["date"] = {"$gte": datetime(now.year, now.month, now.day)}
    elif message.text == "Oylik":
        query["date"] = {"$gte": datetime(now.year, now.month, 1)}
    elif message.text == "Yillik":
        query["date"] = {"$gte": datetime(now.year, 1, 1)}

    records = list(collection.find(query))
    income = sum(r['amount'] for r in records if r['type'] == 'income')
    expense = sum(r['amount'] for r in records if r['type'] == 'expense')
    balance = income - expense

    text = f"📅 {message.text} hisobot:\n\n" \
           f"Daromad: {income} so'm\n" \
           f"Harajat: {expense} so'm\n" \
           f"Qoldiq: {balance} so'm"
    await message.answer(text, reply_markup=main_menu)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
