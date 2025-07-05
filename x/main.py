import logging
import os
from dataclasses import dataclass

import tweepy


@dataclass
class XPublisher:
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_token_secret: str

    def __post_init__(
        self,
    ):
        try:
            self.client = tweepy.Client(
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
            )
        except Exception:
            logging.error("Failed to initiliaze X Client.")

    def create_post(self, text: str):
        try:
            self.client.create_tweet(text=text)
            logging.info("Success!")
        except Exception as e:
            logging.error(f"Error publishing X post with text: {text}. Error: {e}")


publisher = XPublisher(
    consumer_key=os.environ["X_CONSUMER_KEY"],
    consumer_secret=os.environ["X_CONSUMER_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
)
