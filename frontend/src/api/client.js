/**
 * Single source of truth for talking to the Querynetic backend.
 *
 * Job: every API call, request shape, and auth header lives here — no
 * other component should construct a fetch() call directly.
 *
 * Token strategy:
 * - Access token: short-lived, kept in localStorage, sent as a normal
 *   Authorization header (attached automatically below).
 * - Refresh token: long-lived, lives ONLY in an HttpOnly cookie the
 *   browser manages — this file never reads or stores it directly.
 *   withCredentials: true is what makes the browser actually attach that
 *   cookie on requests to the backend.
 */

import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";
const ACCESS_TOKEN_KEY = "querynetic_token";

const client = axios.create({ baseURL: API_BASE, withCredentials: true });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- 401 handling: refresh once, retry, and never loop forever ---
//
// If several requests fail with 401 at the same moment, only the FIRST
// one triggers a real refresh call — the rest wait for that same result
// (isRefreshing + failedQueue) instead of each firing their own refresh.
let isRefreshing = false;
let failedQueue = [];

function processQueue(error, newToken) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(newToken);
  });
  failedQueue = [];
}

function goToLogin() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthEndpoint =
      originalRequest?.url?.includes("/api/auth/refresh") ||
      originalRequest?.url?.includes("/api/auth/login");

    // originalRequest._retry marks a request that's ALREADY been retried
    // once after a refresh — if it fails again, don't refresh again, just
    // give up. This is what stops an infinite refresh loop.
    if (error.response?.status !== 401 || isAuthEndpoint || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // A refresh is already in flight — queue this request instead of
      // triggering a second, redundant refresh call.
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((newToken) => {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return client(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const { data } = await client.post("/api/auth/refresh");
      const newAccessToken = data.access_token;
      localStorage.setItem(ACCESS_TOKEN_KEY, newAccessToken);
      processQueue(null, newAccessToken);
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return client(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      goToLogin();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export async function register(email, password) {
  const res = await client.post("/api/auth/register", { email, password });
  return res.data;
}

export async function login(email, password) {
  const res = await client.post("/api/auth/login", { email, password });
  localStorage.setItem(ACCESS_TOKEN_KEY, res.data.access_token);
  return res.data;
}

export async function logout() {
  try {
    await client.post("/api/auth/logout");
  } finally {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem(ACCESS_TOKEN_KEY));
}

export async function askQuestion(question, conversationId) {
  const res = await client.post("/api/chat/", {
    question,
    conversation_id: conversationId,
  });
  return res.data;
}

export async function createConversation(databaseId) {
  const res = await client.post("/api/conversations/", { database_id: databaseId });
  return res.data;
}

export async function listConversations() {
  const res = await client.get("/api/conversations/");
  return res.data;
}

export async function getConversationMessages(conversationId) {
  const res = await client.get(`/api/conversations/${conversationId}/messages`);
  return res.data;
}

export async function deleteConversation(conversationId) {
  await client.delete(`/api/conversations/${conversationId}`);
}

export async function connectDatabase(name, connectionString) {
  const res = await client.post("/api/databases/", {
    name,
    connection_string: connectionString,
  });
  return res.data;
}

export async function listDatabases() {
  const res = await client.get("/api/databases/");
  return res.data;
}