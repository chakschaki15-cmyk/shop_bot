import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from openai import OpenAI
import logging

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

client = OpenAI(api_key=OPENAI_API_KEY)

STORE_WEBAPP_URL = "https://sweet-peony-5e1e76.netlify.app"

# ТОЧНЫЕ товары из твоего app (скрин)
real_products = {
    "🔒 VPN Франция": 500,
    "🌍 Доступ нет": 1500,
    "🟡 Лот премиум": 5000,
    "🔓 VPN нет": 500,
    "💎 NFT коллекция": 900,
    "👑 Merch премиум": 2000,
    "📱 Бот на сайте": 500,
    "₿ Крипто скам": 5000,
    "📱 Telegram бот": 5000
}

user_contexts = {}
delivery_data = {}

class DeliveryForm(StatesGroup):
    name = State()
    address = State()
    phone = State()

@router.message(Command("start"))
async def start_handler(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Магазин (все лоты)", web_app=WebAppInfo(url=STORE_WEBAPP_URL))
    builder.button(text="Совет по лотам", callback_data="advice")
    builder.adjust(1)
    
    products_list = "\n".join([f"- {name}: {price}р" for name, price in real_products.items()])
    
    system_prompt = f"""Адекватный пацан с района. Простой русский, без понтов/матов. Лёгкий зумер: бро, норм, го.
    
    Товары из магазина {STORE_WEBAPP_URL} (реальные цены):
    {products_list}
    
    Советуй по делу: 'VPN Франция за 500р норм для анонима. NFT коллекция 900р — если в крипту.'
    Всегда веди в магазин 🛒: 'Зайди, актуальные цены там.'
    После покупки — доставка (цифровой товар на email).
    Дружелюбно, коротко, как кореш."""
    
    user_contexts[message.from_user.id] = [{"role": "system", "content": system_prompt}]
    
    await message.answer(
        f"Здарова, бро! 😊\nВсе лоты в магазине: VPN от 500р, NFT 900р, крипта до 5000р.\n"
        "Что интересует? Совет дам или сразу в магазин.",
        reply_markup=builder.as_markup()
    )

@router.message(F.text)
async def ai_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if message.text.lower() in ['доставка', 'адрес', 'отправить', 'доставить']:
        await message.answer("Ок, доставка цифрового товара. Имя?")
        await state.set_state(DeliveryForm.name)
        return
    
    if user_id not in user_contexts:
        user_contexts[user_id] = []
    
    user_contexts[user_id].append({"role": "user", "content": message.text})
    
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=user_contexts[user_id][-10:])
        ai_reply = response.choices[0].message.content
        user_contexts[user_id].append({"role": "assistant", "content": ai_reply})
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🛒 Магазин", web_app=WebAppInfo(url=STORE_WEBAPP_URL))
        builder.button(text="Доставка", callback_data="delivery")
        builder.adjust(1)
        
        await message.answer(ai_reply, reply_markup=builder.as_markup())
    except:
        await message.answer("Чутка подвис. Клик магазин — там полный список.")

# Доставка (цифровой товар)
@router.message(DeliveryForm.name)
async def name_step(message: Message, state: FSMContext):
    delivery_data[message.from_user.id] = {'name': message.text}
    await message.answer("Адрес email для ссылки?")
    await state.set_state(DeliveryForm.address)  # Email вместо адреса

@router.message(DeliveryForm.address)
async def email_step(message: Message, state: FSMContext):
    delivery_data[message.from_user.id]['email'] = message.text
    await message.answer("Телефон для связи?")
    await state.set_state(DeliveryForm.phone)

@router.message(DeliveryForm.phone)
async def phone_step(message: Message, state: FSMContext):
    user_id = message.from_user.id
    delivery_data[user_id]['phone'] = message.text
    
    admin_text = f"🆕 Заказ доставки:\n{str(delivery_data[user_id])}\nЛоты из {STORE_WEBAPP_URL}"
    if ADMIN_ID:
        await bot.send_message(ADMIN_ID, admin_text)
    
    await message.answer("Готово! Ссылка на товар прилетит на email скоро. Спасибо, бро! 👍")
    await state.clear()

@router.callback_query(F.data == "advice")
async def advice(callback: CallbackQuery):
    advice_text = (
        "Норм варианты:\n"
        "• VPN Франция 500р — для приватности\n"
        "• NFT коллекция 900р — если криптой интересуешься\n"
        "• Merch премиум 2000р — стильная тема\n"
        "Зайди в магазин, там сток и цены свежие."
    )
    await callback.message.edit_text(advice_text, reply_markup=InlineKeyboardBuilder().button(text="🛒 Магазин", web_app=WebAppInfo(url=STORE_WEBAPP_URL)).adjust(1).as_markup())
    await callback.answer()

@router.callback_query(F.data == "delivery")
async def delivery_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Доставка (ссылка на email). Имя?")
    await state.set_state(DeliveryForm.name)
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот с реальными лотами из app запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

