from datetime import datetime
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

import json
from elasticsearch import Elasticsearch
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)
es = Elasticsearch(
    hosts=["http://192.168.0.3:9200"],
    basic_auth=('modoo-jeonse', 'sh110930sh35!'),
    verify_certs=False
)
template_name = "modoojeonse"
index = "modoojeonse-news"


def create_index_template():
    with open('es.news.mapping.json', 'r') as f:
        template = json.load(f)
        es.options(ignore_status=[400, 404]).indices.delete(index=index)
        es.indices.put_index_template(name=template_name, body=template)


def retrieve_article():
    for page in range(1, 11):
        article_url = urlopen(
            Request('https://www.hankyung.com/realestate/news-market-trends?page={0}'.format(page), headers={'User-Agent': 'Mozilla/5.0'}))
        soup = BeautifulSoup(article_url.read(), 'html.parser')
        news = soup.select("ul.news-list div.news-item")  # <ul class=news-list> > <div class=news-item>
        for item in news:
            url = item.find("a", href=True)["href"]
            news = scrap_realestate_news(url)
            es.index(index=index, body=news)


def scrap_realestate_news(url):
    article_url = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}))
    soup = BeautifulSoup(article_url.read(), 'html.parser')
    issue_date = soup.find("span", class_="txt-date").text  # <span class="txt-date">
    title_text = soup.find("h1", class_="headline").text  # <h1 class="headline">
    html = soup.find_all("div", "article-body-wrap")  # <div class="article-body-wrap">
    summary_tag = soup.find("div", class_="summary")  # <div class="summary">
    summary_text = "" if summary_tag is None else summary_tag.text
    body_text = soup.find("div", id="articletxt").text  # <div id="articletxt">
    author_tag = soup.find("div", class_="author link subs_author_list") # <div class="author link subs_author_list" data-name="~">
    author = "" if author_tag is None else author_tag["data-name"].replace(' 기자', '', 1)

    news = {"@timestamp": datetime.strptime(issue_date, '%Y.%m.%d %H:%M').strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "title": title_text,
            "html": str(html),
            "summary_text": summary_text,
            "body_text": body_text,
            "publisher": "한경",
            "author": author,
            "url": url}
    return news


if __name__ == '__main__':
    create_index_template()
    retrieve_article()
