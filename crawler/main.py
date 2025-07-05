import logging
import os
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from docling.document_converter import DocumentConverter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class ParlamentPortalCrawler:
    base_url: str
    main_page_url: str

    def _get_page_html(self, url: str) -> str | Exception:
        try:
            html_text = requests.get(url=url).text
            if not html_text or html_text == "":
                raise Exception("No HTML fetched")

            return html_text
        except (requests.exceptions.RequestException, Exception) as e:
            logging.error(f"Error fetching HTML from {url}: {e}")
            return e

    def _get_latest_approved_diplomas_url(self) -> str:
        logging.info("Getting latest approved diplomas URL")
        try:
            html = self._get_page_html(url=self.main_page_url)
            if isinstance(html, Exception):
                raise html

            crawler = BeautifulSoup(html, "lxml")
            latest_approved_diploma = crawler.find(
                "a", {"title": "Detalhe do Diploma Aprovado"}
            )
            if not latest_approved_diploma:
                raise Exception("No latest diploma a tag found!")

            href = latest_approved_diploma.get("href")
            if not href:
                raise Exception("No href attribute found!")

            full_url = self.base_url + str(href)
            return full_url

        except Exception as e:
            logging.error(f"Error getting latest diploma URL: {e}")
            raise

    def _get_diploma_process_state(self, latest_diploma_url: str) -> bool:
        """
        Use a redis db (key-value remote database) to keep track if diploma was already processed and posted or not.
        Logic:
            - if key "latest_diploma" exists and is equal to the latest_diploma_url, it was processed => break the workflow.
            - else, continue the workflow.
        """
        try:
            url = os.environ["REDIS_BASE_URL"] + "/get/latest_diploma"
            headers = {"Authorization": f"Bearer {os.environ['REDIS_BEARER_KEY']}"}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:  # 200 == successful request
                result = response.json()
                diploma_state = result.get("result")

                if not diploma_state:
                    return False

                if diploma_state == latest_diploma_url:
                    logging.info("Diploma already processed")
                    return True

                return False
            else:
                logging.error(f"HTTP request failed with status {response.status_code}")
                return False

        except Exception as e:
            logging.error(f"Error checking diploma state: {e}")
            return False

    def _set_diploma_process_state(self, latest_diploma_url: str) -> None:
        """
        Set recently processed diploma as "processed" in redis database
        """
        try:
            url = os.environ["REDIS_BASE_URL"] + "/set/latest_diploma"
            headers = {"Authorization": f"Bearer {os.environ['REDIS_BEARER_KEY']}"}
            response = requests.post(url, headers=headers, data=latest_diploma_url)

            if response.status_code != 200:
                logging.error(f"HTTP request failed with status {response.status_code}")
        except (requests.exceptions.RequestException, Exception) as e:
            logging.error(f"Error setting diploma state: {e}")

    def _get_document_markdown(self, document_url: str) -> str | None:
        try:
            doc_client = DocumentConverter()
            logging.info("Starting document conversion - this may take a while...")
            convertion_result = doc_client.convert(document_url)
            logging.info("Document conversion completed")

            document_markdown = convertion_result.document.export_to_markdown()
            if not document_markdown or document_markdown == "":
                raise Exception("Empty markdown resulting of document read operation.")

            return document_markdown
        except Exception as e:
            logging.error(f"Error converting document to markdown: {e}")
            return None

    def get_latest_diploma_document_markdown(self) -> tuple[str, str] | None:
        try:
            latest_diploma_url = self._get_latest_approved_diplomas_url()
            is_diploma_already_processed = self._get_diploma_process_state(
                latest_diploma_url=latest_diploma_url
            )

            if is_diploma_already_processed:
                return None

            latest_diploma_page_html = self._get_page_html(url=latest_diploma_url)
            if isinstance(latest_diploma_page_html, Exception):
                raise latest_diploma_page_html

            crawler = BeautifulSoup(latest_diploma_page_html, "lxml")
            diploma_document_urls = [
                str(x.get("href"))
                for x in crawler.find_all(
                    "a",
                    {
                        "title": "Detalhe do documento (formato PDF)"
                    },  # get html a tag containing the url to dowload the diploma
                )
            ]

            if not diploma_document_urls or len(diploma_document_urls) == 0:
                raise Exception("Not possible to find latest document's href.")

            diploma_document_markdown = self._get_document_markdown(
                document_url=str(diploma_document_urls[0])
            )

            diploma_context_document_markdown = self._get_document_markdown(
                document_url=str(diploma_document_urls[1])
            )

            if not diploma_document_markdown or not diploma_context_document_markdown:
                raise Exception(
                    f"Error getting document's markdown. Document urls: {diploma_document_urls}"
                )

            self._set_diploma_process_state(latest_diploma_url=latest_diploma_url)
            logging.info("Successfully processed diploma document")
            return diploma_document_markdown, diploma_context_document_markdown

        except Exception as e:
            logging.error(f"Error in get_latest_diploma_document_markdown: {e}")
            return None
