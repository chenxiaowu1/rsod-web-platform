<template>
  <teleport to="body">
    <transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="close">
        <div class="modal-card">
          <button class="modal-close" @click="close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>

          <div class="modal-tabs" v-if="!forgotMode">
            <button :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
            <button :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
          </div>

          <!-- 登录 -->
          <el-form v-if="mode === 'login' && !forgotMode" ref="loginRef" :model="loginForm" :rules="loginRules"
                   @keydown.enter="handleLogin" class="modal-form">
            <div class="field">
              <el-input v-model="loginForm.account" placeholder="邮箱或用户名" size="large">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </div>
            <div class="field">
              <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" show-password>
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </div>
            <div class="form-foot">
              <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
              <button type="button" class="link-btn" @click="forgotMode = true">忘记密码？</button>
            </div>
            <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="handleLogin">
              登录
            </el-button>
          </el-form>

          <!-- 注册 -->
          <el-form v-if="mode === 'register' && !forgotMode" ref="regRef" :model="regForm" :rules="regRules"
                   @keydown.enter="handleRegister" class="modal-form">
            <div class="field">
              <el-input v-model="regForm.username" placeholder="用户名" size="large">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </div>
            <div class="field">
              <el-input v-model="regForm.email" placeholder="邮箱地址" size="large">
                <template #prefix><el-icon><Message /></el-icon></template>
              </el-input>
            </div>
            <div class="field">
              <el-input v-model="regForm.password" type="password" placeholder="密码" size="large" show-password>
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </div>
            <div class="field">
              <el-input v-model="regForm.confirm" type="password" placeholder="确认密码" size="large" show-password>
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </div>
            <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="handleRegister">
              注册
            </el-button>
          </el-form>

          <!-- 忘记密码 -->
          <div v-if="forgotMode" class="modal-form">
            <p class="forgot-hint">输入注册邮箱，我们将发送重置链接</p>
            <div class="field">
              <el-input v-model="forgotEmail" placeholder="注册邮箱" size="large">
                <template #prefix><el-icon><Message /></el-icon></template>
              </el-input>
            </div>
            <el-button type="primary" size="large" class="submit-btn" @click="handleForgot">
              发送重置链接
            </el-button>
            <button type="button" class="link-btn center" @click="forgotMode = false">返回登录</button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, reactive } from "vue";
import { ElMessage } from "element-plus";
import { User, Lock, Message } from "@element-plus/icons-vue";
import { loginUser, registerUser } from "../utils/auth";

const props = defineProps({ visible: Boolean });
const emit = defineEmits(["close", "logged-in"]);

const mode = ref("login");
const forgotMode = ref(false);
const forgotEmail = ref("");
const loading = ref(false);
const loginRef = ref(null);
const regRef = ref(null);

const loginForm = reactive({ account: "", password: "", remember: false });
const loginRules = {
  account: [{ required: true, message: "请输入邮箱或用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const regForm = reactive({ username: "", email: "", password: "", confirm: "" });
const regRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }, { min: 3, max: 20, message: "3-20 个字符", trigger: "blur" }],
  email: [{ required: true, message: "请输入邮箱", trigger: "blur" }, { type: "email", message: "邮箱格式不正确", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }, { min: 6, max: 30, message: "6-30 个字符", trigger: "blur" }],
  confirm: [
    { required: true, message: "请确认密码", trigger: "blur" },
    { validator: (_, v, cb) => v !== regForm.password ? cb(new Error("两次密码不一致")) : cb(), trigger: "blur" },
  ],
};

const handleLogin = () => {
  loginRef.value?.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    const r = await loginUser(loginForm.account, loginForm.password);
    loading.value = false;
    if (r.success) {
      ElMessage.success(`欢迎回来，${r.user.username}`);
      emit("logged-in");
      close();
    } else {
      ElMessage.error(r.message);
    }
  });
};

const handleRegister = () => {
  regRef.value?.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    const r = await registerUser(regForm.username, regForm.email, regForm.password);
    if (r.success) {
      ElMessage.success("注册成功，正在登录...");
      const lr = await loginUser(regForm.username, regForm.password);
      loading.value = false;
      if (lr.success) {
        emit("logged-in");
        close();
      }
    } else {
      loading.value = false;
      ElMessage.error(r.message);
    }
  });
};

const handleForgot = () => {
  if (!forgotEmail.value) { ElMessage.warning("请输入邮箱"); return; }
  ElMessage.success("重置链接已发送（模拟）");
  forgotMode.value = false;
};

const close = () => {
  mode.value = "login";
  forgotMode.value = false;
  emit("close");
};
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 2000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(3, 7, 17, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.modal-card {
  width: 400px; max-width: 94vw;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 36px 32px 28px;
  position: relative;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
}

.modal-close {
  position: absolute; top: 14px; right: 14px;
  background: none; border: none; color: var(--text-muted);
  cursor: pointer; padding: 4px; border-radius: 4px; line-height: 0;
  transition: color 0.15s;
}
.modal-close:hover { color: var(--text-primary); }

.modal-tabs {
  display: flex; gap: 0; margin-bottom: 28px;
  border-bottom: 1px solid var(--border-color);
}
.modal-tabs button {
  flex: 1; padding: 10px 0; border: none; background: none;
  font-size: 14px; color: var(--text-muted); cursor: pointer;
  font-weight: 500; transition: color 0.15s;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
}
.modal-tabs button.active {
  color: var(--accent); border-bottom-color: var(--accent);
}
.modal-tabs button:hover { color: var(--text-primary); }

.modal-form { display: flex; flex-direction: column; gap: 14px; }
.field { width: 100%; }

.form-foot {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px;
}
.link-btn {
  background: none; border: none; color: var(--accent); cursor: pointer;
  font-size: 13px; padding: 0;
}
.link-btn:hover { opacity: 0.8; }
.link-btn.center { display: block; text-align: center; width: 100%; margin-top: 8px; }

.submit-btn {
  width: 100%; height: 44px; font-size: 14px; letter-spacing: 1px;
  margin-top: 4px;
}

.forgot-hint {
  font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;
}

.modal-fade-enter-active { transition: all 0.2s ease; }
.modal-fade-leave-active { transition: all 0.15s ease; }
.modal-fade-enter-from { opacity: 0; }
.modal-fade-enter-from .modal-card { transform: scale(0.95); }
.modal-fade-leave-to { opacity: 0; }
</style>
