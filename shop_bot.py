import asyncio
import os
from openai import OpenAI  # ← ДОБАВЬ ЭТУ СТРОКУ!
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import logging

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# xAI GROK НАСТРОЙКА ← ИСПРАВЛЕНО
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

STORE_WEBAPP_URL = "https://sweet-peony-5e1e76.netlify.app"

real_products = {
    "🔒 VPN Франция": 500,
    "🌍 Доступ нет": 1500,
    "🟡 Лот премиум": 5000,
    "🔓 VPN нет": 500,
    "💎 NFT коллекция": 900,
    "👑 Merch премиум": 2000,
    "📱 Бот на сайте": 500,
    "₿ Крипто": 5000,
    "📱 Telegram бот": 5000
}

user_contexts = {}
delivery_data = {}

class DeliveryForm(StatesGroup):
    name = State()
    address = State()
    phone = State()

# ... (все @router функции ТАКИЕ ЖЕ до ai_handler) ...

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
        # ← ТУТ ГЛАВНОЕ ИЗМЕНЕНИЕ!
        response = client.chat.completions.create(
            model="grok-beta",  # xAI GROK!
            messages=user_contexts[user_id][-10:]
        )
        ai_reply = response.choices[0].message.content
        user_contexts[user_id].append({"role": "assistant", "content": ai_reply})
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🛒 Магазин", web_app=WebAppInfo(url=STORE_WEBAPP_URL))
        builder.button(text="Доставка", callback_data="delivery")
        builder.adjust(1)
        
        await message.answer(ai_reply, reply_markup=builder.as_markup())
    except Exception as e:
        await message.answer(f"Подвис ({e}). Кликни магазин, бро.")

# ... (все остальные функции БЕЗ ИЗМЕНЕНИЙ!) ...
