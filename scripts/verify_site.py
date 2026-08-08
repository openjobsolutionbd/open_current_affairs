#!/usr/bin/env python3
"""
এই স্ক্রিপ্ট build_index.py চালানোর পরে docs/ ফোল্ডারের generated
output ফাইলগুলো নিজে থেকে যাচাই করে — যাতে কোনো ভাঙা/অসামঞ্জস্যপূর্ণ
কনটেন্ট মানুষের চোখে না পড়েও লাইভ সাইটে চলে না যায়।

build_index.py প্রতিটা টপিক ফাইল আলাদা করে (তার নিজের frontmatter/গঠন)
যাচাই করে। এই স্ক্রিপ্ট সেটা করে না — এটা build করার *পরে*, পুরো সাইট
জুড়ে সব ফাইল একসাথে মিলিয়ে দেখে:

  ১. topics-index.json-এ যত টপিক আছে, docs/topics/*.md-এ ততগুলো
     ফাইল আছে কিনা (সংখ্যা মিলছে কিনা)
  ২. প্রতিটা টপিকের জন্য docs/topic/<slug>/index.html পাতা তৈরি
     হয়েছে কিনা (একটাও বাদ পড়েনি)
  ৩. sitemap.xml-এ প্রতিটা টপিকের URL আছে কিনা
  ৪. কোনো টপিক ফাইলে ডুপ্লিকেট slug (ফাইলনাম) নেই তো
  ৫. টপিক বডিতে [[slug]] আকারে যে internal link আছে, সেই slug
     আসলে অস্তিত্ব আছে এমন টপিকের — অন্যথায় ক্লিক করলে ভাঙা পাতা
     দেখাবে
  ৬. version.json আর VERSION ফাইলের সংখ্যা মিলছে কিনা
  ৭. docs/sw.js-এর CACHE_NAME-এ VERSION-এর সংখ্যা বসেছে কিনা

কোনো সমস্যা পেলে এই স্ক্রিপ্ট non-zero exit code দিয়ে থামে এবং
স্পষ্টভাবে কী ভুল আছে তা বাংলায় জানায়। GitHub Action-এ এটা
build-এর পরপরই চলে — এটা fail করলে generated output commit/push
হয় না, তাই ভাঙা কনটেন্ট কখনো লাইভ সাইটে পৌঁছায় না।

চালানোর নিয়ম:
    python3 scripts/build_index.py && python3 scripts/verify_site.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
TOPICS_DIR = DOCS_DIR / "topics"
TOPIC_PAGES_DIR = DOCS_DIR / "topic"
TOPICS_INDEX = DOCS_DIR / "topics-index.json"
SITEMAP = DOCS_DIR / "sitemap.xml"
VERSION_FILE = ROOT / "VERSION"
VERSION_JSON = DOCS_DIR / "version.json"
SW_JS = DOCS_DIR / "sw.js"

LINK_RE = re.compile(r"\[\[([a-z0-9-]+)\]\]")


class VerifyError(Exception):
    pass


def fail(errors):
    print("✗ verify_site.py ব্যর্থ — নিচের সমস্যাগুলো ঠিক না করে পুশ করা উচিত নয়:\n")
    for e in errors:
        print(f"  - {e}")
    print(f"\nমোট {len(errors)}টা সমস্যা পাওয়া গেছে।")
    sys.exit(1)


def main():
    errors = []

    # ১. topics-index.json বনাম docs/topics/*.md ফাইলসংখ্যা
    if not TOPICS_INDEX.exists():
        fail([f"{TOPICS_INDEX} পাওয়া যায়নি — আগে build_index.py চালাতে হবে"])

    index_data = json.loads(TOPICS_INDEX.read_text(encoding="utf-8"))
    index_topics = index_data.get("topics", [])
    index_slugs = {t["slug"] for t in index_topics}

    md_files = sorted(TOPICS_DIR.glob("*.md"))
    md_slugs = {p.stem for p in md_files}

    if len(index_slugs) != len(md_slugs):
        errors.append(
            f"topics-index.json-এ {len(index_slugs)}টা টপিক আছে, কিন্তু "
            f"docs/topics/-এ .md ফাইল আছে {len(md_slugs)}টা — সংখ্যা মিলছে না"
        )

    missing_from_index = md_slugs - index_slugs
    if missing_from_index:
        errors.append(
            "এই .md ফাইলগুলো topics-index.json-এ ইনডেক্স হয়নি (সম্ভবত frontmatter/গঠনে "
            f"ভুল আছে): {', '.join(sorted(missing_from_index))}"
        )

    extra_in_index = index_slugs - md_slugs
    if extra_in_index:
        errors.append(
            "topics-index.json-এ এমন slug আছে যার কোনো .md ফাইল docs/topics/-এ নেই "
            f"(পুরনো/এতিম এন্ট্রি হতে পারে): {', '.join(sorted(extra_in_index))}"
        )

    # ২. ডুপ্লিকেট slug (কেস-ইনসেনসিটিভ, যেহেতু ফাইল-সিস্টেম কেস-সেনসিটিভ না-ও হতে পারে)
    seen_lower = {}
    for slug in md_slugs:
        low = slug.lower()
        if low in seen_lower and seen_lower[low] != slug:
            errors.append(f"ডুপ্লিকেট slug (case-insensitive collision): '{slug}' বনাম '{seen_lower[low]}'")
        seen_lower[low] = slug

    # ৩. প্রতিটা টপিকের docs/topic/<slug>/index.html আছে কিনা
    for slug in sorted(index_slugs):
        page = TOPIC_PAGES_DIR / slug / "index.html"
        if not page.exists():
            errors.append(f"'{slug}' টপিকের জন্য docs/topic/{slug}/index.html তৈরি হয়নি")

    # ৪. sitemap.xml-এ প্রতিটা টপিকের URL আছে কিনা
    if SITEMAP.exists():
        sitemap_text = SITEMAP.read_text(encoding="utf-8")
        for slug in sorted(index_slugs):
            if slug not in sitemap_text:
                errors.append(f"'{slug}' টপিকের URL sitemap.xml-এ পাওয়া যায়নি")
    else:
        errors.append(f"{SITEMAP} পাওয়া যায়নি")

    # ৫. প্রতিটা টপিক বডিতে থাকা [[slug]] internal link বৈধ কিনা
    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        for m in LINK_RE.finditer(text):
            linked_slug = m.group(1)
            if linked_slug not in md_slugs:
                errors.append(
                    f"'{md_path.name}'-এ [[{linked_slug}]] লিংক আছে, কিন্তু এই নামে "
                    "কোনো টপিক ফাইল নেই (ভাঙা লিংক)"
                )

    # ঘটনাপ্রবাহ ফাইলেও [[slug]] লিংক থাকতে পারে
    archive_dir = ROOT / "archive"
    if archive_dir.exists():
        for arc_path in sorted(archive_dir.glob("*.md")):
            text = arc_path.read_text(encoding="utf-8")
            for m in LINK_RE.finditer(text):
                linked_slug = m.group(1)
                if linked_slug not in md_slugs:
                    errors.append(
                        f"'{arc_path.relative_to(ROOT)}'-এ [[{linked_slug}]] লিংক আছে, কিন্তু "
                        "এই নামে কোনো টপিক ফাইল নেই (ভাঙা লিংক)"
                    )

    # ৬. VERSION বনাম version.json
    if VERSION_FILE.exists() and VERSION_JSON.exists():
        version_file_val = VERSION_FILE.read_text(encoding="utf-8").strip()
        try:
            version_json_val = json.loads(VERSION_JSON.read_text(encoding="utf-8")).get("version")
        except json.JSONDecodeError:
            version_json_val = None
        if version_file_val != version_json_val:
            errors.append(
                f"VERSION ফাইলে '{version_file_val}' কিন্তু docs/version.json-এ "
                f"'{version_json_val}' — মিলছে না"
            )
    else:
        errors.append("VERSION বা docs/version.json ফাইল পাওয়া যায়নি")

    # ৭. sw.js-এর CACHE_NAME-এ VERSION বসেছে কিনা
    if VERSION_FILE.exists() and SW_JS.exists():
        version_file_val = VERSION_FILE.read_text(encoding="utf-8").strip()
        sw_text = SW_JS.read_text(encoding="utf-8")
        if version_file_val not in sw_text:
            errors.append(
                f"docs/sw.js-এ VERSION ('{version_file_val}') সংখ্যাটা CACHE_NAME-এ খুঁজে পাওয়া যায়নি"
            )
    elif not SW_JS.exists():
        errors.append(f"{SW_JS} পাওয়া যায়নি")

    if errors:
        fail(errors)

    print(f"✓ verify_site.py পাস করেছে — {len(md_slugs)}টা টপিক, সব সামঞ্জস্যপূর্ণ, কোনো ভাঙা লিংক নেই।")


if __name__ == "__main__":
    main()
