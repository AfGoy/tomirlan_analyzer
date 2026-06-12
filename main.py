import logging
from dotenv import load_dotenv
import os
import asyncio
from typing import Callable, Any

from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram.filters import Command

from analyser import analyse_messages

load_dotenv()
API_TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

chat_history = {}

HONEY_FILE = "honey_count.txt"


def load_honey() -> int:
    if os.path.exists(HONEY_FILE):
        with open(HONEY_FILE, "r") as f:
            return int(f.read().strip())
    return 0


def save_honey(count: int):
    with open(HONEY_FILE, "w") as f:
        f.write(str(count))


honey_count = load_honey()


class HistoryMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: types.Message,
        data: dict
    ) -> Any:
        if hasattr(event, 'text') and event.text and not event.text.startswith('/'):
            chat_id = event.chat.id
            if chat_id not in chat_history:
                chat_history[chat_id] = []
            chat_history[chat_id].append(event.text)
            logging.info(f"Saved to history: {event.text}, chat: {chat_id}")

            if len(chat_history[chat_id]) > 1000:
                chat_history[chat_id] = chat_history[chat_id][-1000:]

        return await handler(event, data)


dp.message.middleware(HistoryMiddleware())


@dp.message(Command('make_honey'))
async def make_honey(message: types.Message):
    global honey_count
    honey_count += 1
    save_honey(honey_count)
    await message.reply(f"*Tomirlan the analyzer have milked the bees*\n\n_Now we have {honey_count} units of honey_", parse_mode="Markdown")


@dp.message(Command('start', 'help'))
async def send_welcome(message: types.Message):
    await message.reply("Hi!\n*I'm Tomirlan the analyzer!*\n\nUse /analyse <number> to analyze the last <number> messages in this chat.", parse_mode="Markdown")


@dp.message(Command('analysis'))
async def analyse(message: types.Message):
    args = message.text.split()[1:]

    if not args:
        await message.reply("Использование: /analyse <число>")
        return

    try:
        count = int(args[0])
    except ValueError:
        await message.reply("Ошибка: аргумент должен быть целым числом")
        return

    chat_id = message.chat.id
    history = chat_history.get(chat_id, [])
    last_messages = history[-count:]

    if not last_messages:
        await message.reply("История сообщений пуста.")
        return

    await message.reply("Анализирую сообщения...")

    try:
        result = await asyncio.to_thread(analyse_messages, last_messages)
        await message.reply(result)
    except Exception as e:
        logging.error(f"Ошибка при анализе: {e}")
        await message.reply("Произошла ошибка при анализе. Попробуйте позже.")


@dp.message()
async def catch_all(message: types.Message):
    pass


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())