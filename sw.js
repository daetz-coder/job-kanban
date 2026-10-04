/* Job Kanban — service worker
 *
 * 目的：让「在线版」可以安装成应用并离线使用。
 * 策略：
 *   - 应用外壳（页面 / manifest / 图标）走 cache-first
 *   - /api/ 请求一律不缓存（数据必须实时）
 *   - 离线且缓存未命中时，回退到缓存的看板页面
 *
 * 升级界面后请同步改 CACHE 版本号，旧缓存会在 activate 时清掉。
 */
const CACHE = 'job-kanban-v1';

const SHELL = [
  './',
  './index.html',
  './dashboard.html',
  './manifest.webmanifest',
  './docs/icons/favicon-32.png',
  './docs/icons/icon-192.png',
  './docs/icons/icon-512.png',
  './docs/icons/icon-maskable-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => c.addAll(SHELL).catch(() => {}))   // 个别资源缺失不阻塞安装
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;      // 外链交给浏览器
  if (url.pathname.indexOf('/api/') >= 0) return;       // 数据接口绝不缓存

  e.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => caches.match('./dashboard.html').then((p) => p || caches.match('./')));
    })
  );
});
