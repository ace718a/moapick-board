from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONTENT_AREAS = ("moving", "rent", "internet", "water")
CTA_CLASS = re.compile(r"(?:^|\s)(?:bottom-cta|mid-cta)(?:\s|$)")
RELATED_CLASS = re.compile(r"(?:^|\s)[\w-]*related[\w-]*(?:\s|$)")
BAD_HREFS = {"", "#", "javascript:void(0)", "javascript:void(0);"}
EXPECTED_LANDINGS = {
    "moving": ("moapick.co.kr", "/24"),
    "rent": ("moapick.co.kr", "/rent"),
    "internet": ("moapick.co.kr", "/internet"),
    "water": ("moapick.co.kr", "/water"),
}


class ContentAudit(HTMLParser):
    void_elements = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, area: str) -> None:
        super().__init__(convert_charrefs=True)
        self.area = area
        self.stack: list[str] = []
        self.ctas: list[dict[str, object]] = []
        self.related: list[dict[str, int]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = attr.get("class") or ""
        if tag not in self.void_elements:
            self.stack.append(tag)
        if CTA_CLASS.search(classes):
            self.ctas.append({"depth": len(self.stack), "hrefs": [], "buttons": 0})
        if RELATED_CLASS.search(classes):
            self.related.append({"depth": len(self.stack), "links": 0})
        if tag == "a":
            href = (attr.get("href") or "").strip()
            if self.ctas:
                self.ctas[-1]["hrefs"].append(href)
            if self.related:
                self.related[-1]["links"] += 1
        if tag == "button" and self.ctas:
            self.ctas[-1]["buttons"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.void_elements:
            return
        if not self.stack:
            self.errors.append(f"unexpected closing tag </{tag}>")
            return
        opening = self.stack.pop()
        if opening != tag:
            self.errors.append(f"mismatched tags <{opening}>...</{tag}>")
        depth = len(self.stack) + 1
        if self.ctas and self.ctas[-1]["depth"] == depth:
            cta = self.ctas.pop()
            hrefs = cta["hrefs"]
            if not hrefs:
                self.errors.append("CTA has no anchor")
            if cta["buttons"]:
                self.errors.append("CTA contains a button instead of a link")
            for href in hrefs:
                normalized = href.lower().replace(" ", "")
                if normalized in BAD_HREFS or normalized.startswith("javascript:"):
                    self.errors.append(f"CTA has invalid href: {href!r}")
                    continue
                parsed = urlparse(href)
                host, path = EXPECTED_LANDINGS[self.area]
                if parsed.scheme not in {"http", "https"} or parsed.netloc != host or not parsed.path.rstrip("/").startswith(path):
                    self.errors.append(f"CTA points outside expected landing: {href}")
        if self.related and self.related[-1]["depth"] == depth:
            related = self.related.pop()
            if related["links"] == 0:
                self.errors.append("related-information area is empty")

    def close(self) -> None:
        super().close()
        if self.stack:
            self.errors.append("unclosed tags: " + ", ".join(self.stack[-5:]))


def main() -> int:
    failures: list[str] = []
    checked = 0
    for area in CONTENT_AREAS:
        for path in (ROOT / area).rglob("*.html"):
            if path.parent == ROOT / area:
                continue
            checked += 1
            parser = ContentAudit(area)
            parser.feed(path.read_text(encoding="utf-8"))
            parser.close()
            failures.extend(f"{path.relative_to(ROOT)}: {error}" for error in parser.errors)
    if failures:
        print("CONTENT QA FAILED")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print(f"CONTENT QA PASS ({checked} article pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
