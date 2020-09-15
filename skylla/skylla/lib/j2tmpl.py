from jinja2 import Environment, PackageLoader, select_autoescape

j2_env = Environment(
    loader=PackageLoader("skylla", "templates"),
    autoescape=select_autoescape(["html", "xml", "html.j2", "xml.j2"]),
)
