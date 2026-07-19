#!/usr/bin/env python3
"""
এই স্ক্রিপ্ট docs/topics/ ফোল্ডারের সব .md ফাইল স্ক্যান করে
একটা topics-index.json ফাইল বানায়, যা ওয়েবসাইটের সার্চ ফিচার ব্যবহার করে।

এই ফাইল হাতে চালানোর দরকার নেই — GitHub Action স্বয়ংক্রিয়ভাবে
প্রতিটা পুশের পর এটা চালিয়ে দেয়।
"""
import datetime
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
# টপিক ও ঘটনাপ্রবাহ সোর্স ফাইলগুলো এখন সরাসরি docs/-এর ভেতরেই রাখা হয় —
# আলাদা root-level সোর্স ফোল্ডার আর docs/-এর কপি, এই দুই জায়গার বদলে
# একটাই কপি রাখা হচ্ছে। তাই এখানে TOPICS_DIR ও DOCS_TOPICS_DIR একই path,
# এবং build-এ আর shutil.copytree করার দরকার নেই।
TOPICS_DIR = DOCS_DIR / "topics"
OUTPUT_FILE = DOCS_DIR / "topics-index.json"
CHANGES_OUTPUT_FILE = DOCS_DIR / "recent-changes.json"
VERSION_FILE = ROOT / "VERSION"
VERSION_OUTPUT = DOCS_DIR / "version.json"
SW_TEMPLATE = ROOT / "scripts" / "sw_template.js"
SW_OUTPUT = DOCS_DIR / "sw.js"

GHOTONAPROBAHO_DIR = DOCS_DIR / "ghotonaprobaho"
GHOTONAPROBAHO_OUTPUT_FILE = DOCS_DIR / "ghotonaprobaho-index.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

# TASK 7 / TASK 10: last_updated অবশ্যই ISO-সাজানোর-উপযোগী ফরম্যাটে থাকতে হবে
# (YYYY-MM বা YYYY-MM-DD) — যাতে স্ট্রিং-তুলনাতেই সময়ানুক্রম ঠিক থাকে, আলাদা
# পার্সিং লাগে না এবং লোকালাইজড (বাংলা মাসের নাম) স্ট্রিং দিয়ে সর্ট করতে হয় না।
DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")

# টপিকের ফাইলনাম-ই স্লাগ হিসেবে ব্যবহৃত হয় (আলাদা frontmatter slug ফিল্ড নেই) —
# তাই স্লাগ-ভ্যালিডেশন ফাইলনামের উপর হয়।
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

class BuildError(Exception):
    """একটা ভ্যালিডেশন সমস্যা বোঝায় — এটা ধরা পড়লে বিল্ড অবশ্যই
    নন-জিরো এক্সিট-কোড দিয়ে থামবে, আংশিক/পুরনো আউটপুট থেকে যাবে না।"""

BENGALI_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
BENGALI_MONTHS = {
    "জানুয়ারি": 1, "ফেব্রুয়ারি": 2, "মার্চ": 3, "এপ্রিল": 4,
    "মে": 5, "জুন": 6, "জুলাই": 7, "আগস্ট": 8,
    "সেপ্টেম্বর": 9, "অক্টোবর": 10, "নভেম্বর": 11, "ডিসেম্বর": 12,
}


