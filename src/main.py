import asyncio
import logging
import sys
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import FSInputFile
from .search_papers import PapersSurf, article_analyser
from .message_formater import message_generator

BOT_TOKEN = os.getenv("BOT_TOKEN")
NCBI_TOKEN = os.getenv("NCBI_TOKEN")

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def paper_search(message: Message) -> None:
    rika_ids = (597421569, 349895366, 296931944)
    print(f"Request user id: {message.from_user.id}")
    if message.from_user.id in rika_ids:
        print("Sending Rika chan to you!")
        file_path = Path(__file__)
        rika_gif = FSInputFile(
            file_path.parent / ".." / "assets" / "rika_for_denis.mp4"
        )
        await message.answer_animation(rika_gif)
    tmp_dir = Path("./tmp/")
    if not tmp_dir.exists():
        tmp_dir.mkdir()
    article_explorer = PapersSurf(
        tmp_dir=tmp_dir,
        query=message.text,
        since=30,
    )
    articles = article_explorer.search_articles(1200, 400)
    parsed_articles = article_analyser(articles=articles)
    answer = message_generator(parsed_articles, message)
    await message.answer(**answer.as_kwargs())


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
