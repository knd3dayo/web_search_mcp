
import os, sys
import asyncio
from typing import Annotated, Any
from dotenv import load_dotenv
import argparse
from fastmcp import FastMCP
from pydantic import Field
from web_search_mcp.web_modules.search_wikipedia_ja import search_wikipedia_ja
from web_search_mcp.web_modules.web_util import WebUtil, WebSearchResult

mcp = FastMCP("web_search_mcp") #type :ignore

# toolは実行時にmcp.tool()で登録する。@mcp.toolは使用しない。
# Wikipedia検索ツールを登録
def search_wikipedia_ja_mcp(
    query: Annotated[str, Field(description="String to search for")], 
    lang: Annotated[str, Field(description="Language of Wikipedia")], 
    num_results: Annotated[int, Field(description="Maximum number of results to display")]
    ) -> Annotated[list[str], Field(description="List of related articles from Wikipedia")]:
    """
    This function searches Wikipedia with the specified keywords and returns related articles.
    """
    return search_wikipedia_ja(query, lang, num_results)

# duckduckgo_searchツールで検索した結果を返す
async def ddgs_search(
    query: Annotated[str, "The search query"],
    max_results: Annotated[int, "Maximum number of results to return"] = 10,
    site: Annotated[str, "Site to restrict the search to (optional)"] = "",
    detail: Annotated[bool, "If True, returns detailed results including the page content and a list of links from the result pages. Default is False"] = False
) -> Annotated[list[WebSearchResult], "List of search results from DuckDuckGo"]:
    return await WebUtil.ddgs_search(query, max_results, site, detail)
        
        
# 指定したURLのWebページからテキストとリンクを抽出するツールを登録
async def extract_webpage_mcp(
    url: Annotated[str, "URL of the web page to extract text and links from"]
) -> Annotated[dict[str, Any], "Dictionary containing 'output' (extracted text) and 'urls' (list of links with href and link text)"]:
    text, urls = await WebUtil.extract_webpage(url)
    result: dict[str, Any] = {}
    result["output"] = text
    result["urls"] = urls
    return result

# 引数解析用の関数
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MCP server with specified mode and APP_DATA_PATH.")
    # -m オプションを追加
    parser.add_argument("-m", "--mode", choices=["sse", "stdio"], default="stdio", help="Mode to run the server in: 'sse' for Server-Sent Events, 'stdio' for standard input/output.")
    # -d オプションを追加　APP_DATA_PATH を指定する
    parser.add_argument("-d", "--app_data_path", type=str, help="Path to the application data directory.")
    # 引数を解析して返す
    # -t tools オプションを追加 toolsはカンマ区切りの文字列. search_wikipedia_ja_mcp, vector_search, etc. 指定されていない場合は空文字を設定
    parser.add_argument("-t", "--tools", type=str, default="", help="Comma-separated list of tools to use, e.g., 'search_wikipedia_ja_mcp,vector_search_mcp'. If not specified, no tools are loaded.")
    # -p オプションを追加　ポート番号を指定する modeがsseの場合に使用.defaultは5001
    parser.add_argument("-p", "--port", type=int, default=5001, help="Port number to run the server on. Default is 5001.")
    # -v LOG_LEVEL オプションを追加 ログレベルを指定する. デフォルトは空白文字
    parser.add_argument("-v", "--log_level", type=str, default="", help="Log level to set for the server. Default is empty, which uses the default log level.")

    return parser.parse_args()

async def main():
    # load_dotenv() を使用して環境変数を読み込む
    load_dotenv()
    # 引数を解析
    args = parse_args()
    mode = args.mode

    # tools オプションが指定されている場合は、ツールを登録
    if args.tools:
        tools = [tool.strip() for tool in args.tools.split(",")]
        for tool_name in tools:
            # tool_nameという名前の関数が存在する場合は登録
            tool = globals().get(tool_name)
            if tool and callable(tool):
                mcp.tool()(tool)
            else:
                print(f"Warning: Tool '{tool_name}' not found or not callable. Skipping registration.")
    else:
        # デフォルトのツールを登録
        mcp.tool()(search_wikipedia_ja_mcp)
        mcp.tool()(ddgs_search)
        mcp.tool()(extract_webpage_mcp)

    if mode == "stdio":
        await mcp.run_async()
    elif mode == "sse":
        # port番号を取得
        port = args.port
        await mcp.run_async(transport="sse", port=port)


if __name__ == "__main__":
    asyncio.run(main())
