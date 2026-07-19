# TEST_CHECKLIST

কোনো বড় পরিবর্তনের পর deploy করার আগে/পরে এই তালিকা ধরে ৫–১০ মিনিটে যাচাই করো।

## Build

- [ ] `python3 scripts/build_index.py` exit code 0 দিয়ে শেষ হয়।
- [ ] ভুল frontmatter দিয়ে test করলে build non-zero exit দেয়।
- [ ] `docs/topics/`-এ `topics/`-এর সব topic আছে।
- [ ] `docs/topics-index.json`-এর topic count source topic count-এর সঙ্গে মেলে।
- [ ] `docs/sw.js`-এর CACHE_NAME-এ `VERSION`-এর সংখ্যা বসেছে।
- [ ] `docs/version.json`-এর ভার্সন `VERSION` ফাইলের সংখ্যার সাথে মেলে।
- [ ] `docs/mcq-index.json` বা কোনো quiz output তৈরি হয় না।
- [ ] repo-তে `mcq/` বা `revision/` নামে কোনো ফোল্ডার অবশিষ্ট নেই।
- [ ] `scripts/__pycache__/` বা অন্য কোনো `*.pyc` ফাইল কমিট হয়নি।

## Website

- [ ] Homepage লোড হয় এবং topic list দেখা যায়।
- [ ] Search title, tags ও full text-এ কাজ করে।
- [ ] Topic খুললে Markdown ঠিকভাবে render হয়।
- [ ] URL hash-এ topic slug বসে এবং shareable link কাজ করে।
- [ ] আজকের রিভিশন, মাস অনুযায়ী view, সাম্প্রতিক পরিবর্তন ও dashboard লোড হয়।
- [ ] Dashboard-এ topic count, tag coverage, oldest topics ও reading progress দেখা যায়।
- [ ] Quiz button বা quiz screen নেই।

## Mobile ও error handling

- [ ] Mobile view-তে topic খুলে তালিকায় ফেরা যায়।
- [ ] Topic খোলা অবস্থায় search ও tag click করলে তালিকা ঠিক থাকে।
- [ ] Browser Back চাপলে article view থেকে তালিকায় ফেরা যায়।
- [ ] না-থাকা slug দিলে পরিষ্কার error দেখায়।
- [ ] Sanitizer-এর কারণে topic content-এ HTML event handler চালু হয় না।

## Offline / PWA

- [ ] একবার site visit করার পর offline reload-এ app shell খোলে।
- [ ] আগে দেখা topic offline-এ খোলা যায়।
- [ ] Service worker install-এর সময় কোনো না-থাকা file cache করতে যায় না।
- [ ] PWA icon ও Add to Home Screen কাজ করে।

## Theme ও version

- [ ] Dark mode কাজ করে এবং preference মনে থাকে।
- [ ] VERSION বাড়িয়ে rebuild করলে নতুন service-worker cache তৈরি হয়।
- [ ] Footer-এ সংস্করণ নম্বর দেখা যায় এবং সেটা `VERSION` ফাইলের সংখ্যার সাথে মেলে।
- [ ] `docs/version.json` না থাকলে/লোড ব্যর্থ হলেও পাতা ভাঙে না (footer-এ ভার্সন অংশ চুপচাপ বাদ পড়ে)।
