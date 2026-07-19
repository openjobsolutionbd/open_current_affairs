# Open Current Affairs

টপিক-ভিত্তিক কারেন্ট অ্যাফেয়ার্স knowledge-base। প্রতি মাসে নতুন তথ্য `docs/topics/`-এর টপিক পেজে যোগ হয় এবং প্রতিটি পেজে পরিবর্তনের ইতিহাস থাকে।

## এই রিপোতে কী কী আছে

- **`docs/topics/`** — মূল কনটেন্ট, হাতে edit করার সোর্স। প্রতিটি ফাইলে "বর্তমান তথ্য" ও "পরিবর্তনের ইতিহাস" অংশ থাকে।
- **`archive/`** — মাসিক আসল সোর্স ডকুমেন্ট, যাচাই ও রেফারেন্সের জন্য।
- **`docs/index.html`** — সার্চ, টপিক পড়া, আজকের রিভিশন, সাম্প্রতিক পরিবর্তন ও ড্যাশবোর্ডসহ static website। Cloudflare Pages দিয়ে হোস্ট করা হয়।
- **`docs/topics-index.json`** — সার্চের জন্য স্বয়ংক্রিয়ভাবে তৈরি index; হাতে edit করবে না।
- **`docs/recent-changes.json`**, **`docs/sw.js`**, **`docs/version.json`** — build-এর সময় তৈরি হওয়া website output; হাতে edit করবে না।
- **`docs/vendor/`** — offline rendering-এর জন্য local Markdown renderer ও sanitizer library।
- **`scripts/build_index.py`** — topic validate করে website-এর generated data তৈরি করে।
- **`scripts/sw_template.js`** — service worker-এর template।
- **`.github/workflows/update-wiki.yml`** — push-এর পর build চালিয়ে generated output আপডেট করে (যদি repo-তে workflow সক্রিয় থাকে)।

## Cloudflare Pages-এ চালু করা

1. পুরো repo GitHub-এ push করো।
2. Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git-এ যাও।
3. repo নির্বাচন করো।
4. Framework preset `None`, Build command খালি, Build output directory `docs` রাখো।
5. Save and Deploy চাপো।

`docs/topics/`-এ পরিবর্তন করলে `scripts/build_index.py` চালিয়ে generated output আপডেট করতে হবে। GitHub Action এটি স্বয়ংক্রিয়ভাবে করে থাকলে আলাদা করে চালাতে হবে না।

## নতুন মাসের তথ্য যোগ করা

1. নতুন মাসের কারেন্ট অ্যাফেয়ার্স ফাইল Claude-কে দাও।
2. বলো: “এই মাসের তথ্য দিয়ে টপিক পেজগুলো আপডেট করো।”
3. Claude সংশ্লিষ্ট টপিকের বর্তমান তথ্য ও পরিবর্তনের ইতিহাস আপডেট করবে, নতুন বিষয় হলে নতুন topic file বানাবে এবং আসল মাসিক ফাইল `archive/`-এ রাখবে।
4. পরিবর্তন GitHub-এ push করলে generated search index আপডেট হবে।

এই কাজের সময় Claude `EDITORIAL_MEMORY.md`-এ জমা হওয়া আগের সিদ্ধান্তগুলো মেনে চলে, আর নতুন কোনো স্থায়ী-যোগ্য সিদ্ধান্ত এলে সেখানে নিজে থেকেই যোগ করে রাখে।

## একটি topic file-এর কাঠামো

```markdown
---
title: বাংলাদেশের GDP পরিসংখ্যান
tags: [অর্থনীতি, GDP, পরিসংখ্যান ব্যুরো]
last_updated: 2026-04
---

## বর্তমান তথ্য
(এখানে সর্বশেষ তথ্য থাকবে)

## পরিবর্তনের ইতিহাস
| মাস | কী পরিবর্তন হয়েছে | কেন / সূত্র |
|---|---|---|
| এপ্রিল ২০২৬ | পেজ প্রথম তৈরি হলো | মাসিক কারেন্ট অ্যাফেয়ার্স |
```

`title`, `tags` ও `last_updated` frontmatter সঠিক রাখা জরুরি, কারণ search index এগুলোর ওপর নির্ভর করে।

## Website-এর ফিচার

- আজকের রিভিশন: প্রতিদিন পাঁচটি random topic দেখায়।
- Search: title, tags ও full text-এ খোঁজে।
- Topic print/PDF ও shareable link।
- Dashboard: topic count, tag coverage, oldest topics ও reading progress।
- Recent changes feed, tag browsing ও related topics।
- Reading progress, dark mode এবং offline support browser-এ কাজ করে।

Reading progress ও theme preference browser-এর localStorage-এ থাকে; অন্য browser বা device-এ এগুলো আলাদা থাকবে।

## বর্তমান topic-এর উদাহরণ

- বাংলাদেশের GDP পরিসংখ্যান
- মন্ত্রিসভা ও দপ্তর বণ্টন
- ত্রয়োদশ জাতীয় সংসদ
- ইরান-ইসরায়েল-মার্কিন সংকট
- LDC উত্তরণ

আরও বিষয় যোগ করতে `docs/topics/`-এ নতুন valid topic file তৈরি করো।
