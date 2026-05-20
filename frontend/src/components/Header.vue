<template>
  <div class="header-container">
    <div class="header-left">
      <div class="page-indicator">
        <span class="indicator-dot"></span>
        <span class="indicator-text">{{ currentPageName }}</span>
      </div>
    </div>

    <div class="header-right">
      <div class="header-actions">
        <el-tooltip :content="isDark ? '切换浅色' : '切换深色'" placement="bottom">
          <el-button class="theme-btn" size="small" circle @click="toggleTheme">
            <el-icon :size="16"><Sunny v-if="isDark" /><Moon v-else /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="通知" placement="bottom">
          <el-badge :value="3" :max="99" class="header-badge">
            <el-icon class="action-icon"><Bell /></el-icon>
          </el-badge>
        </el-tooltip>
      </div>

      <div class="user-section">
        <el-avatar class="user-avatar" :size="32">
          <el-icon :size="18"><User /></el-icon>
        </el-avatar>
        <div class="user-info">
          <span class="user-name">Lily</span>
          <span class="user-role">普通用户</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { Bell, User, Sunny, Moon } from "@element-plus/icons-vue";

const route = useRoute();
const isDark = ref(true);
const THEME_KEY = "rsod-theme";

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

onMounted(() => {
  const saved = localStorage.getItem(THEME_KEY);
  applyTheme(saved !== "light"); // 默认深色
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
.header-right { display: flex; align-items: center; gap: 20px; }
.header-actions { display: flex; align-items: center; gap: 8px; }

.theme-btn {
  color: var(--text-secondary) !important;
  background: transparent !important;
  border-color: var(--border-color) !important;
}
.theme-btn:hover { color: var(--accent) !important; border-color: var(--accent) !important; }

.header-badge { cursor: pointer; }
.action-icon { font-size: 18px; color: var(--text-secondary); cursor: pointer; transition: color 0.2s; }
.action-icon:hover { color: var(--accent); }

.user-section {
  display: flex; align-items: center; gap: 10px; padding: 4px 10px;
  border-radius: var(--radius-md); cursor: pointer; transition: background 0.2s;
}
.user-section:hover { background: var(--bg-card); }
.user-avatar { background: linear-gradient(135deg, var(--accent), var(--accent-secondary)); }
.user-info { display: flex; flex-direction: column; }
.user-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.user-role { font-size: 11px; color: var(--text-muted); }
</style>
