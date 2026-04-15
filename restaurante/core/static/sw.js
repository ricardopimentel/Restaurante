const CACHE_NAME = 'restaurante-ifto-v1';
const urlsToCache = [
  '/restaurante/',
  '/restaurante/acesso/login/',
  '/restaurante/static/css/style.css',
  '/restaurante/static/images/pwa-icon-512.png',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
