import requests
import smtplib
import logging
import argparse

from datetime import datetime, timedelta
from dataclasses import dataclass

from bs4 import BeautifulSoup
from email.message import EmailMessage

import config


@dataclass
class Article:
    gericht: str
    date: datetime
    code: str
    title: str
    url: str

    def __str__(self) -> str:
        fields = [
            self.gericht,
            self.date.strftime("%d.%m.%Y"),
            self.code,
            self.title,
            self.url,
        ]

        return "\n".join(fields)


def get_articles_gber(now: datetime) -> list[Article]:
    date = now.strftime("%Y%m%d")
    url = f"https://search.bger.ch/ext/eurospider/live/de/php/aza/http/index_aza.php?date={date}&lang=de&mode=news"

    response = requests.get(url)

    if not response.ok:
        raise Exception(response.status_code)

    soup = BeautifulSoup(response.content, "html.parser")
    maincontent = soup.find(id="maincontent")
    rows = maincontent.find_all("tr")

    articles: list[Article] = []

    for row in rows:
        cells = row.find_all("td")

        if len(cells) != 5:
            continue

        if cells[1].string == "":
            continue

        category = cells[4].string

        if category.endswith("*"):
            articles.append(
                Article(
                    gericht="Bundesgericht",
                    date=datetime.strptime(cells[1].string, "%d.%m.%Y"),
                    code=cells[2].string,
                    title=cells[4].string,
                    url=cells[2].a["href"],
                )
            )

    return articles


def get_articles_gzh(now: datetime) -> list[Article]:
    def filter_css_classes(divs: list, count: int):
        entscheid = None
        entscheidDetails = None

        for div in divs:
            for css_class in div["class"]:
                if css_class == f"entscheid_nummer_{count}":
                    entscheid = div
                elif css_class == f"container_{count}":
                    entscheidDetails = div

        return entscheid, entscheidDetails

    url = "https://www.gerichte-zh.ch/entscheide/entscheide-anzeigen.html"
    response = requests.get(url)

    if not response.ok:
        raise Exception(response.status_code)

    soup = BeautifulSoup(response.content, "html.parser")
    sammlungsEntscheide = soup.find(id="entscheidsammlungEntscheide")
    entscheide_divs = sammlungsEntscheide.find_all("div")

    articles: list[Article] = []

    count = 0
    while True:
        entscheid, entscheidDetails = filter_css_classes(entscheide_divs, count)
        count += 1

        if entscheid is None or entscheidDetails is None:
            break

        p_elements = entscheid.find_all("p")

        spans = p_elements[2].find_all("span")
        date = spans[0].string
        date = datetime.strptime(date, "%d.%m.%Y")

        if date < now:
            continue

        title = p_elements[1].string
        id_num = spans[2].string
        gericht = spans[4].string
        abteilung = spans[6].string
        pdf_link = "https://www.gerichte-zh.ch" + entscheidDetails.div.p.a["href"]

        articles.append(
            Article(
                gericht=gericht,
                date=date,
                code=id_num,
                title=f"{abteilung}, {title}",
                url=pdf_link,
            )
        )

    return articles


def send_mail(articles: list[Article], now: datetime):
    server = smtplib.SMTP(config.SMTP_SERVER_ADDRESS, 587)
    # start TLS for security
    server.starttls()

    # Authentication
    server.login(config.EMAIL_SENDER, config.PASSWORD)

    # message to be sent
    message = EmailMessage()
    articles_str = [str(article) for article in articles]

    message.set_content(
        "Liste der am "
        + now.strftime("%d.%m.%Y")
        + " neu aufgenommenen Entscheide"
        + ":\n\n"
        + "\n\n".join(articles_str)
    )

    message["Subject"] = "Neues vom Bundesgericht"
    message["From"] = config.EMAIL_SENDER
    message["To"] = config.EMAIL_TO
    message["Cc"] = config.EMAIL_CC

    # sending the mail
    server.send_message(message)

    # terminating the session
    server.quit()


if __name__ == "__main__":
    logging.basicConfig(filename="bagger.log", level=logging.ERROR)
    logger = logging.getLogger(__name__)

    description = (
        "Checks the websites of BGE (bger.ch) and ZZS (gerichte-zh.ch) for new rulings "
    )
    description += "and sends a summary to the email address specified in the config."
    description += (
        "\nUnless specified using the --date option, bagger will take yesterday as the "
    )
    description += "date to match for rulings."

    parser = argparse.ArgumentParser(
        prog="Bagger",
        description=description,
    )
    parser.add_argument("--date")
    args = parser.parse_args()

    if args.date is None:
        now = datetime.now()
    else:
        now = datetime.strptime(args.date, "%d.%m.%Y")

    if now.weekday() == 0:
        yesterday = now - timedelta(days=3)
    else:
        yesterday = now - timedelta(days=1)

    articles: list[Article] = []
    try:
        articles.extend(get_articles_gber(yesterday))
    except Exception as exception:
        logger.error(str(exception))
    try:
        articles.extend(get_articles_gzh(yesterday))
    except Exception as exception:
        logger.error(str(exception))

    try:
        if len(articles) != 0:
            send_mail(articles, yesterday)
    except Exception as exception:
        logger.error(str(exception))
