import logging
import os

from crawler.main import ParlamentPortalCrawler
from llm.main import LLMDiplomaConsumer
from publisher.main import XPublisher


def run_cron_job():
    crawler = ParlamentPortalCrawler(
        base_url="https://www.parlamento.pt",
        main_page_url="https://www.parlamento.pt/Paginas/Ultimosdiplomasaprovados.aspx",
    )

    llm_consumer = LLMDiplomaConsumer(api_key=os.environ["GEMINI_API_KEY"])

    x_publisher = XPublisher(
        consumer_key=os.environ["X_CONSUMER_KEY"],
        consumer_secret=os.environ["X_CONSUMER_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )

    try:
        result = crawler.get_latest_diploma_document_markdown()
        if result is not None:
            diploma_markdown, diploma_context_markdown = result

            post_content = llm_consumer.get_post_content(
                diploma_markdown=diploma_markdown,
                diploma_context_markdown=diploma_context_markdown,
            )

            x_publisher.create_post(text=post_content)
        else:
            logging.warning("No diploma document found")

    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    run_cron_job()