def bengali_month_sort_key(month_str):
    """'এপ্রিল ২০২৬'-এর মতো লেখাকে (year, month_number)-এ রূপান্তর করে,
    যাতে সময়ানুক্রমে (নতুন থেকে পুরনো) সাজানো যায়। বুঝতে না পারলে
    সবচেয়ে পুরনো ধরে নেয় (তালিকার নিচে চলে যায়), বিল্ড ভেঙে পড়ে না —
    তবে চুপচাপ না থেকে stderr-এ একটা সতর্কতা দেয়, যাতে ভুল বানান/ফরম্যাট
    ধরা পড়ে (আগে এটা কোনো সংকেত ছাড়াই ভুল জায়গায় সর্ট হয়ে যেত)।"""
    try:
        parts = month_str.strip().split()
        month_name = parts[0]
        year = int(parts[1].translate(BENGALI_DIGITS))
        month_num = BENGALI_MONTHS.get(month_name, 0)
        if month_num == 0:
            print(f"সতর্কতা: '{month_str}' থেকে মাসের নাম চেনা যায়নি, সর্ট-এ এটা সবচেয়ে পুরনো ধরা হবে।", file=sys.stderr)
        return (year, month_num)
    except Exception:
        print(f"সতর্কতা: '{month_str}' পার্স করা যায়নি (প্রত্যাশিত ফরম্যাট: 'মাস বছর'), সর্ট-এ এটা সবচেয়ে পুরনো ধরা হবে।", file=sys.stderr)
        return (0, 0)


def bengali_date_sort_key(date_str):
    """'২৫ এপ্রিল ২০২৬'-এর মতো লেখাকে (year, month_number, day)-এ রূপান্তর করে।
    bengali_month_sort_key-এর মতোই আচরণ করে, কিন্তু দিনসহ।"""
    try:
        parts = date_str.strip().split()
        day = int(parts[0].translate(BENGALI_DIGITS))
        month_name = parts[1]
        year = int(parts[2].translate(BENGALI_DIGITS))
        month_num = BENGALI_MONTHS.get(month_name, 0)
        if month_num == 0:
            print(f"সতর্কতা: '{date_str}' থেকে মাসের নাম চেনা যায়নি, সর্ট-এ এটা সবচেয়ে পুরনো ধরা হবে।", file=sys.stderr)
        return (year, month_num, day)
    except Exception:
        print(f"সতর্কতা: '{date_str}' পার্স করা যায়নি (প্রত্যাশিত ফরম্যাট: 'দিন মাস বছর'), সর্ট-এ এটা সবচেয়ে পুরনো ধরা হবে।", file=sys.stderr)
        return (0, 0, 0)


def parse_ghotonaprobaho_file(path):
    """ghotonaprobaho/*.md ফাইলের একটা থেকে দিন-ভিত্তিক এন্ট্রি বের করে।
    প্রত্যাশিত ফরম্যাট:
      ## ২৫ এপ্রিল ২০২৬
      **বাংলাদেশ**
      - বুলেট এক
      - বুলেট দুই
      **আন্তর্জাতিক**
      - বুলেট তিন
    একই ফাইলে একাধিক মাসের এন্ট্রি থাকলেও সমস্যা নেই — প্রতিটা দিন নিজের
    তারিখ থেকেই বছর/মাস বের করে, তাই ফাইলের নাম/বিভাজনের উপর নির্ভর করে না।
    """
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    day_entries = []
    current_date = None
    current_category = None

    date_re = re.compile(r"^##\s+(.+?)\s*$")
    category_re = re.compile(r"^\*\*(.+?)\*\*\s*$")
    bullet_re = re.compile(r"^-\s+(.+?)\s*$")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = date_re.match(line)
        if m:
            current_date = {
                "date": m.group(1).strip(),
                "_sort": bengali_date_sort_key(m.group(1).strip()),
                "categories": [],
            }
            day_entries.append(current_date)
            current_category = None
            continue
        m = category_re.match(line)
        if m and current_date is not None:
            current_category = {"category": m.group(1).strip(), "items": []}
            current_date["categories"].append(current_category)
            continue
        m = bullet_re.match(line)
        if m and current_category is not None:
            current_category["items"].append(m.group(1).strip())
            continue
        # লাইন # হেডিং (টাইটেল) বা *(তারিখ পরিসীমা)* মন্তব্য হলে উপেক্ষা করা হয় —
        # এগুলো শুধু ফাইলের ভেতরের নোট, আউটপুটে দরকার নেই।

    return day_entries


