import logging
import asyncio
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ------------------- Настройки -------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')  # Установите токен через переменные окружения
ORDERS_CHANNEL_ID = -1002993312286      # Канал для заказов
PRODUCTS_CHANNEL_ID = -1003175183010    # Канал для публикации товаров
ADMIN_ID = 1390211018                   # Только этот ID может добавлять товары

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ------------------- Данные -------------------
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

# ------------------- FSM состояния -------------------
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

# ------------------- Проверка владельца -------------------
def owner_only(func):
    async def wrapper(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            await message.answer('У вас нет прав для добавления товаров.')
            return
        await func(message, state)
    return wrapper

# ------------------- Хендлеры -------------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Бот запущен ✅")

# Пример отправки уведомления о заказе
async def send_order_notification(order: Order):
    product = PRODUCTS.get(order.product_id)
    if not product:
        return
    text = (
        f"<b>Новый заказ #{order.order_id}</b>\n"
        f"Товар: {product.name}\n"
        f"ФИО: {order.full_name}\n"
        f"Телефон: {order.phone}\n"
        f"Адрес: {order.address}\n"
        f"Оплата: {order.payment_method}\n"
        f"Покупатель: @{order.user_id}\n"
        f"Время: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await bot.send_message(chat_id=ORDERS_CHANNEL_ID, text=text, parse_mode='HTML')

# ------------------- Основной запуск бота -------------------
async def main():
    logger.info("Бот запущен")
    # skip_updates=True пропускает старые сообщения и предотвращает ConflictError
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Если цикл уже есть (например, IDE), запускаем как задачу
        loop.create_task(main())
    else:
        # Иначе запускаем стандартно
        asyncio.run(main())


