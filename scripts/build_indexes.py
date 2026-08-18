#!/usr/bin/env python3
from pathlib import Path
import html
import math
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PER_PAGE = 10

CATEGORIES = {
    "moving": {
        "label": "포장이사",
        "title": "포장이사 게시판",
        "description": "포장이사 견적과 일정, 추가비용과 계약조건을 확인하는 모아픽 포장이사 게시판입니다.",
        "head_copy": "견적·일정·추가비용과 계약 조건을 확인해 보세요.",
    },
    "rent": {
        "label": "장기렌트",
        "title": "장기렌트 게시판",
        "description": "장기렌트 견적과 계약 조건을 비교할 때 확인할 내용을 정리한 모아픽 장기렌트 게시판입니다.",
        "head_copy": "월 렌트료부터 만기 조건까지 계약 전에 확인해 보세요.",
    },
    "internet": {
        "label": "인터넷가입",
        "title": "인터넷가입 게시판",
        "description": "인터넷 요금제와 약정, 결합 할인, 설치 조건을 확인하는 모아픽 인터넷가입 게시판입니다.",
        "head_copy": "요금제부터 결합과 설치 조건까지 가입 전에 확인해 보세요.",
    },
    "water": {
        "label": "정수기렌탈",
        "title": "정수기렌탈 게시판",
        "description": "정수기 렌탈 가격과 관리방식, 약정 및 위약금 조건을 비교하는 모아픽 정수기렌탈 게시판입니다.",
        "head_copy": "관리방식과 약정, 월 렌탈료를 계약 전에 비교해 보세요.",
    },
}

def strip_tags(value):
    value = re.sub(r"<br\\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\\s+", " ", html.unescape(value)).strip()

def meta_content(text, key, value):
    p1 = rf'<meta\\s+[^>]*{key}=["\\\']{re.escape(value)}["\\\'][^>]*content=["\\\']([^"\\\']*)["\\\']'
    p2 = rf'<meta\\s+[^>]*content=["\\\']([^"\\\']*)["\\\'][^>]*{key}=["\\\']{re.escape(value)}["\\\']'
    m = re.search(p1, text, re.I) or re.search(p2, text, re.I)
    return html.unescape(m.group(1)).strip() if m else ""

def article_data(path, category):
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S | re.I)
    title = strip_tags(m.group(1)) if m else path.parent.name
    desc = meta_content(text, "name", "description")
    pub = re.search(r'"datePublished"\\s*:\\s*"([^"]+)"', text)
    mod = re.search(r'"dateModified"\\s*:\\s*"([^"]+)"', text)
    slug = path.parent.name
    return {
        "category": category,
        "slug": slug,
        "url": f"/{category}/{slug}/",
        "title": title,
        "description": desc,
        "published": pub.group(1) if pub else "",
        "modified": mod.group(1) if mod else "",
    }

def existing_order(index_path):
    if not index_path.exists():
        return []
    text = index_path.read_text(encoding="utf-8", errors="ignore")
    return re.findall(r'href=["\\\'](/(?:moving|rent|internet|water)/[^"\\\']+/)["\\\']', text)

def collect_articles():
    out = []
    for cat in CATEGORIES:
        root = ROOT / cat
        if not root.exists():
            continue
        for p in root.glob("*/index.html"):
            if p.parent.name == "page":
                continue
            out.append(article_data(p, cat))
    return out

def stable_sort(items, known_order):
    rank = {url: i for i, url in enumerate(known_order)}
    known = [x for x in items if x["url"] in rank]
    unknown = [x for x in items if x["url"] not in rank]
    known.sort(key=lambda x: rank[x["url"]])
    unknown.sort(key=lambda x: (x["published"], x["modified"], x["url"]), reverse=True)
    return unknown + known