def compile_ghotonaprobaho():
    """ghotonaprobaho/ ফোল্ডারের সব .md ফাইল থেকে দিন-ভিত্তিক ঘটনাপ্রবাহ
    একত্র করে docs/ghotonaprobaho-index.json বানায় (মাস অনুযায়ী গ্রুপ করা,
    নতুন থেকে পুরনো সাজানো)।"""
    if not GHOTONAPROBAHO_DIR.exists():
        print("তথ্য: ghotonaprobaho/ ফোল্ডার নেই, এই ফিচার বাদ দিয়ে বিল্ড চলবে।")
        return

    all_days = []
    seen_dates = {}  # তারিখ-টেক্সট -> কোন ফাইলে প্রথম দেখা গেছে (ডুপ্লিকেট ধরার জন্য)
    for path in sorted(GHOTONAPROBAHO_DIR.glob("*.md")):
        for d in parse_ghotonaprobaho_file(path):
            date_key = d["date"].strip()
            if date_key in seen_dates:
                print(
                    f"সতর্কতা: '{date_key}' তারিখটা একাধিক ফাইলে পাওয়া গেছে "
                    f"({seen_dates[date_key]} এবং {path.name}) — দুটোই যোগ হচ্ছে, "
                    f"তাই এই তারিখের এন্ট্রি ডুপ্লিকেট হতে পারে। একটা ফাইল থেকে বাদ দিন।",
                    file=sys.stderr,
                )
            else:
                seen_dates[date_key] = path.name
            all_days.append(d)

    all_days.sort(key=lambda d: d["_sort"], reverse=True)

    by_month = {}
    month_order = []
    for d in all_days:
        year, month_num, day = d["_sort"]
        month_key = f"{year:04d}-{month_num:02d}" if month_num else "অজানা"
        if month_key not in by_month:
            by_month[month_key] = {
                "month_key": month_key,
                "month_label": " ".join(d["date"].strip().split()[1:]) if month_num else "অজানা মাস",
                "days": [],
            }
            month_order.append(month_key)
        del d["_sort"]
        by_month[month_key]["days"].append(d)

    months = [by_month[k] for k in month_order]

    GHOTONAPROBAHO_OUTPUT_FILE.write_text(
        json.dumps({"months": months}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total_days = sum(len(m["days"]) for m in months)
    print(f"তৈরি হলো: {GHOTONAPROBAHO_OUTPUT_FILE} ({len(months)} মাস, {total_days} দিন)")
    # ghotonaprobaho/*.md এখন সরাসরি docs/ghotonaprobaho/-এই থাকে (আলাদা
    # root-level সোর্স ফোল্ডার নেই), তাই এখানে আর কপি করার দরকার নেই।


def parse_history_table(body, slug=""):
    """'পরিবর্তনের ইতিহাস' হেডিং-এর পরের মার্কডাউন টেবিল থেকে সারিগুলো বের করে।
    টেবিল না পেলে (heading missing, ভুল বানান, বা টেবিল খালি) চুপচাপ খালি লিস্ট
    রিটার্ন না করে stderr-এ একটা সতর্কতা দেয়, যাতে recent-changes.json থেকে
    কোনো টপিক নিঃশব্দে বাদ পড়ে গেলে সেটা ধরা পড়ে।"""
    idx = body.find("পরিবর্তনের ইতিহাস")
    if idx == -1:
        print(f"সতর্কতা: {slug or '(অজানা টপিক)'}-এ 'পরিবর্তনের ইতিহাস' সেকশন পাওয়া যায়নি, recent-changes.json-এ কোনো এন্ট্রি যুক্ত হবে না।", file=sys.stderr)
        return []
    section = body[idx:]
    rows = []
    started = False
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if started:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0] in ("মাস",):  # হেডার সারি
            started = True
            continue
        if set("".join(cells)) <= set("-: "):  # সেপারেটর সারি (|---|---|)
            continue
        started = True
        rows.append({
            "month": cells[0],
            "change": cells[1] if len(cells) > 1 else "",
            "reason": cells[2] if len(cells) > 2 else "",
        })
    if not rows:
        print(f"সতর্কতা: {slug or '(অজানা টপিক)'}-এ 'পরিবর্তনের ইতিহাস' সেকশন আছে কিন্তু কোনো টেবিল সারি পার্স করা যায়নি — ফরম্যাট চেক করো।", file=sys.stderr)
    return rows


def compile_recent_changes(topic_entries):
    """সব টপিকের 'পরিবর্তনের ইতিহাস' টেবিল একত্র করে সময়ানুক্রমে সাজিয়ে
    docs/recent-changes.json বানায় — উইকিপিডিয়ার Recent Changes-এর মতো।"""
    all_changes = []
    for entry in topic_entries:
        rows = parse_history_table(entry["raw_body"], slug=entry.get("slug", ""))
        for row in rows:
            all_changes.append({
                "topic_slug": entry["slug"],
                "topic_title": entry["title"],
                "month": row["month"],
                "change": row["change"],
                "reason": row["reason"],
                "_sort": bengali_month_sort_key(row["month"]),
            })
    all_changes.sort(key=lambda c: c["_sort"], reverse=True)
    for c in all_changes:
        del c["_sort"]

    CHANGES_OUTPUT_FILE.write_text(
        json.dumps({"changes": all_changes}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"তৈরি হলো: {CHANGES_OUTPUT_FILE} ({len(all_changes)} টা এন্ট্রি)")


def parse_frontmatter_yaml(block, path):
    """ফ্রন্টম্যাটার ব্লক real YAML দিয়ে পার্স করে (pyyaml আবশ্যক)।
    এতে ব্র্যাকেট-স্টাইল (tags: [a, b]) আর ব্লক-লিস্ট (tags:\n  - a\n  - b)
    দুটোই সঠিকভাবে সাপোর্ট হয় — কোনো কাস্টম/দুর্বল পার্সার না রেখে।
    পার্স ব্যর্থ হলে BuildError তোলে (বিল্ড থামানোর জন্য)।"""
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as e:
        raise BuildError(f"{path.name}: frontmatter YAML পার্স করা যায়নি — {e}")
    if not isinstance(data, dict):
        raise BuildError(f"{path.name}: frontmatter একটা key: value ম্যাপ হতে হবে")
    # YAML 'YYYY-MM-DD' কে auto-parse করে datetime.date বানিয়ে ফেলে (quote ছাড়া লিখলে) —
    # সবসময় ISO স্ট্রিং-এই রাখা হয় (TASK 10: internal-এ সবসময় ISO)।
    if isinstance(data.get("last_updated"), (datetime.date, datetime.datetime)):
        data["last_updated"] = data["last_updated"].isoformat()[:10]
    return data


def extract_snippet(body, limit=160):
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("|"):
            return (line[:limit] + "…") if len(line) > limit else line
    return ""


def strip_markdown(body):
    """মার্কডাউন সিনট্যাক্স সরিয়ে সাদামাটা টেক্সট বানায়, যাতে ফুল-টেক্সট
    সার্চের সময় হ্যাশ/পাইপ/তারকা চিহ্নের কারণে মিল খুঁজে পেতে সমস্যা না হয়।"""
    text = body
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)      # হেডিং হ্যাশ
    text = re.sub(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"\|", " ", text)                                    # টেবিলের পাইপ
    text = re.sub(r"^-{2,}\s*$", " ", text, flags=re.MULTILINE)        # টেবিলের ড্যাশ-লাইন
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)                       # বোল্ড
    text = re.sub(r"\*(.*?)\*", r"\1", text)                           # ইটালিক
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def validate_topic(path, meta, body):
    """প্রতিটা টপিক ফাইলের frontmatter ও গঠন কড়াভাবে যাচাই করে (TASK 7).
    এখানে যা কিছু সমস্যা পাওয়া যায় তার প্রতিটাই এখন থেকে বিল্ড-ফেইলিং এরর
    (আগে শুধু সতর্কতা ছিল, কিন্তু TASK 9 অনুযায়ী ভুল মেটাডেটা/মিসিং ফিল্ডে
    বিল্ড অবশ্যই non-zero এক্সিট-কোড দিয়ে থামতে হবে)।"""
    errors = []

    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title নেই বা খালি")

    tags = meta.get("tags")
    if not isinstance(tags, list):
        errors.append(
            "tags অবশ্যই একটা array/list হতে হবে (যেমন 'tags:\\n  - অর্থনীতি\\n  - GDP' "
            f"অথবা 'tags: [অর্থনীতি, GDP]') — পাওয়া গেছে: {tags!r}"
        )
    elif len(tags) == 0:
        errors.append("tags খালি — কমপক্ষে একটা ট্যাগ দরকার")
    elif not all(isinstance(t, str) and t.strip() for t in tags):
        errors.append("tags-এর প্রতিটা আইটেম non-empty টেক্সট হতে হবে")

    last_updated = meta.get("last_updated")
    if not isinstance(last_updated, str) or not DATE_RE.match(last_updated.strip()):
        errors.append(
            f"last_updated সঠিক ISO ফরম্যাটে নেই (YYYY-MM বা YYYY-MM-DD হওয়া উচিত) — পাওয়া গেছে: {last_updated!r}"
        )

    slug = path.stem
    if not SLUG_RE.match(slug):
        errors.append(f"ফাইলনাম/স্লাগ '{slug}' বৈধ নয় (শুধু lowercase অক্ষর/সংখ্যা/হাইফেন অনুমোদিত)")

    if "বর্তমান তথ্য" not in body:
        errors.append('"বর্তমান তথ্য" সেকশন খুঁজে পাওয়া যায়নি')
    if "পরিবর্তনের ইতিহাস" not in body:
        errors.append('"পরিবর্তনের ইতিহাস" সেকশন খুঁজে পাওয়া যায়নি')

    return errors


