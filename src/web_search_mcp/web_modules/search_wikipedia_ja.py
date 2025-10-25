from typing import Annotated
import wikipedia # type: ignore[import]
import web_search_mcp.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

def search_wikipedia_ja(query: Annotated[str, "String to search for"], lang: Annotated[str, "Language of Wikipedia"], num_results: Annotated[int, "Maximum number of results to display"]) -> list[str]:
    """
    This function searches Wikipedia with the specified keywords and returns related articles.
    """

    # Use the Japanese version of Wikipedia
    wikipedia.set_lang(lang)
    logger.debug(f"Searching Wikipedia in language: {lang} for query: {query}")
    # Retrieve search results
    search_results = wikipedia.search(query, results=num_results)
    
    result_texts = []
    # Display the top results
    for i, title in enumerate(search_results):
    
        logger.debug(f"Result {i + 1}: {title}")
        try:
            # Retrieve the content of the page
            page = wikipedia.page(title)
            logger.debug(page.content[:500])  # Display the first 500 characters
            text = f"Title:\n{title}\n\nContent:\n{page.content}\n"
            result_texts.append(text)
        except wikipedia.exceptions.DisambiguationError as e:
            logger.debug(f"Disambiguation: {e.options}")
        except wikipedia.exceptions.PageError:
            logger.debug("Page not found.")
        logger.debug("\n" + "-"*50 + "\n")
    return result_texts