def pagination_html(current, total, base_url):
    if total <= 1:
        return ""
    parts = ['<nav class="pagination" aria-label="페이지 이동">']
    if current > 1:
        href = base_url if current == 2 else f"{base_url}page/{current-1}/"
        parts.append(f'<a class="page-arrow" href="{href}" aria-label="이전 페이지">‹</a>')
    for n in range(1, total + 1):
        href = base_url if n == 1 else f"{base_url}page/{n}/"
        if n == current:
            parts.append(f'<span class="page-number is-current" aria-current="page">{n}</span>')
        else:
            parts.append(f'<a class="page-number" href="{href}">{n}</a>')
    if current < total:
        parts.append(f'<a class="page-arrow" href="{base_url}page/{current+1}/" aria-label="다음 페이지">›</a>')
    parts.append("</nav>")
    return "".join(parts)

def write_category_page(cat, chunk, page_num, total_pages, total_count):
    cfg = CATEGORIES[cat]
    base_url = f"/{cat}/"
    canonical = f"https://board.moapick.co.kr{base_url}" if page_num == 1 else f"https://board.moapick.co.kr{base_url}page/{page_num}/"
    page_title = f'{cfg["title"]} | 모아픽' if page_num == 1 else f'{cfg["title"]} {page_num}페이지 | 모아픽'
    start_pos = (page_num - 1) * PER_PAGE
    rows = []
    for offset, item in enumerate(chunk):
        number = total_count - (start_pos + offset)
        rows.append(
            f'      <a class="board-row" href="{html.escape(item["url"])}">\\n'
            f'        <span class="board-number">{number}</span>\\n'
            f'        <span class="board-title"><strong>{html.escape(item["title"])}</strong><small>{html.escape(item["description"])}</small></span>\\n'
            f'      </a>'
        )
    pager = pagination_html(page_num, total_pages, base_url)
    doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(page_title)}</title>
  <meta name="description" content="{html.escape(cfg["description"])}">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="/assets/style.css?v=20260818-pagination">
</head>
<body>
  <header class="site-header"><div class="header-inner"><a class="brand" href="/"><span class="brand-mark">M</span><span><strong>MOAPICK</strong><small>생활정보 게시판</small></span></a><a class="main-site" href="/">전체 게시판</a></div></header>
  <main class="board-page">
    <section class="board-head"><div class="content-wrap"><h1>{html.escape(cfg["title"])}</h1><p>{html.escape(cfg["head_copy"])}</p></div></section>
    <section class="content-wrap board-list">
      <div class="board-table-head"><span>번호</span><span>제목</span></div>
{chr(10).join(rows)}
      {pager}
    </section>
  </main>
  <footer><div class="footer-inner"><div><strong>MOAPICK.</strong><p>생활 서비스 선택을 위한 정보 게시판</p></div><p class="copyright">© 2026 MOAPICK. All rights reserved.</p></div></footer>
</body>
</html>
"""
    target = ROOT / cat / "index.html" if page_num == 1 else ROOT / cat / "page" / str(page_num) / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc, encoding="utf-8")

def main_header(page_num):
    canonical = "https://board.moapick.co.kr/" if page_num == 1 else f"https://board.moapick.co.kr/page/{page_num}/"
    title = "모아픽 생활정보 게시판 | 이사·장기렌트·인터넷·정수기" if page_num == 1 else f"모아픽 생활정보 게시판 {page_num}페이지 | 이사·장기렌트·인터넷·정수기"
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="naver-site-verification" content="4cc153b28a9c806401bb2d7b356226c82e7ec5fd" />
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="포장이사, 장기렌트, 인터넷가입, 정수기렌탈을 준비할 때 확인할 조건과 생활정보를 업종별로 정리한 모아픽 게시판입니다.">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="ko_KR">
  <meta property="og:site_name" content="모아픽 생활정보 게시판">
  <meta property="og:title" content="모아픽 생활정보 게시판">
  <meta property="og:description" content="이사·장기렌트·인터넷·정수기 정보를 업종별로 확인하세요.">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary">
  <link rel="stylesheet" href="/assets/style.css?v=20260818-pagination">
</head>
<body>
  <a class="skip" href="#content">본문 바로가기</a>
  <header class="site-header"><div class="header-inner"><a class="brand" href="/" aria-label="모아픽 생활정보 게시판 홈"><span class="brand-mark">M</span><span><strong>MOAPICK</strong><small>생활정보 게시판</small></span></a><a class="main-site" href="https://moapick.co.kr/">모아픽 메인 ↗</a></div></header>
  <main id="content">
    <section class="hero"><div class="hero-inner"><p class="eyebrow">생활 서비스 선택 전 확인할 것들</p><h1>복잡한 조건을<br><span>한곳에서 쉽게</span> 확인하세요</h1><p class="hero-copy">광고 문구보다 계약 전에 확인해야 할 조건을 중심으로 정리합니다. 필요한 업종을 선택해 살펴보세요.</p></div></section>
    <nav class="category-nav" aria-label="업종별 게시판">
      <a href="/moving/"><span><strong>포장이사</strong><small>견적·일정·계약 확인</small></span></a>
      <a href="/rent/"><span><strong>장기렌트</strong><small>비용·약정·반납 조건</small></span></a>
      <a href="/internet/"><span><strong>인터넷가입</strong><small>요금·결합·설치 기준</small></span></a>
      <a href="/water/"><span><strong>정수기렌탈</strong><small>관리·필터·의무기간</small></span></a>
    </nav>
"""

