// JobArchive service worker — অফলাইনেও আগে দেখা টপিক পড়া যাবে।
// CACHE_NAME নিচে বিল্ড-স্ক্রিপ্ট স্বয়ংক্রিয়ভাবে VERSION ফাইল থেকে বসিয়ে দেয়।
// তাই VERSION বাড়লেই পুরনো ক্যাশ বাতিল হয়ে সবার জন্য নতুন ভার্সন লোড হয় —
// এই ফাইলে হাতে কিছু বদলানোর দরকার নেই।
const CACHE_NAME = "jobarchive-cache-1.1.0";

const APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./vendor/marked.min.js",
  "./vendor/purify.min.js",
  // TASK 4: ইনডেক্স ফাইলগুলোও ইনস্টল-টাইমে ক্যাশ করা হয়, যাতে প্রথমবার
  // অফলাইনে গেলেও (একবারও এই নির্দিষ্ট ফাইল না খুলে থাকলেও) তালিকা,
  // সাম্প্রতিক-পরিবর্তন মোড কাজ করে।
  "./topics-index.json",
  "./recent-changes.json",
  "./version.json",
];

// ইনস্টলের সময় মূল অ্যাপ-শেল ক্যাশ করে রাখা
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// পুরনো ক্যাশ পরিষ্কার করা
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    )
  );
  self.clients.claim();
});

// ফেচ-স্ট্র্যাটেজি:
// - topics-index.json, recent-changes.json, version.json ও topics/*.md (কনটেন্ট):
//   আগে নেটওয়ার্ক থেকে চেষ্টা, অফলাইন হলে ক্যাশ থেকে দেখানো — যাতে নতুন তথ্য
//   (ভার্সন নম্বর সহ) থাকলে সেটাই আগে দেখা যায়, পুরনো ক্যাশড ভার্সন আটকে না থাকে।
// - বাকি সব (অ্যাপ-শেল): আগে ক্যাশ থেকে দেখানো, দ্রুত লোডের জন্য।
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isContent =
    url.pathname.endsWith("topics-index.json") ||
    url.pathname.endsWith("recent-changes.json") ||
    url.pathname.endsWith("version.json") ||
    url.pathname.includes("/topics/");

  if (isContent) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // TASK 3: শুধু সফল (2xx) রেসপন্সই ক্যাশ হয় — 404/500 কখনো ক্যাশ হয় না,
          // আর কখনোই একটা ভালো/আগের ক্যাশড ফাইলকে ব্যর্থ রেসপন্স দিয়ে ওভাররাইট করা হয় না।
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((response) => {
          // এখানেও একই নিয়ম: শুধু সফল রেসপন্সই ক্যাশে যোগ হয়।
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        });
      })
    );
  }
});
