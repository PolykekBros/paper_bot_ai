from aiogram.utils import formatting
from aiogram.utils.formatting import Text, Bold, Italic, TextLink
from aiogram.types import Message
import pandas as pd


def message_generator(articles: pd.DataFrame, message: Message) -> Text:
    header = Text(
        "Here are the articles, that I found with your query, ",
        Bold(message.from_user.full_name),
        ":\n\n",
    )
    footer = Text(
        "\n\n",
        "If it is not what you was looking for, please, try to change your query: \n",
        Italic(message.text),
    )

    articles_list = []
    for _, article in articles.iterrows():
        title = article["Title"]
        link = article["URL"]
        articles_list.append(TextLink(title, url=link))

    body = formatting.as_marked_list(*articles_list, marker="✏️")
    return Text(header, body, footer)