def write_main_page(chunk, page_num, total_pages, total_count):
    rows = []
    for item in chunk:
        rows.append(
            f'      <a class="home-post-row" href="{html.escape(item["url"])}">\\n'
            f'        <span class="post-category">{html.escape(CATEGORIES[item["category"]]["label"])}</span>\\n'
            f'        <span class="board-title"><strong>{html.escape(item["title"])}</strong><small>{html.escape(item["description"])}</small></span>\\n'
            f'      </a>'
        )
    pager = pagination_html(page_num, total_pages, "/")
    doc = main_header(page_num) + f"""
    <section class="content-wrap home-posts">
      <div class="home-posts-head"><h2>새로 올라온 글</h2><span>총 {total_count}개</span></div>
      <div class="board-table-head"><span>분류</span><span>제목</span></div>
{chr(10).join(rows)}
      {pager}
    </section>
  </main>
  <footer><div class="footer-inner"><div><strong>MOAPICK.</strong><p>생활 서비스 선택을 위한 정보 게시판</p></div><p class="copyright">© 2026 MOAPICK. All rights reserved.</p></div></footer>
</body>
</html>
"""
    target = ROOT / "index.html" if page_num == 1 else ROOT / "page" / str(page_num) / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc, encoding="utf-8")

def clean_generated_pages():
    targets = [ROOT / "page"] + [ROOT / cat / "page" for cat in CATEGORIES]
    for p in targets:
        if p.exists():
            shutil.rmtree(p)

def main():
    main_order = existing_order(ROOT / "index.html")
    category_orders = {cat: existing_order(ROOT / cat / "index.html") for cat in CATEGORIES}
    articles = collect_articles()

    clean_generated_pages()

    for cat in CATEGORIES:
        items = [x for x in articles if x["category"] == cat]
        items = stable_sort(items, category_orders.get(cat, []))
        total_pages = max(1, math.ceil(len(items) / PER_PAGE))
        for n in range(1, total_pages + 1):
            chunk = items[(n - 1) * PER_PAGE:n * PER_PAGE]
            write_category_page(cat, chunk, n, total_pages, len(items))

    items = stable_sort(articles, main_order)
    total_pages = max(1, math.ceil(len(items) / PER_PAGE))
    for n in range(1, total_pages + 1):
        chunk = items[(n - 1) * PER_PAGE:n * PER_PAGE]
        write_main_page(chunk, n, total_pages, len(items))

    print(f"INDEX BUILD PASS: {len(articles)} posts / main {total_pages} page(s) / {PER_PAGE} posts per page")
    for cat in CATEGORIES:
        count = len([x for x in articles if x["category"] == cat])
        print(f"- {cat}: {count} posts / {max(1, math.ceil(count / PER_PAGE))} page(s)")

if __name__ == "__main__":
    main()
