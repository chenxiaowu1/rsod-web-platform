/**
 * JWT 认证模块 — 对接后端 /api/auth/*
 * 统一管理 token 生命周期、刷新、注销、状态同步
 */

import { ref } from "vue";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

// ── 响应式认证触发器 — Header / 页面 watch 此值 ──
export const authVersion = ref(0);

/** 触发所有依赖 authVersion 的 computed 重新计算 */
export function refreshAuth() {
  authVersion.value++;
}

// ── 原始 localStorage 读写 ──

export function getToken() {
  return localStorage.getItem("rsod-access-token");
}

export function getRefreshToken() {
  return localStorage.getItem("rsod-refresh-token");
}

export function getSession() {
  try {
    const user = JSON.parse(localStorage.getItem("rsod-user"));
    const token = getToken();
    return token && user ? { ...user, token } : null;
  } catch {
    return null;
  }
}

// ── 统一清除认证状态（清 localStorage + 刷新 UI）──

export function clearAuthState() {
  localStorage.removeItem("rsod-access-token");
  localStorage.removeItem("rsod-refresh-token");
  localStorage.removeItem("rsod-user");
  refreshAuth();
}

export function logoutUser() {
  clearAuthState();
}

// ── Access token 自动续签 ──

/** 用 refresh_token 尝试换取新 access_token；成功返回 true */
export async function tryRefreshAccessToken() {
  const rt = getRefreshToken();
  if (!rt) return false;
  try {
    const res = await axios.post(`${API_BASE}/auth/refresh`, {}, {
      headers: { Authorization: `Bearer ${rt}` },
    });
    if (res.data?.success && res.data?.data?.access_token) {
      localStorage.setItem("rsod-access-token", res.data.data.access_token);
      refreshAuth();
      return true;
    }
  } catch (e) { /* refresh 失败 */ }
  return false;
}

// ── 启动时校验登录态是否仍有效 ──

/** 调 /auth/me 验证当前 token 有效性；无效则自动 clearAuthState() */
export async function checkAuth() {
  const token = getToken();
  if (!token) return false;
  try {
    const res = await axios.get(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.data?.success) {
      localStorage.setItem("rsod-user", JSON.stringify(res.data.data));
      refreshAuth();
      return true;
    }
  } catch (e) {
    if (e.response?.status === 401) {
      // token 已过期，尝试 refresh
      const refreshed = await tryRefreshAccessToken();
      if (refreshed) return true;
    }
  }
  clearAuthState();
  return false;
}

// ── 登录 / 注册 ──

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
      refreshAuth();
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
