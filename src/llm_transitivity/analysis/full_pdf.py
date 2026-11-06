"""Convert the report article to shared static blocks for a continuous PDF."""

from html.parser import HTMLParser

from llm_transitivity.analysis.interpret_document import _pdf


class ArticleBlocks(HTMLParser):
    """Read generated headings, paragraphs, literal responses, tables and figures."""

    def __init__(self):
        super().__init__()
        self.blocks = []
        self.active = None
        self.parts = []
        self.table = None
        self.row = None
        self.cell = None
        self.skip = 0
        self.anchor = None
        self.link = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.skip:
            self.skip += tag == "div"
            return
        if tag == "div" and attrs.get("class") == "toc":
            self.skip = 1
        elif tag == "ul" and self.active == "li":
            self.handle_endtag("li")
        elif tag == "table":
            self.table = []
        elif tag == "tr":
            self.row = []
        elif tag in ("th", "td"):
            self.cell = []
        elif tag == "img":
            self.blocks.append(
                {
                    "kind": "figure",
                    "name": attrs["src"].removeprefix("figures/").removesuffix(".svg"),
                    "alt": attrs.get("alt", ""),
                }
            )
        elif tag == "a" and self.active == "li":
            href = attrs.get("href", "")
            if href.startswith("#"):
                self.link = href[1:]
        elif tag == "br":
            self.handle_data("\n")
        elif tag in ("p", "pre", "h1", "h2", "h3", "li") and self.active is None:
            self.active = tag
            self.parts = []
            self.anchor = attrs.get("id")
            self.link = None

    def handle_data(self, data):
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(data)
        elif self.active is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= tag == "div"
            return
        if tag in ("td", "th"):
            self.row.append("".join(self.cell))
            self.cell = None
        elif tag == "tr":
            self.table.append(self.row)
        elif tag == "table":
            self.blocks.append(
                {"kind": "table", "headers": self.table[0], "rows": self.table[1:]}
            )
            self.table = None
        elif tag == self.active:
            text = "".join(self.parts)
            if text.strip():
                if tag.startswith("h"):
                    block = {"kind": "heading", "level": int(tag[1]), "text": text}
                else:
                    block = {
                        "kind": "literal" if tag == "pre" else "text",
                        "text": text,
                    }
                if self.anchor:
                    block["anchor"] = self.anchor
                if self.link:
                    block["link"] = self.link
                self.blocks.append(block)
            self.active = None
            self.parts = []


def render_pdf(output, article):
    parser = ArticleBlocks()
    parser.feed(article)
    _pdf(output, parser.blocks)
