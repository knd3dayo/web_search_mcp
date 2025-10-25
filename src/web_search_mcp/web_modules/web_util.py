
from typing import Any, Union
from typing import Annotated
import json
import os
from playwright.async_api import async_playwright
from ddgs import DDGS
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from bs4 import BeautifulSoup

# PlaywrightSettings クラスをファイル上部に定義
class PlaywrightSettings(BaseSettings):
    headless: bool = False
    browser: str = "msedge"
    auth_json_path: str = ""
    class Config:
        env_prefix = "PLAYWRIGHT_"
        case_sensitive = False

    def get_valid_auth_json_path(self) -> str:
        """
        auth_json_pathが存在しない場合は空文字を返す
        """
        if not self.auth_json_path or not os.path.exists(self.auth_json_path):
            return ""
        return self.auth_json_path

import web_search_mcp.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class WebSearchResult(BaseModel):
    title: str
    href: str
    body: str
    page_content: str = ""
    links: list[tuple[str, str]] = []


class WebUtil:

    @staticmethod
    def get_absolute_url(base_url: str, href: str) -> str:
        """
        hrefが相対パスの場合はbase_urlと結合して絶対URLに変換。
        すでに絶対URLの場合はそのまま返す。
        """
        from urllib.parse import urljoin
        if not href:
            return ""
        if href.startswith("http://") or href.startswith("https://"):
            return href
        return urljoin(base_url, href)

    @classmethod
    def download_file(cls, url: str, save_path: str) -> bool:
        import requests
        try:
            response = requests.get(url)
            response.raise_for_status()  # HTTPエラーが発生した場合に例外をスロー
            with open(save_path, 'wb') as file:
                file.write(response.content)
            logger.info(f"File downloaded successfully: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False


    @classmethod
    async def extract_webpage(cls, url: Annotated[str, "URL of the web page to extract text and links from"]) -> Annotated[tuple[str, list[tuple[str, str]]], "Page text, list of links (absolute href and link text from <a> tags)"]:
        """
        This function extracts text and links from the specified URL of a web page.
        リンクは絶対URLで返す。
        """
        settings = PlaywrightSettings()
        browser = None
        result = ("", [])
        try:
            async with async_playwright() as p:
                auth_json_path = settings.get_valid_auth_json_path()
                browser = await p.chromium.launch(headless=settings.headless, channel=settings.browser)
                if auth_json_path:
                    page = await browser.new_page(storage_state=auth_json_path)
                else:
                    page = await browser.new_page()
                await page.goto(url)
                page_html = await page.content()
                soup = BeautifulSoup(page_html, "html.parser")
                text = soup.get_text()
                sanitized_text = cls.sanitize_text(text)
                if not sanitized_text or len(sanitized_text) == 0:
                    return result

                # <a>タグのhrefを絶対URL化して取得
                urls: list[tuple[str, str]] = []
                for a in soup.find_all("a"):
                    href = a.get("href")
                    if href:
                        link_text = a.get_text()
                        if link_text:
                            abs_url = cls.get_absolute_url(url, str(href))
                            urls.append((abs_url, link_text))

                result = (sanitized_text, urls)

        except Exception as e:
            logger.error(f"Error extracting webpage: {e}")
        finally:
            if browser:
                await browser.close()
        return result

    @classmethod
    async def ddgs_search(
        cls, query: Annotated[str, "The search query"],
        max_results: Annotated[int, "Maximum number of results to return"] = 10,
        site: Annotated[str, "Site to restrict the search to (optional)"] = "",
        detail: Annotated[bool, "If True, returns detailed results"] = False
    ) -> Annotated[list[WebSearchResult], "List of search results from DuckDuckGo"]:
        
        """ This function performs a search using DuckDuckGo's search engine via the ddgs library.
        Args:
            query (str): The search query.
            site (str, optional): If specified, restricts the search to this site. Defaults to "".
            max_results (int, optional): The maximum number of results to return. Defaults to 10.
            detail (bool, optional): If True, returns detailed results including the page content and a list of links from the result pages. Defaults to False.
        Returns:
            list[DDGSSearchResult]: A list of search results, each containing the title, href, and body.
        """
        if site:
            query = f"site:{site} {query}"
        results = DDGS().text(query, max_results=max_results)
        search_results = [WebSearchResult(title=res.get("title", ""), href=res.get("href", ""), body=res.get("body", "")) for res in results]
        if detail:
            for res in search_results:
                logger.debug(f"Title: {res.title}\nURL: {res.href}\nBody: {res.body}\n")
                page_content, links = await cls.extract_webpage(res.href)
                res.page_content = page_content
                res.links = links

        return search_results
    
    @classmethod    
    def sanitize_text(cls, text: str) -> str:
        # テキストをサニタイズする
        # textが空の場合は空の文字列を返す
        if not text or len(text) == 0:
            return ""
        import re
        # 1. 複数の改行を1つの改行に変換
        text = re.sub(r'\n+', '\n', text)
        # 2. 複数のスペースを1つのスペースに変換
        text = re.sub(r' +', ' ', text)

        return text