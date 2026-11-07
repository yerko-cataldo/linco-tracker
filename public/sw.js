// Service worker de Lincoyán: solo muestra las notificaciones push (no guarda nada en caché).
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("push", (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch { d = { body: e.data ? e.data.text() : "" }; }
  e.waitUntil(self.registration.showNotification(d.title || "Lincoyán", {
    body: d.body || "",
    tag: d.tag,
    renotify: !!d.tag,
    icon: "/img/icono-192.png",
    data: { url: d.url || "/" },
  }));
});

// Al tocar la notificación: abre la app en la pestaña indicada (?tab=…) o la trae al frente si ya está abierta
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = new URL(e.notification.data?.url || "/", self.location.origin);
  e.waitUntil((async () => {
    const wins = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    const win = wins.find((w) => new URL(w.url).origin === url.origin);
    if (!win) return self.clients.openWindow(url.href);
    await win.focus();
    win.postMessage({ tab: url.searchParams.get("tab") });
  })());
});
