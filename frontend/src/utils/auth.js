/**
 * JWT 认证模块 — 对接后端 /api/auth/*
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

function authApi(url, data) {
  return axios.post(API_BASE + url, data).then((r) => r.data);
}

export async function loginUser(identifier, password) {
  try {
    const res = await authApi("/auth/login", { account: identifier, password });
    if (res.success && res.data.access_token) {
      localStorage.setItem("rsod-access-token", res.data.access_token);
      localStorage.setItem("rsod-refresh-token", res.data.refresh_token);
      localStorage.setItem("rsod-user", JSON.stringify(res.data.user));
      return { success: true, user: res.data.user };
    }
    return { success: false, message: res.message || "登录失败" };
  } catch (err) {
    return { success: false, message: err.response?.data?.detail || "登录失败" };
  }
}

export async function registerUser(username, email, password) {
  try {
    const res = await authApi("/auth/register", { username, email, password });
    return { success: res.success, message: res.message };
  } catch (err) {
    return { success: false, message: err.response?.data?.detail || "注册失败" };
  }
}

export function logoutUser() {
  localStorage.removeItem("rsod-access-token");
  localStorage.removeItem("rsod-refresh-token");
  localStorage.removeItem("rsod-user");
}

export function getToken() {
  return localStorage.getItem("rsod-access-token");
}

export function getRefreshToken() {
  return localStorage.getItem("rsod-refresh-token");
}

export function getSession() {
  try {
    const user = JSON.parse(localStorage.getItem("rsod-user"));
    const token = localStorage.getItem("rsod-access-token");
    return token && user ? { ...user, token } : null;
  } catch {
    return null;
  }
}
