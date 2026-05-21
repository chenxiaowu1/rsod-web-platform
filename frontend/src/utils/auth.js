/**
 * 本地账号系统（localStorage）
 * 默认管理员账号: admin / admin123
 */

const USERS_KEY = "rsod-users";
const SESSION_KEY = "rsod-session";

// 初始化默认账号
function initUsers() {
  if (!localStorage.getItem(USERS_KEY)) {
    const defaultUsers = [
      { username: "admin", email: "admin@rsod.cn", password: "admin123" },
    ];
    localStorage.setItem(USERS_KEY, JSON.stringify(defaultUsers));
  }
}

export function getUsers() {
  initUsers();
  return JSON.parse(localStorage.getItem(USERS_KEY));
}

export function findUser(username) {
  return getUsers().find((u) => u.username === username);
}

export function registerUser(username, email, password) {
  const users = getUsers();
  if (findUser(username)) {
    return { success: false, message: "用户名已存在" };
  }
  if (users.find((u) => u.email === email)) {
    return { success: false, message: "邮箱已注册" };
  }
  users.push({ username, email, password });
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
  return { success: true };
}

export function loginUser(username, password) {
  const user = findUser(username);
  if (!user) {
    return { success: false, message: "用户名不存在，请先注册" };
  }
  if (user.password !== password) {
    return { success: false, message: "密码错误" };
  }
  localStorage.setItem(SESSION_KEY, JSON.stringify({ username: user.username, email: user.email }));
  return { success: true, user: { username: user.username, email: user.email } };
}

export function logoutUser() {
  localStorage.removeItem(SESSION_KEY);
}

export function getSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY));
  } catch {
    return null;
  }
}
