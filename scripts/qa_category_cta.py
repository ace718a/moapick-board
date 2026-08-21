from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "moving": {
        "iframe": {"https://replyalba.com/pt/AM19mNDaWx"},
        "href_contains": "/24/",
        "special": {"moving-estimate-checklist": "https://modu24.kr/frm.php?p_id=zobonpal15"},
    },
    "rent": {
        "iframe": {"https://replyalba.com/intros/_frm/index.php?code=HkNocHicEW"},
        "href_contains": "/rent",
    },
    "internet": {
        "iframe": {"https://kinternet.kr/frm.php?p_id=zobonpal15"},
        "href_contains": "/internet",
    },
    "water": {
        "iframe": {"https://replyalba.com/intros/_frm/index.php?code=DnrdQaVJyl"},
        "href_contains": "/water/",
    },
}
errors=[]
for cat, rule in RULES.items():
    for page in sorted((ROOT/cat).glob("*/index.html")):
        text=page.read_text(encoding="utf-8",errors="ignore")
        slug=page.parent.name
        srcs=re.findall(r'<iframe[^>]+src=["\']([^"\']+)',text,re.I)
        allowed=set(rule["iframe"])
        if slug in rule.get("special",{}):
            allowed={rule["special"][slug]}
        for src in srcs:
            if src not in allowed:
                errors.append(f"{cat}/{slug}: wrong iframe {src}")
        ext=re.findall(r'<a[^>]+href=["\'](https?://[^"\']+)',text,re.I)
        moapick=[u for u in ext if "moapick.co.kr" in u]
        for u in moapick:
            if rule["href_contains"] not in u:
                errors.append(f"{cat}/{slug}: wrong CTA {u}")
if errors:
    print("CATEGORY CTA QA FAIL")
    print("\n".join(errors))
    sys.exit(1)
print("CATEGORY CTA QA PASS")
