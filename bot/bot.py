from decouple import config
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

TOKEN = config("TOKEN")      # 👈 теперь так
MY_ID = config("MY_ID", cast=int)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Главное меню ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍕 Пицца"), KeyboardButton(text="🍣 Суши")],
        [KeyboardButton(text="🛒 Сделать заказ")]
    ],
    resize_keyboard=True
)

# --- Пицца ---
pizza_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Маргарита"), KeyboardButton(text="Гавайская")],
        [KeyboardButton(text="Охотничья")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

# --- Суши ---
sushi_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Филадельфия"), KeyboardButton(text="Калифорния")],
        [KeyboardButton(text="Дракон")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

# --- Старт ---
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Добро пожаловать! Выберите категорию:", reply_markup=main_kb)

# --- Переходы ---
@dp.message(F.text == "🍕 Пицца")
async def pizza_menu(message: Message):
    await message.answer("Выберите пиццу:", reply_markup=pizza_kb)

@dp.message(F.text == "🍣 Суши")
async def sushi_menu(message: Message):
    await message.answer("Выберите суши:", reply_markup=sushi_kb)

@dp.message(F.text == "⬅️ Назад")
async def back_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_kb)

# --- Пиццы ---
@dp.message(F.text == "Маргарита")
async def margarita(message: Message):
    await message.answer("🍕 Маргарита\nТоматный соус, сыр моцарелла\nЦена: 120 грн")

@dp.message(F.text == "Гавайская")
async def hawaiian(message: Message):
    await message.answer("🍕 Гавайская\nКурица, ананас, сыр\nЦена: 150 грн")

@dp.message(F.text == "Охотничья")
async def hunting(message: Message):
    await message.answer("🍕 Охотничья\nКолбаски, бекон, сыр\nЦена: 170 грн")

# --- Суши ---
@dp.message(F.text == "Филадельфия")
async def philadelphia(message: Message):
    await message.answer("🍣 Филадельфия\nЛосось, сливочный сыр\nЦена: 180 грн")

@dp.message(F.text == "Калифорния")
async def california(message: Message):
    await message.answer("🍣 Калифорния\nКраб, авокадо\nЦена: 160 грн")

@dp.message(F.text == "Дракон")
async def dragon(message: Message):
    await message.answer("🍣 Дракон\nУгорь, соус унаги\nЦена: 200 грн")

# --- Заказ ---
@dp.message(F.text == "🛒 Сделать заказ")
async def order(message: Message):
    await message.answer("Напишите ваш заказ и номер телефона 📞")

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())