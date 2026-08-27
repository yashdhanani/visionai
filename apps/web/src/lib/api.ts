import axios from "axios";

// NEXT_PUBLIC_API_URL is set via Vercel env vars.
// Fallback to Render production URL if not set (covers all preview/branch deployments).
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://visionai-236r.onrender.com";

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

let _refreshing = false;

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && !_refreshing) {
      original._retry = true;
      _refreshing = true;
      try {
        const resp = await axios.post(`${API_BASE}/api/v1/auth/refresh`, null, {
          withCredentials: true,
        });
        const newToken = resp.data.data?.access_token;
        if (newToken) {
          localStorage.setItem("access_token", newToken);
          original.headers.Authorization = `Bearer ${newToken}`;
          _refreshing = false;
          return api(original);
        }
      } catch {
        localStorage.removeItem("access_token");
        if (typeof window !== "undefined") {
          // eslint-disable-next-line @next/next/no-location-assign-relative-destination
          window.location.href = "/login";
        }
      }
      _refreshing = false;
    }
    return Promise.reject(error);
  }
);

export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  meta: { request_id: string };
  error?: { code: string; message: string };
}

export function getWsUrl(): string {
  const base = API_BASE.replace(/^http/, "ws");
  return base;
}