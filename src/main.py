import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message
from aiogram.utils.formatting import Text

from .message_formater import message_generator
from .search_papers import PapersSurf, article_analyser

logger = logging.getLogger(__name__)

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
    logger.info(f"Request user id: {message.from_user.id}")
    if message.from_user.id in rika_ids:
        logger.info("Sending Rika chan to you!")
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
    try:
        articles = article_explorer.search_articles(1200, 400)
        parsed_articles = article_analyser(articles=articles)
        answer = message_generator(parsed_articles, message)
    except Exception as e:
        logger.exception(e, stack_info=True)
        answer = Text("I had an error (")
    await message.answer(**answer.as_kwargs())


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    logger.info("Started")
    asyncio.run(main())
    logger.info("Finished")
