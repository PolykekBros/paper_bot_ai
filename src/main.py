import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    FSInputFile,
    Message,
)
from aiogram.utils.formatting import (
    Bold,
    Italic,
    Text,
    TextLink,
    as_marked_list,
)

from .message_formater import message_generator
from .search_papers import PapersSurf, article_analyser

logger = logging.getLogger(__name__)


def get_env_tuple(var_name: str, default: tuple = ()) -> tuple:
    env_value = os.getenv(var_name)

    if env_value is None or env_value.strip() == "":
        return default
    else:
        return tuple(
            int(item.strip()) for item in env_value.split(",") if item.strip()
        )


BOT_TOKEN = os.getenv("BOT_TOKEN")
NCBI_TOKEN = os.getenv("NCBI_TOKEN")
RIKA_USERS = get_env_tuple("RIKA_USERS")

private_commands = [
    BotCommand(command="switch_rika", description="❤️ Turn Rika gifs on/off."),
    BotCommand(command="help", description="❓ Get help and info."),
]


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(
        private_commands,
        scope=BotCommandScopeDefault(),
    )
    logging.info("Default commands set.")


dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message(Command("switch_rika"))
async def command_rika_handler(message: Message) -> None:
    global RIKA_USERS
    if message.from_user.id in RIKA_USERS:
        RIKA_USERS = tuple(
            item for item in RIKA_USERS if item != message.from_user.id
        )
        print(RIKA_USERS)
        await message.answer("No Rika for you now!")
    else:
        RIKA_USERS += (message.from_user.id,)
        await message.answer("Nice choice!")


@dp.message(Command("help"))
async def command_help_handler(message: Message):
    answer = Text(
        "To run articles search send command formatted like this:\n",
        Italic("[<query>, <since>]"),
        " , where \n",
        as_marked_list(
            Text(
                Bold(Italic("query")),
                " - keywords for search. Learn more about its formattig ",
                TextLink(
                    "here",
                    url="https://github.com/jonatasgrosman/findpapers/tree/master?tab=readme-ov-file#search-query-construction",
                ),
            ),
            Text(
                Bold(Italic("since")),
                " - integer number of days from today, ",
                "for which search will be performed. \n\n",
            ),
            marker="➤ ",
        ),
        Bold("Other commands:\n"),
        as_marked_list(
            Text(Italic("/help"), " - Get help."),
            Text(
                Italic("/switch_rika"),
                " - Run this command to turn on/off recieving rika gif.",
            ),
            marker="🚩 ",
        ),
    )
    await message.answer(**answer.as_kwargs())


@dp.message()
async def paper_search(message: Message) -> None:
    logger.info(f"Request user id: {message.from_user.id}")
    if message.from_user.id in RIKA_USERS:
        logger.info("Sending Rika chan to you!")
        file_path = Path(__file__)
        rika_gif = FSInputFile(
            file_path.parent / ".." / "assets" / "rika_for_denis.mp4"
        )
        await message.answer_animation(rika_gif)
    try:
        args = message.text.split(sep=",")
    except Exception as e:
        logger.exception(e, stack_info=True)
        answer = Text(
            "Incorrect command.",
            "Please, check /help for more info about formating.",
        )
    tmp_dir = Path("./tmp/")
    if not tmp_dir.exists():
        tmp_dir.mkdir()
    article_explorer = PapersSurf(
        tmp_dir=tmp_dir,
        query=args[0],
        since=int(args[1].strip()),
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
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp.startup.register(set_default_commands)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    logger.info("Started")
    asyncio.run(main())
    logger.info("Finished")
