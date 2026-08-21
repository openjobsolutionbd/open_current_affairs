#!/usr/bin/env python3
"""
build_index.py-এর ফাংশনগুলোর জন্য ছোট, নির্দিষ্ট regression টেস্ট —
আগে ধরা পড়া bug (দেখুন BUGFIX.md) যেন চুপচাপ আবার ফিরে না আসে।

নিয়ম (AGENTS.md-এও লেখা আছে): ভবিষ্যতে build_index.py-তে নতুন কোনো bug
পাওয়া/ঠিক করা হলে, BUGFIX.md-এ এন্ট্রি লেখার পাশাপাশি এখানে একটা
matching test যোগ করতে হবে।

চালানোর নিয়ম: python3 scripts/test_build_index.py
(scripts/preflight.sh কোড-ফাইল বদলালে এটা স্বয়ংক্রিয়ভাবে চালায়)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_index import strip_markdown  # noqa: E402
from build_index import parse_mcq_file  # noqa: E402

tests = []


def test(name):
    def deco(fn):
        tests.append((name, fn))
        return fn
    return deco


@test("strip_markdown — table separator row-এ stray double-space থাকা উচিত নয় (BUG-10)")
def _():
    body = "লাইন এক\n|কলাম১|কলাম২|\n|---|---|\n|ক|খ|\nলাইন শেষ"
    out = strip_markdown(body)
    assert "  " not in out, f"stray double-space পাওয়া গেছে: {out!r} (BUGFIX.md BUG-10)"


@test("strip_markdown — heading হ্যাশ ও bold/italic মার্কার সরে যাওয়া উচিত")
def _():
    out = strip_markdown("## শিরোনাম\n**বোল্ড** ও *ইটালিক* টেক্সট")
    assert "#" not in out, f"heading হ্যাশ রয়ে গেছে: {out!r}"
    assert "*" not in out, f"bold/italic মার্কার রয়ে গেছে: {out!r}"
    assert "শিরোনাম" in out and "বোল্ড" in out and "ইটালিক" in out


@test("parse_mcq_file — বিভিন্ন সেকশনে প্রশ্ন-নাম্বার ওভারল্যাপ করলেও, উত্তর-কী সেকশনের বাইরে (ফাইলের শেষে consolidated) থাকলে কোনো সেকশন হারিয়ে যাওয়া বা ভুল সেকশনের উত্তর বসে যাওয়া উচিত না (BUG-17)")
def _():
    import tempfile

    # ম্যাগাজিনের একটা প্রচলিত কনভেনশন: সব বিভাগের প্রশ্ন আগে, তারপর
    # ফাইলের শেষে সবগুলোর উত্তর-কী একসাথে (consolidated) — প্রতি বিভাগেই
    # নাম্বারিং নতুন করে ১ থেকে শুরু।
    sample = (
        "## বিভাগ ১\n"
        "১. প্রথম বিভাগের প্রথম প্রশ্ন?\n"
        "ক) ক১ খ) খ১ গ) গ১ ঘ) ঘ১\n\n"
        "২. প্রথম বিভাগের দ্বিতীয় প্রশ্ন?\n"
        "ক) ক২ খ) খ২ গ) গ২ ঘ) ঘ২\n\n"
        "## বিভাগ ২\n"
        "১. দ্বিতীয় বিভাগের প্রথম প্রশ্ন?\n"
        "ক) খক১ খ) খখ১ গ) খগ১ ঘ) খঘ১\n\n"
        "২. দ্বিতীয় বিভাগের দ্বিতীয় প্রশ্ন?\n"
        "ক) খক২ খ) খখ২ গ) খগ২ ঘ) খঘ২\n\n"
        "**উত্তর (বিভাগ ১):** ১.ক ২.খ\n\n"
        "**উত্তর (বিভাগ ২):** ১.গ ২.ঘ\n"
    )
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "sample.md"
        path.write_text(sample, encoding="utf-8")
        sections = parse_mcq_file(path)

    names = [s["name"] for s in sections]
    assert "বিভাগ ১" in names, (
        f"'বিভাগ ১' সেকশনটাই আউটপুট থেকে হারিয়ে গেছে (পাওয়া গেছে শুধু: {names}) — "
        "দুই সেকশনে একই প্রশ্ন-নাম্বার (১, ২...) থাকলে question_lookup shared/global "
        "থাকলে প্রথম সেকশনের প্রশ্ন উত্তর-কী কখনো মেলে না, ফলে চুপচাপ বাদ পড়ে যায়। (BUGFIX.md BUG-17)"
    )
    assert "বিভাগ ২" in names, f"'বিভাগ ২' সেকশনও হারিয়ে গেছে (পাওয়া গেছে: {names})"

    sec1 = next(s for s in sections if s["name"] == "বিভাগ ১")
    sec2 = next(s for s in sections if s["name"] == "বিভাগ ২")
    assert len(sec1["questions"]) == 2, f"বিভাগ ১-এ ২টা প্রশ্ন থাকা উচিত, পাওয়া গেছে {len(sec1['questions'])}টা"
    assert len(sec2["questions"]) == 2, f"বিভাগ ২-এ ২টা প্রশ্ন থাকা উচিত, পাওয়া গেছে {len(sec2['questions'])}টা"

    q1_1 = next(q for q in sec1["questions"] if q["number"] == "১")
    q2_1 = next(q for q in sec2["questions"] if q["number"] == "১")
    assert q1_1["answer_index"] == 0, (
        f"বিভাগ ১-এর প্রশ্ন ১-এর উত্তর 'ক' (index 0) হওয়া উচিত, পাওয়া গেছে {q1_1['answer_index']} — "
        "সম্ভবত ভুল সেকশনের উত্তর-কী প্রয়োগ হয়েছে। (BUGFIX.md BUG-17)"
    )
    assert q2_1["answer_index"] == 2, (
        f"বিভাগ ২-এর প্রশ্ন ১-এর উত্তর 'গ' (index 2) হওয়া উচিত, পাওয়া গেছে {q2_1['answer_index']} — "
        "সম্ভবত ভুল সেকশনের উত্তর-কী প্রয়োগ হয়েছে। (BUGFIX.md BUG-17)"
    )


def main():
    passed, failed = 0, []
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except AssertionError as e:
            failed.append((name, str(e)))
    if failed:
        print(f"✗ test_build_index.py ব্যর্থ — {passed}/{len(tests)} পাস, {len(failed)}টা ব্যর্থ:\n")
        for name, msg in failed:
            print(f"  ✗ {name}\n    {msg}\n")
        sys.exit(1)
    print(f"✓ test_build_index.py পাস — {passed}/{len(tests)}টা।")


if __name__ == "__main__":
    main()
