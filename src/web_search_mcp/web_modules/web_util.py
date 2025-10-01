from typing import Any, Union
from typing import Annotated
import json
import os
from playwright.async_api import async_playwright
from ddgs import DDGS
from pydantic import BaseModel
from bs4 import BeautifulSoup

import web_search_mcp.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class WebSearchResult(BaseModel):
    title: str
    href: str
    body: str
    page_content: str = ""
    links: list[tuple[str, str]] = []


class WebUtil:
    web_request_name = "web_request"
    @classmethod
    def get_web_request_objects(cls, request_dict: dict) -> dict:
        '''
        {"context": {"web_request": {}}}の形式で渡される
        '''
        # contextを取得
        from typing import Optional
        request: Optional[dict] = request_dict.get(cls.web_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return request
    
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
    async def extract_webpage_api(cls,request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # web_requestを取得
        request = WebUtil.get_web_request_objects(request_dict)

        url = request.get("url", None)
        if url is None:
            raise ValueError("URL is not set in the web_request object.")
        text, urls = await WebUtil.extract_webpage(url)
        result: dict[str, Any] = {}
        result["output"] = text
        result["urls"] = urls
        return result

    @classmethod
    async def extract_webpage(cls, url: Annotated[str, "URL of the web page to extract text and links from"]) -> Annotated[tuple[str, list[tuple[str, str]]], "Page text, list of links (href attribute and link text from <a> tags)"]:
        """
        This function extracts text and links from the specified URL of a web page.
        """
        async with async_playwright() as p:
            headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
            channel = os.getenv("PLAYWRIGHT_BROWSER", "msedge").lower()
            auth_json_path = os.getenv("PLAYWRIGHT_AUTH_JSON", "")
            
            if not os.path.exists(auth_json_path):
                auth_json_path = ""
            
            # EdgeのWebドライバーを取得
            browser = await p.chromium.launch(headless=headless, channel=channel)
            try:
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
                    return "", []

                # Retrieve href attribute and text from <a> tags
                urls: list[tuple[str, str]] = [(a.get("href"), a.get_text()) for a in soup.find_all("a")] # type: ignore
                return sanitized_text, urls

            except Exception as e:
                logger.error(f"Error extracting webpage: {e}")
                return "", []
            finally:
                await browser.close()


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