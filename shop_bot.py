import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8386547826:AAHo-Bn5fuXVnhDfl1ZuQ9Ss294HStpn10E"  # твой токен

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

products = [
    ("🍔 Бургер", 500),
    ("🍕 Пицца", 800),
    ("🥤 Кола", 150),
]

user_baskets = {}

@router.message(Command("start"))
async def start_handler(message: Message):
    builder = InlineKeyboardBuilder()
    for name, price in products:
        builder.button(text=f"{name} + ({price}₽)", callback_data=f"add_{name}_{price}")
    builder.button(text="🧾 Ваш заказ", callback_data="basket")
    builder.adjust(1)
    await message.answer("🍔 Меню:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("add_"))
async def add_to_basket(callback: CallbackQuery):
    _, name, price = callback.data.split("_", 2)
    price = int(price)
    user_id = callback.from_user.id
    if user_id not in user_baskets:
        user_baskets[user_id] = {}
    if name in user_baskets[user_id]:
        qty, _ = user_baskets[user_id][name]
        user_baskets[user_id][name] = (qty + 1, price)
    else:
        user_baskets[user_id][name] = (1, price)
    await callback.message.edit_text(f"✅ Добавлено: {name} (корзина обновлена)")
    await callback.answer()

@router.callback_query(F.data == "basket")
async def show_basket(callback: CallbackQuery):
    user_id = callback.from_user.id
    basket = user_baskets.get(user_id, {})
    if not basket:
        await callback.message.edit_text("🛒 Корзина пуста!")
    else:
        text = "🧾 Заказ:\n"
        total = 0
        for name, (qty, price) in basket.items():
            subtotal = qty * price
            text += f"{name}: {qty} × {price}₽ = {subtotal}₽\n"
            total += subtotal
        text += f"\n💰 Итого: {total}₽"
        await callback.message.edit_text(text)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
