<template>
  <div class="header-container">
    <div class="header-left">
      <div class="page-indicator">
        <span class="indicator-dot"></span>
        <span class="indicator-text">{{ currentPageName }}</span>
      </div>
    </div>

    <div class="header-right">
      <el-tooltip :content="isDark ? '切换浅色' : '切换深色'" placement="bottom">
        <el-button class="theme-btn" size="small" circle @click="toggleTheme">
          <el-icon :size="16"><Sunny v-if="isDark" /><Moon v-else /></el-icon>
        </el-button>
      </el-tooltip>

      <div class="user-section" @click="goProfile">
        <el-avatar class="user-avatar" :size="32">
          <el-icon :size="18"><User /></el-icon>
        </el-avatar>
        <div class="user-info">
          <span class="user-name">{{ displayName }}</span>
          <span class="user-role">普通用户</span>
        </div>
      </div>

      <el-tooltip content="退出登录" placement="bottom">
        <el-button class="logout-btn" size="small" circle @click="handleLogout">
          <el-icon :size="16"><SwitchButton /></el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessageBox } from "element-plus";
import { User, Sunny, Moon, SwitchButton } from "@element-plus/icons-vue";
import { getSession, logoutUser } from "../utils/auth";

const route = useRoute();
const router = useRouter();
const isDark = ref(true);
const THEME_KEY = "rsod-theme";

const session = getSession();
const displayName = session ? session.username : "Lily";

const pageNames = {
  "/detection": "智能检测",
  "/history": "历史记录",
  "/qa": "AI 问答",
  "/targets": "目标库",
  "/profile": "个人中心",
};
const currentPageName = computed(() => pageNames[route.path] || "智能检测");

const applyTheme = (dark) => {
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  isDark.value = dark;
  localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
};
const toggleTheme = () => applyTheme(!isDark.value);

const goProfile = () => router.push("/profile");

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm("确定要退出登录吗？", "退出登录", {
      confirmButtonText: "退出",
      cancelButtonText: "取消",
      type: "warning",
    });
    logoutUser();
    router.push("/login");
  } catch (e) { /* cancelled */ }
};

onMounted(() => {
  const saved = localStorage.getItem(THEME_KEY);
  applyTheme(saved !== "light");
});
</script>

<style scoped>
.header-container { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.header-left { display: flex; align-items: center; }
.page-indicator { display: flex; align-items: center; gap: 10px; }
.indicator-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent); box-shadow: 0 0 8px var(--accent-glow);
}
.indicator-text { font-size: 14px; font-weight: 600; color: var(--text-primary); letter-spacing: 0.3px; }

.header-right { display: flex; align-items: center; gap: 12px; }

.theme-btn {
  color: var(--text-secondary) !important;
  background: transparent !important;
  border-color: var(--border-color) !important;
}
.theme-btn:hover { color: var(--accent) !important; border-color: var(--accent) !important; }

.user-section {
  display: flex; align-items: center; gap: 10px; padding: 4px 10px;
  border-radius: var(--radius-md); cursor: pointer; transition: background 0.2s;
}
.user-section:hover { background: var(--bg-card); }
.user-avatar { background: linear-gradient(135deg, var(--accent), var(--accent-secondary)); }
.user-info { display: flex; flex-direction: column; }
.user-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.user-role { font-size: 11px; color: var(--text-muted); }

.logout-btn {
  color: var(--text-muted) !important;
  background: transparent !important;
  border-color: transparent !important;
}
.logout-btn:hover { color: #ef4444 !important; border-color: rgba(239,68,68,0.3) !important; }
</style>