def write_version_json():
    """VERSION ফাইলের সংখ্যাটা docs/version.json-এ লিখে দেয়, যাতে এই ফাইলটা
    ম্যানুয়ালি এডিট করে ভুলে VERSION-এর সাথে out-of-sync না থেকে যায়।"""
    version = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "0"
    VERSION_OUTPUT.write_text(
        json.dumps({"version": version}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"তৈরি হলো: {VERSION_OUTPUT} (version: {version})")


def stamp_service_worker():
    """VERSION ফাইলের সংখ্যাটা sw.js-এর ক্যাশ-নামে বসিয়ে docs/sw.js বানায়।
    এভাবে প্রতিবার ভার্সন বাড়লেই ব্যবহারকারীর ব্রাউজার পুরনো ক্যাশ ফেলে
    দিয়ে সব ফাইল নতুন করে ডাউনলোড করবে — অটো ক্যাশ-ক্লিন।"""
    if not SW_TEMPLATE.exists():
        print("সতর্কতা: sw_template.js পাওয়া যায়নি, sw.js আপডেট করা হলো না।", file=sys.stderr)
        return
    version = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "0"
    template = SW_TEMPLATE.read_text(encoding="utf-8")
    stamped = template.replace("__VERSION__", version)
    SW_OUTPUT.write_text(stamped, encoding="utf-8")
    print(f"তৈরি হলো: {SW_OUTPUT} (cache: oca-cache-{version})")


def _main():
    # TASK 9: বিল্ড দুই ধাপে হয় — আগে সব কিছু ভ্যালিডেট করা হয়, তারপরই
    # (এবং শুধুমাত্র সবকিছু ঠিক থাকলেই) কোনো আউটপুট ফাইল লেখা হয় বা
    # docs/topics/ কপি করা হয়। কোনো এক জায়গায় সমস্যা পেলে গোটা বিল্ড
    # non-zero এক্সিট-কোড দিয়ে থামে — আংশিক বা পুরনো/ভুল আউটপুট থাকে না।
    if yaml is None:
        print("✗ বিল্ড ব্যর্থ: pyyaml ইনস্টল নেই (প্রয়োজনীয় ডিপেন্ডেন্সি অনুপস্থিত)।", file=sys.stderr)
        print("   ঠিক করতে: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    if not TOPICS_DIR.exists():
        print("✗ বিল্ড ব্যর্থ: docs/topics/ ফোল্ডার পাওয়া যায়নি।", file=sys.stderr)
        sys.exit(1)

    all_errors = []
    entries = []

    for path in sorted(TOPICS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        # কিছু এডিটর (যেমন Windows Notepad) UTF-8 ফাইলের শুরুতে একটা অদৃশ্য
        # BOM ক্যারেক্টার যোগ করে দেয়, যেটা থাকলে নিচের frontmatter regex
        # (যা ফাইলের একদম শুরু থেকে '---' খোঁজে) ম্যাচ করতে ব্যর্থ হতো এবং
        # পুরো বিল্ড আটকে যেত। এখানেই স্ট্রিপ করে দেওয়া হচ্ছে, যাতে এমন
        # ফাইল থাকলেও নীরবে ঠিকভাবে পার্স হয়।
        text = text.lstrip("\ufeff")
        match = FRONTMATTER_RE.match(text)
        if not match:
            all_errors.append(f"{path.name}: frontmatter (---...---) পাওয়া যায়নি")
            continue
        try:
            meta = parse_frontmatter_yaml(match.group(1), path)
        except BuildError as e:
            all_errors.append(str(e))
            continue
        body = match.group(2)
        errors = validate_topic(path, meta, body)
        if errors:
            all_errors.extend(f"{path.name}: {e}" for e in errors)
            continue
        entries.append({
            "slug": path.stem,
            "title": meta.get("title", path.stem),
            "tags": meta.get("tags", []),
            "last_updated": meta.get("last_updated", ""),
            "snippet": extract_snippet(body),
            "body": strip_markdown(body),
            "file": f"topics/{path.name}",
            "raw_body": body,
        })

    if all_errors:
        print(f"✗ বিল্ড ব্যর্থ — {len(all_errors)} টা ভ্যালিডেশন সমস্যা পাওয়া গেছে:", file=sys.stderr)
        for e in all_errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ সব ({len(entries)}) টপিক ফাইল ভ্যালিডেশন পাস করেছে।")

    # এখান থেকে সব ভ্যালিডেশন পাস করেছে — এখন থেকেই ফাইল-সিস্টেমে লেখা শুরু।
    # topics/*.md এখন সরাসরি docs/topics/-এই থাকে (আলাদা root-level সোর্স
    # ফোল্ডার নেই), তাই আগের মতো docs/topics/-এ আলাদা করে কপি করার দরকার নেই।

    stamp_service_worker()
    write_version_json()

    compile_recent_changes(entries)
    compile_ghotonaprobaho()

    for e in entries:
        del e["raw_body"]  # শুধু history-পার্সিং-এর জন্য দরকার ছিল, চূড়ান্ত ইনডেক্সে থাকবে না

    OUTPUT_FILE.write_text(
        json.dumps({"topics": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"তৈরি হলো: {OUTPUT_FILE} ({len(entries)} টি টপিক)")

def main():
    """`_main()`-কে wrap করে রাখা হয়েছে — কোনো অপ্রত্যাশিত/অচেনা সমস্যায়ও
    (যা উপরের নির্দিষ্ট ভ্যালিডেশনগুলো ধরতে পারেনি) বিল্ড যেন কাঁচা Python
    traceback না দেখিয়ে একটা পরিষ্কার এরর-মেসেজ দিয়ে non-zero exit করে।"""
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"✗ বিল্ড ব্যর্থ — অপ্রত্যাশিত সমস্যা: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
