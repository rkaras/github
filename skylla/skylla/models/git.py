from pydantic import AnyUrl


class GitUrl(AnyUrl):
    allowed_schemes = {"ssh", "http", "https"}
