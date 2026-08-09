#!/usr/bin/env bash
# একই কাজ (fetch → local/remote তুলনা → build → verify) আগে ৪টা আলাদা
# কমান্ডে করা হতো — প্রতিটা কমান্ড-কল টোকেন খরচ করে (নিজের আউটপুট +
# তা নিয়ে পরের চিন্তা)। এই স্ক্রিপ্ট সবগুলো একসাথে একটাই কলে করে, এবং
# সব ঠিক থাকলে শুধু একটা সংক্ষিপ্ত ✓ লাইন দেখায় — বিস্তারিত build/verify
# লগ শুধু তখনই দেখায় যখন কিছু ভুল থাকে।
#
# push করার ঠিক আগে চালান:
#   bash scripts/preflight.sh
#
# Exit code 0 মানে push করা নিরাপদ। অন্য কোনো exit code মানে থামুন,
# নিচের মেসেজ অনুযায়ী ব্যবস্থা নিন (rebase করুন / এরর ঠিক করুন)।
set -uo pipefail
cd "$(dirname "$0")/.."

git fetch origin main --quiet 2>/tmp/preflight_fetch.log
if [ $? -ne 0 ]; then
  echo "✗ git fetch ব্যর্থ:"
  cat /tmp/preflight_fetch.log
  exit 3
fi

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
  AHEAD=$(git rev-list --count HEAD..origin/main)
  if [ "$AHEAD" -gt 0 ]; then
    echo "⚠️  remote এগিয়ে আছে — origin/main-এ $AHEAD টা নতুন কমিট আছে যা local-এ নেই।"
    echo "    সম্ভবত অন্য কোনো Claude সেশন push করেছে। এখনই push করবেন না।"
    echo "    আগে চালান: git rebase origin/main"
    echo "    তারপর conflict না থাকলে এই স্ক্রিপ্ট আবার চালান।"
    exit 2
  fi
  # local এগিয়ে, remote না — এটাই স্বাভাবিক push-এর ঠিক আগের অবস্থা, সমস্যা নয়।
fi

pip install pyyaml --break-system-packages -q 2>/dev/null

python3 scripts/build_index.py > /tmp/preflight_build.log 2>&1
if [ $? -ne 0 ]; then
  echo "✗ build_index.py ব্যর্থ:"
  cat /tmp/preflight_build.log
  exit 1
fi

python3 scripts/verify_site.py > /tmp/preflight_verify.log 2>&1
if [ $? -ne 0 ]; then
  echo "✗ verify_site.py ব্যর্থ:"
  cat /tmp/preflight_verify.log
  exit 1
fi

TOPIC_COUNT=$(ls docs/topics/*.md 2>/dev/null | wc -l | tr -d ' ')
echo "✓ preflight পাস — local ও remote সমান, build+verify ক্লিন, ${TOPIC_COUNT}টা টপিক। push করা নিরাপদ।"
