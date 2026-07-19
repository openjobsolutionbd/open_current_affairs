# JobArchive — Project Notes

## ১. প্রজেক্ট কী

JobArchive একটি static, topic-based current-affairs knowledge-base। প্রতিটি বিষয় `topics/`-এ আলাদা Markdown page হিসেবে থাকে। Page-এ সর্বশেষ তথ্য এবং পরিবর্তনের ইতিহাস—দুইটিই থাকে। Website-এ search, topic reading, recent changes, dashboard, daily revision strip, dark mode এবং offline support আছে।

## ২. Source ও generated output

```text
archive-main/
├── PROJECT.md                 ← এই ফাইল (মাস্টার ডকুমেন্টেশন — সিস্টেম কীভাবে বানানো)
├── EDITORIAL_MEMORY.md        ← ক্রমবর্ধমান নিয়ম-খাতা (কনটেন্ট কীভাবে লেখা/গোছানো — প্রতি সেশনে আগে পড়তে হয়)
├── topics/                    ← একমাত্র মূল topic content
├── archive/                   ← মাসিক source/reference documents
├── scripts/build_index.py     ← validation ও build script
├── scripts/sw_template.js     ← service-worker template
├── docs/index.html            ← website application
├── docs/vendor/               ← local Markdown renderer ও sanitizer
├── docs/manifest.json         ← PWA metadata
├── docs/icon-*.png            ← PWA icons
└── docs/                     ← Cloudflare Pages deploy root
    ├── topics/                ← topics/ থেকে generated copy
    ├── topics-index.json      ← generated search index
    ├── recent-changes.json    ← generated changes feed
    ├── sw.js                  ← generated service worker
    └── version.json           ← generated version (footer-এ দেখানো হয়)
```

**গুরুত্বপূর্ণ (v1.0.0-এর পর যোগ হয়েছে):** যেকোনো কনটেন্ট-আপডেট কাজ শুরু করার আগে Claude অবশ্যই `EDITORIAL_MEMORY.md` পড়বে — সেখানে ব্যবহারকারীর আগের সিদ্ধান্ত থেকে জমা হওয়া ফরম্যাট/স্টাইল/কাঠামো-নিয়ম থাকে। নতুন কোনো স্থায়ী-যোগ্য সিদ্ধান্ত এলে Claude নিজে থেকেই সেখানে যোগ করে, কাজ শেষে ব্যবহারকারীকে জানিয়ে দেয়।

`topics/` হাতে edit করার source। `docs/topics/`, `docs/topics-index.json`, `docs/recent-changes.json`, `docs/sw.js` ও `docs/version.json` build output—এগুলো হাতে edit করা উচিত নয়।

`archive/` website runtime-এ ব্যবহৃত হয় না; এটি source verification ও reference-এর জন্য রাখা হয়।

## ৩. Build flow

`python3 scripts/build_index.py` চালালে:

1. `topics/*.md` frontmatter ও section structure validate হয়।
2. valid topic files `docs/topics/`-এ কপি হয়।
3. `docs/topics-index.json` search-এর জন্য তৈরি হয়।
4. `docs/recent-changes.json` history table থেকে তৈরি হয়।
5. `scripts/sw_template.js` থেকে VERSION বসিয়ে `docs/sw.js` তৈরি হয়।
6. `VERSION` থেকে `docs/version.json` তৈরি হয় — ওয়েবসাইটের ফুটারে ভার্সন নম্বর দেখাতে ব্যবহৃত হয়।

Validation ব্যর্থ হলে build non-zero exit করে এবং generated output লেখার আগেই থামে।

## ৪. Deployment

Cloudflare Pages-এর output directory `docs`। তাই `docs/` path বদলালে Cloudflare configuration-ও বদলাতে হবে। GitHub Action সক্রিয় থাকলে push-এর পর build script চালিয়ে generated output commit বা deploy-এর জন্য প্রস্তুত করবে। Workflow-এর actual behavior যাচাই না করে generated output fresh হয়েছে ধরে নেওয়া যাবে না।

## ৫. নিরাপত্তা ও রক্ষণাবেক্ষণ

- Markdown rendering-এর আগে sanitizer ব্যবহার করতে হবে।
- Topic filename lowercase slug format-এ রাখতে হবে।
- `title`, `tags` ও `last_updated` frontmatter valid রাখতে হবে।
- নতুন topic যোগ বা পুরনো topic বদলানোর পর build চালাতে হবে।
- বড় system change-এর পর `TEST_CHECKLIST.md` অনুসরণ করতে হবে।

## ৬. বর্তমান scope

এই project-এর website এখন search ও topic-reading-কেন্দ্রিক। Quiz/MCQ data, quiz UI, quiz build pipeline এবং আলাদা revision workflow এই scope-এর অংশ নয়। পুরনো পরিবর্তনের ইতিহাস `CHANGELOG.md`-এ historical record হিসেবে থাকতে পারে, কিন্তু নতুন runtime বা maintenance নির্দেশনা হিসেবে ব্যবহার করা যাবে না।

## ৭. ভবিষ্যৎ পরিকল্পনা (Roadmap)

**`topics/` স্কেলিং:** টপিক সংখ্যা যখন অনেক বেড়ে যাবে (কয়েকশো ছাড়িয়ে যাওয়ার পর থেকেই বিবেচনা করা উচিত), তখন নিচের দুইটা পরিবর্তন দরকার হবে:

1. **সাব-ফোল্ডার কাঠামো:** `topics/` ও `docs/topics/`-কে বছর/মাস অনুযায়ী সাব-ফোল্ডারে ভাগ করা (যেমন `topics/2026/07/`) — একটা ফ্ল্যাট ফোল্ডারে হাজার হাজার ফাইল থাকলে GitHub-এর ওয়েব ইন্টারফেসে ব্রাউজ করা কঠিন হয়ে যায়। এতে `scripts/build_index.py`-এ ফাইল খোঁজার লজিক আপডেট করতে হবে।
2. **সার্চ/ফিল্টার UX:** `docs/index.html`-এ বর্তমান সার্চের পাশাপাশি ক্যাটাগরি বা ট্যাগ অনুযায়ী ফিল্টার/pagination যোগ করা, যাতে বড় তালিকায় নির্দিষ্ট টপিক খুঁজে পাওয়া সহজ থাকে।

কারিগরিভাবে (repo সাইজ, GitHub সীমা, ওয়েবসাইট লোডিং স্পিড) ৫,০০০+ টপিক ফাইলেও কোনো সমস্যা হবে না — এই দুইটা পরিবর্তন শুধু ব্যবহারযোগ্যতার (usability) জন্য দরকার হবে, জরুরি কোনো ভাঙন এড়ানোর জন্য নয়।
