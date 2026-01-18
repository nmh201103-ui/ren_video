from abc import ABC, abstractmethod
from typing import Dict


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, url: str) -> Dict:
        pass





