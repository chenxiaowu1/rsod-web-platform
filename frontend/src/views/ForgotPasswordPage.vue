<template>
  <div class="forgot-container">
    <div class="forgot-bg"></div>

    <div class="forgot-card">
      <div class="forgot-header">
        <div class="logo-icon">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
          </svg>
        </div>
        <h1 class="forgot-title">找回密码</h1>
        <p class="forgot-subtitle">输入注册邮箱，发送重置链接</p>
      </div>

      <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules" class="forgot-form">
        <el-form-item prop="email">
          <el-input v-model="forgotForm.email" type="email" placeholder="注册邮箱" size="large">
            <template #prefix><el-icon><Message /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button type="primary" size="large" class="submit-btn" @click="handleSubmit">发送重置链接</el-button>
      </el-form>

      <div class="back-link"><router-link to="/login">返回登录</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { Message } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

const router = useRouter();
const forgotForm = reactive({ email: "" });
const forgotFormRef = ref(null);
const forgotRules = {
  email: [{ required: true, message: "请输入邮箱", trigger: "blur" }, { type: "email", message: "邮箱格式不正确", trigger: "blur" }],
};

const handleSubmit = () => {
  forgotFormRef.value.validate((valid) => {
    if (valid) {
      ElMessage.success("重置链接已发送");
      setTimeout(() => router.push("/login"), 1500);
    }
  });
};
</script>

<style scoped>
.forgot-container {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg-deep); position: relative; overflow: hidden;
}
.forgot-bg {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 50% 40%, rgba(0, 184, 212, 0.05) 0%, transparent 60%);
  pointer-events: none;
}
.forgot-card {
  width: 100%; max-width: 400px; padding: 40px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); position: relative; z-index: 1;
}
.forgot-header { text-align: center; margin-bottom: 32px; }
.logo-icon {
  width: 60px; height: 60px; margin: 0 auto 18px;
  background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
  border-radius: 14px; display: flex; align-items: center; justify-content: center;
  color: var(--on-accent); box-shadow: 0 4px 16px var(--accent-glow);
}
.forgot-title { font-size: 24px; font-weight: 700; color: var(--text-primary); letter-spacing: 0.5px; margin-bottom: 6px; }
.forgot-subtitle { font-size: 13px; color: var(--text-muted); }
.forgot-form { margin-bottom: 20px; }
.submit-btn { width: 100%; height: 46px; border-radius: var(--radius-md); font-size: 15px; letter-spacing: 2px; }
.back-link { text-align: center; font-size: 13px; }
.back-link a { color: var(--accent); text-decoration: none; }
</style>
