/**
 * Service Worker for Trio Monitor
 * Provides offline support and caching for better performance
 */

const CACHE_NAME = 'trio-monitor-v1.0.0';
const STATIC_CACHE_NAME = 'trio-monitor-static-v1.0.0';
const API_CACHE_NAME = 'trio-monitor-api-v1.0.0';

// Files to cache for offline support
const STATIC_FILES = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json',
  '/favicon.ico'
];

// API endpoints to cache (with short TTL)
const API_ENDPOINTS = [
  '/api/health',
  '/api/stats'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static files
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        console.log('Caching static files');
        return cache.addAll(STATIC_FILES);
      }),
      // Cache API endpoints
      caches.open(API_CACHE_NAME).then((cache) => {
        console.log('Pre-caching API endpoints');
        return Promise.all(
          API_ENDPOINTS.map(url => 
            fetch(url).then(response => {
              if (response.ok) {
                return cache.put(url, response);
              }
            }).catch(() => {
              // Ignore errors during pre-caching
              console.log(`Failed to pre-cache ${url}`);
            })
          )
        );
      })
    ]).then(() => {
      // Force activation of new service worker
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== API_CACHE_NAME &&
                cacheName !== CACHE_NAME) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // Take control of all pages
      self.clients.claim()
    ])
  );
});

// Fetch event - handle requests with caching strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle different types of requests
  if (url.pathname.startsWith('/api/')) {
    // API requests - Network First with fallback to cache
    event.respondWith(handleApiRequest(request));
  } else if (url.pathname.startsWith('/static/') || 
             url.pathname === '/' || 
             url.pathname === '/admin') {
    // Static files - Cache First
    event.respondWith(handleStaticRequest(request));
  } else {
    // Other requests - Network Only
    event.respondWith(fetch(request));
  }
});

// Handle API requests with Network First strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful responses (except for real-time data)
      if (!url.pathname.includes('/dashboard') && 
          !url.pathname.includes('/agents') && 
          !url.pathname.includes('/queues')) {
        const cache = await caches.open(API_CACHE_NAME);
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    }
    
    // If network fails, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('Serving API request from cache:', request.url);
      return cachedResponse;
    }
    
    // Return network response even if not ok
    return networkResponse;
    
  } catch (error) {
    console.log('Network failed, trying cache for:', request.url);
    
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline response for critical endpoints
    if (url.pathname === '/api/health') {
      return new Response(
        JSON.stringify({ 
          status: 'offline', 
          message: 'Service Worker: Offline mode' 
        }),
        { 
          headers: { 'Content-Type': 'application/json' },
          status: 503
        }
      );
    }
    
    throw error;
  }
}

// Handle static requests with Cache First strategy
async function handleStaticRequest(request) {
  try {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // If not in cache, fetch from network
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache the response
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
    
  } catch (error) {
    // If both cache and network fail, return offline page
    if (request.destination === 'document') {
      return new Response(
        `
        <!DOCTYPE html>
        <html>
        <head>
          <title>Trio Monitor - Offline</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .offline-message { max-width: 500px; margin: 0 auto; }
            .btn { background: #007bff; color: white; padding: 10px 20px; 
                   text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }
          </style>
        </head>
        <body>
          <div class="offline-message">
            <h1>🔌 Offline</h1>
            <p>Du är för närvarande offline. Trio Monitor kräver en internetanslutning för att fungera.</p>
            <p>Kontrollera din anslutning och försök igen.</p>
            <a href="/" class="btn" onclick="window.location.reload()">Försök igen</a>
          </div>
        </body>
        </html>
        `,
        { 
          headers: { 'Content-Type': 'text/html' },
          status: 503
        }
      );
    }
    
    throw error;
  }
}

// Handle background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  try {
    // Sync any offline actions when connection is restored
    console.log('Performing background sync...');
    
    // Example: retry failed API calls
    // This would be implemented based on specific needs
    
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Handle push notifications (if needed in future)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    
    const options = {
      body: data.body || 'Ny uppdatering från Trio Monitor',
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: 'trio-monitor-notification',
      requireInteraction: data.requireInteraction || false,
      actions: data.actions || []
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'Trio Monitor', options)
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});

console.log('Service Worker loaded successfully');
