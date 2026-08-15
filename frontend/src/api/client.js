/**
 * Single source of truth for talking to the Querynetic backend.
 *
 * Job: every API call, request shape, and auth header lives here — no
 * other component should construct a fetch() call directly. Same reasoning
 * as core/ on the backend: one reusable building block, not duplicated
 * request logic scattered across components.
 */

import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

const client = axios.create({ baseURL: API_BASE });

// Attach the stored token to every request automatically, if one exists.
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("querynetic_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If ANY request comes back unauthorized (expired or invalid token), the
// stored token is stale — clear it and send the user back to login rather
// than letting the app sit in a broken, silently-failing state.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("querynetic_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export async function register(email, password) {
  const res = await client.post("/api/auth/register", { email, password });
  return res.data;
}

export async function login(email, password) {
  const res = await client.post("/api/auth/login", { email, password });
  localStorage.setItem("querynetic_token", res.data.access_token);
  return res.data;
}

export function logout() {
  localStorage.removeItem("querynetic_token");
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem("querynetic_token"));
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