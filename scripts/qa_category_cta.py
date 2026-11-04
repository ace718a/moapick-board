from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = "2026-11-04"
LEGACY = {
    "moving": {"iframe": "https://replyalba.com/intros/_frm/index.php?code=WrHxEC3ope", "href_contains": "/24/", "special": {"moving-estimate-checklist": "https://modu24.kr/frm.php?p_id=zobonpal15"}},
    "rent": {"iframe": "https://replyalba.com/intros/_frm/index.php?code=HkNocHicEW", "href_contains": "/rent"},
    "internet": {"iframe": "https://kinternet.kr/frm.php?p_id=zobonpal15", "href_contains": "/internet"},
    "water": {"iframe": "https://replyalba.com/intros/_frm/index.php?code=DnrdQaVJyl", "href_contains": "/water/"},
}
NEW = {
    "moving": {"iframe": "https://modu24.kr/frm.php?p_id=d301p", "href": "https://modu24.kr/?num=15421040", "name": "co10Frm", "id": "co10Frm", "scripts": ("https://co10.kr/gate/js/jquery.min.js", "https://co10.kr/gate/js/iframeResizer.min.js")},
    "rent": {"iframe": "https://replyalba.com/intros/_frm/index.php?code=OFrqeIk6Cx", "href": "https://replyalba.com/pt/OFrqeIk6Cx", "name": "ifrm_icode", "id": "ifrCCAl", "scripts": ("https://replyalba.com/js/jquery-1.11.0.min.js", "https://replyalba.com/js/iframeResizer.min.js")},
    "internet": {"iframe": "https://kinternet.kr/frm.php?p_id=d301p", "href": "https://kinternet.kr/?num=15421040", "name": "co10Frm", "id": "co10Frm", "scripts": ("https://co10.kr/gate/js/jquery.min.js", "https://co10.kr/gate/js/iframeResizer.min.js")},
    "water": {"iframe": "https://replyalba.com/intros/_frm/index.php?code=MPhJVqrLHl", "href": "https://replyalba.com/pt/MPhJVqrLHl", "name": "ifrm_icode", "id": "ifrCCAl", "scripts": ("https://replyalba.com/js/jquery-1.11.0.min.js", "https://replyalba.com/js/iframeResizer.min.js")},
}

errors = []
new_checked = 0
legacy_checked = 0
for category in LEGACY:
    for page in sorted((ROOT / category).glob("*/index.html")):
        text = page.read_text(encoding="utf-8", errors="ignore")
        slug = page.parent.name
        published_match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', text)
        published = published_match.group(1) if published_match else ""
        iframe_tags = re.findall(r"<iframe\b[^>]*>", text, re.I)
        iframe_srcs = re.findall(r'<iframe[^>]+src=["\']([^"\']+)', text, re.I)
        if published >= CUTOFF:
            new_checked += 1
            rule = NEW[category]
            if iframe_srcs != [rule["iframe"]]:
                errors.append(f"{category}/{slug}: new iframe mismatch {iframe_srcs}")
            if len(iframe_tags) != 1:
                errors.append(f"{category}/{slug}: expected one iframe")
            else:
                tag = iframe_tags[0]
                for attr in ("name", "id"):
                    if not re.search(rf'{attr}=["\']{re.escape(rule[attr])}["\']', tag, re.I):
                        errors.append(f"{category}/{slug}: wrong iframe {attr}")
            for script in rule["scripts"]:
                if script not in text:
                    errors.append(f"{category}/{slug}: missing script {script}")
            bottom = re.search(r'<section\s+class=["\']bottom-cta["\'][^>]*>(.*?)</section>', text, re.I | re.S)
            hrefs = re.findall(r'<a[^>]+href=["\']([^"\']+)', bottom.group(1), re.I) if bottom else []
            if hrefs != [rule["href"]]:
                errors.append(f"{category}/{slug}: new CTA mismatch {hrefs}")
        else:
            legacy_checked += 1
            rule = LEGACY[category]
            allowed_iframe = rule.get("special", {}).get(slug, rule["iframe"])
            for src in iframe_srcs:
                if src != allowed_iframe:
                    errors.append(f"{category}/{slug}: legacy iframe mismatch {src}")
            external = re.findall(r'<a[^>]+href=["\'](https?://[^"\']+)', text, re.I)
            for url in (u for u in external if "moapick.co.kr" in u):
                if rule["href_contains"] not in url:
                    errors.append(f"{category}/{slug}: legacy CTA mismatch {url}")
if errors:
    print("CATEGORY CTA QA FAIL")
    print("\n".join(errors))
    sys.exit(1)
print(f"CATEGORY CTA QA PASS (legacy {legacy_checked} / new {new_checked})")
