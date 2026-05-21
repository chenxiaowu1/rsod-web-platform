<template>
  <div class="register-container">
    <div class="register-bg"></div>

    <div class="register-card">
      <div class="register-header">
        <div class="logo-icon">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </div>
        <h1 class="register-title">创建账号</h1>
        <p class="register-subtitle">加入遥感目标检测平台</p>
      </div>

      <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" class="register-form">
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" placeholder="用户名" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="registerForm.email" type="email" placeholder="邮箱地址" size="large">
            <template #prefix><el-icon><Message /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="密码" size="large">
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" size="large">
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <div class="agree-row">
          <el-checkbox v-model="registerForm.agree" />
          <span>我已阅读并同意服务条款和隐私政策</span>
        </div>

        <el-button type="primary" size="large" class="register-btn" @click="handleRegister">注 册</el-button>
      </el-form>

      <div class="login-link">已有账号？<router-link to="/login">立即登录</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { ElMessage } from "element-plus";
import { User, Message, Lock } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { registerUser, loginUser } from "../utils/auth";

const router = useRouter();
const registerForm = reactive({ username: "", email: "", password: "", confirmPassword: "", agree: false });
const registerFormRef = ref(null);

const registerRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }, { min: 3, max: 20, message: "3-20 个字符", trigger: "blur" }],
  email: [{ required: true, message: "请输入邮箱", trigger: "blur" }, { type: "email", message: "邮箱格式不正确", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }, { min: 6, max: 30, message: "6-30 个字符", trigger: "blur" }],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    { validator: (_, v, cb) => v !== registerForm.password ? cb(new Error("两次密码不一致")) : cb(), trigger: "blur" },
  ],
  agree: [{ validator: (_, v, cb) => !v ? cb(new Error("请勾选同意")) : cb(), trigger: "change" }],
};

const handleRegister = () => {
  registerFormRef.value.validate((valid) => {
    if (valid) {
      const result = registerUser(registerForm.username, registerForm.email, registerForm.password);
      if (result.success) {
        ElMessage.success("注册成功，正在登录...");
        loginUser(registerForm.username, registerForm.password);
        router.push("/detection");
      } else {
        ElMessage.error(result.message);
      }
    }
  });
};
</script>

<style scoped>
.register-container {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg-deep); position: relative; overflow: hidden;
}
.register-bg {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 60% 40%, rgba(0, 230, 118, 0.05) 0%, transparent 60%),
              radial-gradient(ellipse at 30% 60%, rgba(0, 184, 212, 0.04) 0%, transparent 50%);
  pointer-events: none;
}
.register-card {
  width: 100%; max-width: 420px; padding: 40px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); position: relative; z-index: 1;
}
.register-header { text-align: center; margin-bottom: 32px; }
.logo-icon {
  width: 60px; height: 60px; margin: 0 auto 18px;
  background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
  border-radius: 14px; display: flex; align-items: center; justify-content: center;
  color: var(--on-accent); box-shadow: 0 4px 16px var(--accent-glow);
}
.register-title { font-size: 24px; font-weight: 700; color: var(--text-primary); letter-spacing: 0.5px; margin-bottom: 6px; }
.register-subtitle { font-size: 13px; color: var(--text-muted); }
.register-form { margin-bottom: 20px; }
.agree-row { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--text-muted); margin-bottom: 20px; }
.agree-row a { color: var(--accent); text-decoration: none; }
.register-btn { width: 100%; height: 46px; border-radius: var(--radius-md); font-size: 15px; letter-spacing: 2px; }
.login-link { text-align: center; font-size: 13px; color: var(--text-muted); }
.login-link a { color: var(--accent); text-decoration: none; margin-left: 4px; }
</style>
