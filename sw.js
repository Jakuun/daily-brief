// Daily Brief service worker.
// Code, data and articles are NETWORK-FIRST and bypass the HTTP cache (cache:'reload'),
// so when online you always get the latest. Icons/manifest are cache-first.
// Cache fallback is used only when offline. Bump SHELL to force clients onto new code.
const SHELL = 'db-shell-v4';
const SHELL_FILES = ['./', './index.html', './icon.svg', './manifest.webmanifest'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  const url = new URL(req.url);
  const netFirst = req.mode === 'navigate'
    || url.pathname.endsWith('index.html')
    || url.pathname.endsWith('briefs.js')
    || url.pathname.includes('/articles/');
  if (netFirst) {
    e.respondWith(
      fetch(req, { cache: 'reload' })                 // force network, skip HTTP cache
        .then(r => { const c = r.clone(); caches.open(SHELL).then(x => x.put(req, c)); return r; })
        .catch(() => caches.match(req).then(m => m || caches.match('./index.html')))
    );
    return;
  }
  e.respondWith(caches.match(req).then(r => r || fetch(req)));
});
