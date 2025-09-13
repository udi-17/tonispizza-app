const CACHE_NAME = 'tonis-pizza-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192x192.PNG.png',
  '/icon-512x512.PNG.png'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Activate event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Push notification event
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'הזמנה חדשה מחכה לך!',
    icon: '/icon-192x192.PNG.png',
    badge: '/icon-72x72.PNG.png',
    dir: 'rtl',
    lang: 'he',
    tag: 'pizza-notification',
    requireInteraction: true,
    actions: [
      {
        action: 'view',
        title: 'צפייה',
        icon: '/icon-96x96.PNG.png'
      },
      {
        action: 'close',
        title: 'סגירה'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('פיצה טוני\'ס', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});