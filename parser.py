import re

from bs4 import BeautifulSoup

from normalizer import (
    normalize_model_name,
    parse_capabilities,
)


_NUMBER = re.compile(r"([\d,]+)")


def _parse_number(text):

    if not text:
        return None

    m = _NUMBER.search(text)

    if not m:
        return None

    try:
        return int(
            m.group(1).replace(",", "")
        )
    except Exception:
        return None


def _find_value(soup, title):

    node = soup.find(
        string=lambda x:
        x and title.lower() in x.lower()
    )

    if not node:
        return None

    td = node.parent

    if td is None:
        return None

    nxt = td.find_next()

    if nxt is None:
        return None

    return nxt.get_text(" ", strip=True)


def parse_model_detail(html):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    data = {}

    #
    # Model Name
    #

    h1 = soup.find("h1")

    if h1:
        data["logical_name"] = normalize_model_name(
            h1.get_text(strip=True)
        )

    #
    # Context Window
    #

    try:

        value = _find_value(
            soup,
            "Context Window",
        )

        data["context_window"] = _parse_number(value)

    except Exception:

        data["context_window"] = None

    #
    # Max Output Tokens
    #

    try:

        value = _find_value(
            soup,
            "Max Output Tokens",
        )

        data["max_output_tokens"] = _parse_number(value)

    except Exception:

        data["max_output_tokens"] = None

    #
    # Base URL
    #

    try:

        data["base_url"] = _find_value(
            soup,
            "Base URL",
        )

    except Exception:

        data["base_url"] = None

    #
    # Model ID
    #

    try:

        data["model_id"] = _find_value(
            soup,
            "Model ID",
        )

    except Exception:

        data["model_id"] = None

    #
    # API format
    #

    try:

        data["api_format"] = _find_value(
            soup,
            "API Format",
        )

    except Exception:

        data["api_format"] = None

    #
    # Capability
    #

    capabilities = []

    tags = []

    try:

        value = _find_value(
            soup,
            "Capabilities",
        )

        if value:

            capabilities = [
                x.strip()
                for x in value.split(",")
                if x.strip()
            ]

    except Exception:
        pass

    try:

        value = _find_value(
            soup,
            "Tags",
        )

        if value:

            tags = [
                x.strip()
                for x in value.split(",")
                if x.strip()
            ]

    except Exception:
        pass

    data["capability"] = parse_capabilities(
        capabilities,
        tags,
    )

    data["raw_capabilities"] = capabilities

    data["raw_tags"] = tags

    return data
