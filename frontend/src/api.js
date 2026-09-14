const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `${res.status} ${res.statusText}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  listDevices: () => request("/devices"),
  createDevice: (payload) => request("/devices", { method: "POST", body: JSON.stringify(payload) }),
  updateDevice: (id, payload) => request(`/devices/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteDevice: (id) => request(`/devices/${id}`, { method: "DELETE" }),
  testConnection: (id) => request(`/devices/${id}/test`, { method: "POST" }),

  getLatest: (id) => request(`/devices/${id}/latest`),
  getReadings: (id, limit = 100) => request(`/devices/${id}/readings?limit=${limit}`),
  getLogbook: (id, limit = 100) => request(`/devices/${id}/logbook?limit=${limit}`),

  writeSystemTime: (id) => request(`/devices/${id}/write/system-time`, { method: "POST" }),
  writeSensitivity: (id, payload) =>
    request(`/devices/${id}/write/sensitivity`, { method: "POST", body: JSON.stringify(payload) }),

  wsUrl: (id) => {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}/ws/devices/${id}`;
  },
};
