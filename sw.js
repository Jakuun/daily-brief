// Minimal offline cache for the Daily Brief app shell.
// Data (briefs.js) is network-first so new issues show; shell is cache-first.
const SHELL = 'db-shell-v1';
const SHELL_FILES = ['./', './index.html', './icon.svg', './manifest.webmanifest'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.pathname.endsWith('briefs.js')) {
    // network-first for fresh content, fall back to cache offline
    e.respondWith(
      fetch(e.request).then(r => {
        const copy = r.clone(); caches.open(SHELL).then(c => c.put(e.request, copy)); return r;
      }).catch(() => caches.match(e.request))
    );
    return;
  }
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
