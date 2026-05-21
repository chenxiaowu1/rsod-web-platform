<template>
  <div class="login-container">
    <div class="login-bg"></div>

    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="12" r="3"/>
            <line x1="12" y1="2" x2="12" y2="9"/>
            <line x1="12" y1="15" x2="12" y2="22"/>
          </svg>
        </div>
        <h1 class="login-title">遥感目标检测平台</h1>
        <p class="login-subtitle">遥感目标智能检测平台</p>
      </div>

      <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" placeholder="用户名" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" @keydown.enter="handleLogin">
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <div class="form-row">
          <el-checkbox v-model="loginForm.remember" class="remember-check">记住我</el-checkbox>
          <router-link to="/forgot-password" class="forgot-link">忘记密码?</router-link>
        </div>

        <el-button type="primary" size="large" class="login-btn" @click="handleLogin">登 录</el-button>
      </el-form>

      <div class="register-link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { ElMessage } from "element-plus";
import { User, Lock } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { loginUser, getSession } from "../utils/auth";

const router = useRouter();

// 已登录则跳过
if (getSession()) {
  router.replace("/detection");
}

const loginForm = reactive({ username: "", password: "", remember: false });
const loginFormRef = ref(null);

const loginRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const handleLogin = () => {
  loginFormRef.value.validate((valid) => {
    if (valid) {
      const result = loginUser(loginForm.username, loginForm.password);
      if (result.success) {
        ElMessage.success(`欢迎回来，${result.user.username}`);
        router.push("/detection");
      } else {
        ElMessage.error(result.message);
      }
    }
  });
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-deep);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 50%, rgba(0, 230, 118, 0.06) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 30%, rgba(0, 184, 212, 0.04) 0%, transparent 50%);
  pointer-events: none;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 44px 40px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 18px;
  background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--on-accent);
  box-shadow: 0 4px 16px var(--accent-glow);
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.login-subtitle {
  font-size: 13px;
  color: var(--text-muted);
}

.login-form {
  margin-bottom: 24px;
}

.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.forgot-link {
  font-size: 13px;
  color: var(--accent);
  text-decoration: none;
  transition: opacity 0.2s;
}
.forgot-link:hover { opacity: 0.8; }

.login-btn {
  width: 100%;
  height: 46px;
  border-radius: var(--radius-md);
  font-size: 15px;
  letter-spacing: 2px;
}

.register-link {
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}
.register-link a {
  color: var(--accent);
  text-decoration: none;
  margin-left: 4px;
}
.register-link a:hover { opacity: 0.8; }
</style>
