from datetime import date, timedelta
from time import sleep
import json
from typing import Any, Optional
import requests
from pathlib import Path

import defusedxml.ElementTree as ET
import findpapers
import pandas as pd
from tqdm import tqdm


class PapersSurf:
    def __init__(
        self, tmp_dir: Path, query: Optional[str] = None, since: Optional[int] = None
    ) -> None:
        self.today: date = date.today()
        self.query = query
        self.since: date = self.today - timedelta(
            days=since if since is not None else 1
        )
        self.search_results_file = tmp_dir / f"{self.today.strftime('%Y-%m-%d')}.json"
        self.databases = ["biorxiv", "arxiv", "pubmed"]

    def search_articles(self, limit, limit_per_database) -> list[dict[str, Any]]:
        if self.query:
            findpapers.search(
                outputpath=self.search_results_file,
                query=self.query,
                since=self.since,
                until=self.today,
                limit=limit,
                limit_per_database=limit_per_database,
                databases=self.databases,
            )
            with open(self.search_results_file) as papers_file:
                articles_dict = json.load(papers_file)["papers"]
            return list(articles_dict)
        else:
            print(
                "Query is empty! Don't know what to search for."
            )  # TODO: change to logger


def get_pubmed_doi(
    title: str,
    seconds_to_wait: float = 1 / 10,
    ncbi_api_key: Optional[str] = None,
    n_retries: int = 3,
) -> Optional[str]:
    api_key = f"&api_key={ncbi_api_key}" if ncbi_api_key else ""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi?db=pubmed&term={title}&retmode=json{api_key}"
    for _ in range(n_retries):
        try:
            search_response = requests.get(search_url, timeout=10)  # Added timeout
            search_data = search_response.json()
            # NCBI does not allow more than 3 requests per second (10 with an API key)
            if seconds_to_wait:
                sleep(seconds_to_wait)
            pubmed_id = (
                search_data["esearchresult"]["idlist"][0]
                if search_data["esearchresult"]["idlist"]
                else None
            )
            if not pubmed_id:
                return None
            else:
                break
        except Exception as e:
            print(f"Error fetching DOI from PubMed: {e}")
            print("Increasing timeout and retrying...")
            seconds_to_wait *= 2
            if seconds_to_wait:
                sleep(seconds_to_wait)
            continue
    if seconds_to_wait:
        sleep(seconds_to_wait)
    fetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={pubmed_id}&retmode=xml"
    fetch_response = requests.get(fetch_url, timeout=10)  # Added timeout
    root = ET.fromstring(fetch_response.content)  # Using defusedxml for parsing
    for article in root.findall(".//Article"):
        for el in article.findall(".//ELocationID"):
            if el.attrib.get("EIdType") == "doi":
                return str(el.text)
    return None


def article_analyser(
    articles: list[dict[str, Any]], ncbi_api_key: Optional[str] = None
) -> pd.DataFrame:
    for article in tqdm(articles):
        if "PubMed" in article["databases"]:
            doi = get_pubmed_doi(article["title"], ncbi_api_key=ncbi_api_key)
            article["url"] = f"https://doi.org/{doi}" if doi else None
        else:
            article["url"] = next(
                (s for s in article["urls"] if s.startswith("https://doi.org")), None
            )
    articles = [article for article in articles if article.get("url") is not None]

    df_articles = pd.DataFrame.from_dict(articles)
    columns = ["databases", "publication_date", "title", "keywords", "url"]
    df_articles = df_articles.loc[:, columns]
    df_articles["DOI"] = df_articles["url"].apply(lambda x: x[x.find("10.") :])
    df_articles["Date"] = date.today().strftime("%Y-%m-%d")
    df_articles["PostedDate"] = df_articles["publication_date"]
    df_articles["IsPreprint"] = df_articles["databases"].apply(
        lambda dbs: "FALSE" if "PubMed" in dbs else "TRUE"
    )
    df_articles["Title"] = df_articles["title"]
    df_articles["Keywords"] = df_articles["keywords"].apply(
        lambda kws: ", ".join(kw[2:] for kw in kws)
    )
    df_articles["URL"] = df_articles["url"]
    df_articles = df_articles[
        [
            "DOI",
            "Date",
            "PostedDate",
            "IsPreprint",
            "Title",
            "Keywords",
            "URL",
        ]
    ]
    return df_articles
