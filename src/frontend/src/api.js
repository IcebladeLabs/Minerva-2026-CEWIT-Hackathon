const BASE = "/api";

function getToken() { return localStorage.getItem("token"); }
function setToken(t) { localStorage.setItem("token", t); }
function clearToken() { localStorage.removeItem("token"); }

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(BASE + path, {
    method, headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

export const api = {
  getToken, setToken, clearToken,
  get:  (p)    => request("GET", p),
  post: (p, b) => request("POST", p, b),
  put:  (p, b) => request("PUT", p, b),
  del:  (p)    => request("DELETE", p),

  streamUrl: (feedId) => `${BASE}/feeds/${feedId}/stream`,

  async signup(username, email, password) {
    const data = await request("POST", "/signup", { username, email, password });
    setToken(data.token);
    return data;
  },
  async login(username, password) {
    const data = await request("POST", "/login", { username, password });
    setToken(data.token);
    return data;
  },
  logout() { clearToken(); window.location.reload(); },
  isLoggedIn() { return !!getToken(); },
};
