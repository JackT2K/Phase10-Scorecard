const CACHE='p10-shell-css-v2';
const SHELL=['/static/css/app.css','/static/css/tv.css','/offline','/static/icons/p10-192.png','/static/icons/p10-512.png'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  const url=new URL(event.request.url);
  if(url.origin!==location.origin) return;
  if(event.request.mode==='navigate'){
    event.respondWith(fetch(event.request).then(response=>{const copy=response.clone();caches.open(CACHE).then(c=>c.put(event.request,copy));return response}).catch(()=>caches.match(event.request).then(r=>r||caches.match('/offline'))));
    return;
  }
  event.respondWith(caches.match(event.request).then(cached=>cached||fetch(event.request).then(response=>{if(response.ok && (url.pathname.startsWith('/static/')||url.pathname==='/manifest.webmanifest')){const copy=response.clone();caches.open(CACHE).then(c=>c.put(event.request,copy))}return response})));
});
