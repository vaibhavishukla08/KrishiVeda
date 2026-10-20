// Thin wrapper around fetch for the KrishiVeda backend.
// All requests go to /api/... (proxied to FastAPI in development).

const BASE = import.meta.env.VITE_API_URL || "";

export class ApiError extends Error {
  constructor(message, { status, code, details } = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(path, { method = "GET", body, query, form, headers } = {}) {
  const url = new URL(BASE + path, window.location.origin);
  Object.entries(query || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });
  const init = { method, headers: { ...headers } };
  if (form) init.body = form;
  else if (body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(url, init);
  } catch {
    throw new ApiError("Cannot reach the KrishiVeda server. Is the backend running?", { code: "NETWORK_ERROR" });
  }
  const data = await res.json().catch(() => null);
  // 502/504 without our JSON error body = the dev proxy could not reach the backend
  if ((res.status === 502 || res.status === 504) && !data?.error) {
    throw new ApiError(
      "The KrishiVeda backend server is not running. Start it with start-krishiveda.bat (keep its window open), then try again.",
      { status: res.status, code: "BACKEND_DOWN" }
    );
  }
  if (!res.ok) {
    const err = data?.error || {};
    throw new ApiError(err.message || `Request failed (${res.status})`, { status: res.status, code: err.code, details: err.details });
  }
  return data;
}

export const api = {
  health: () => request("/api/health"),

  createFarmer: (body) => request("/api/farmers", { method: "POST", body }),
  updateFarmer: (id, body) => request(`/api/farmers/${id}`, { method: "PUT", body }),
  getFarmer: (id) => request(`/api/farmers/${id}`),
  history: (id, limit = 20) => request(`/api/farmers/${id}/history`, { query: { limit } }),
  stats: (id, days = 30) => request(`/api/farmers/${id}/stats`, { query: { days } }),

  diseaseModel: () => request("/api/disease/model"),
  predictDisease: (file, farmerId) => {
    const form = new FormData();
    form.append("file", file);
    if (farmerId) form.append("farmer_id", farmerId);
    return request("/api/disease/predict", { method: "POST", form });
  },

  cropModel: () => request("/api/crops/model"),
  recommendCrop: (body) => request("/api/crops/recommend", { method: "POST", body }),

  weather: (query) => request("/api/weather", { query }),
  irrigation: (query) => request("/api/irrigation/advice", { query }),

  marketPrices: (query) => request("/api/market-prices", { query }),
  commodities: () => request("/api/market-prices/commodities"),

  advisoryStatus: () => request("/api/advisory/status"),
  ask: (body) => request("/api/advisory/ask", { method: "POST", body }),

  // Ask a human expert
  expertContacts: () => request("/api/expert/contacts"),
  askExpert: (body) => request("/api/expert/questions", { method: "POST", body }),
  myExpertQuestions: (farmerId) => request("/api/expert/questions", { query: { farmer_id: farmerId } }),
  // Expert Panel (the access code is sent as a header, never in the URL)
  expertVerify: (code) => request("/api/expert/verify", { headers: { "X-Expert-Code": code } }),
  expertInbox: (code, status) => request("/api/expert/inbox", { query: { status }, headers: { "X-Expert-Code": code } }),
  expertAnswer: (code, id, body) =>
    request(`/api/expert/questions/${id}/answer`, { method: "POST", body, headers: { "X-Expert-Code": code } }),

  schemes: () => request("/api/resources/schemes"),
  stubble: () => request("/api/resources/stubble"),
};
