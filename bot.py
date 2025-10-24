import logging
import asyncio
from typing import Optional, Dict
from dataclasses import dataclass
import uuid

try:
    import ssl
except ModuleNotFoundError as e:
    raise RuntimeError('Модуль ssl не найден. Убедитесь, что Python с поддержкой SSL установлен.') from e

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ORDERS_CHANNEL_ID = -1002993312286  # Канал для заказов
PRODUCTS_CHANNEL_ID = -1003175183010  # Канал для публикации товаров
ADMIN_ID = 1390211018  # Только этот ID может добавлять товары

bot = Bot(token=BOT_TOKEN)  # parse_mode больше не передается напрямую, используется при отправке сообщений
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

@dataclass
class Product:
    product_id: str
    photo: Optional[str]
    name: str
    description: str
    price: float
    quantity: int

@dataclass
class Order:
    order_id: str
    user_id: int
    product_id: str
    full_name: str
    phone: str
    address: str
    payment_method: str
    created_at: datetime

PRODUCTS: Dict[str, Product] = {}
ORDERS: Dict[str, Order] = {}

class ProductStates(StatesGroup):
    photo = State()
    name = State()
    description = State()
    price = State()
    quantity = State()
    confirm = State()

class OrderStates(StatesGroup):
    full_name = State()
    phone = State()
    address = State()
    payment_method = State()
    confirm = State()

# Проверка на владельца
def owner_only(func):
    async def wrapper(message: Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            await message.answer('У вас нет прав для добавления товаров.')
            return
        await func(message, state)
    return wrapper

# Остальные хендлеры и логика остаются без изменений, только все вызовы bot.send_message и bot.send_photo должны явно указывать parse_mode='HTML' при необходимости, например:
# await bot.send_message(chat_id=ORDERS_CHANNEL_ID, text=..., parse_mode='HTML')
# await bot.send_photo(chat_id=PRODUCTS_CHANNEL_ID, photo=photo, caption=..., reply_markup=kb, parse_mode='HTML')

# --- Пример исправления ---
# await bot.send_message(chat_id=ORDERS_CHANNEL_ID, text=f"<b>Новый заказ #{order.order_id}</b>\nТовар: {PRODUCTS[order.product_id].name}\nФИО: {order.full_name}\nТелефон: {order.phone}\nАдрес: {order.address}\nОплата: {order.payment_method}\nПокупатель: @{callback.from_user.username} (id: {order.user_id})\nВремя: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}", parse_mode='HTML')

async def main():
    logger.info('Бот запущен')
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(main())
    except RuntimeError:
        asyncio.run(main())

