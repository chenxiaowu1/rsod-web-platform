<template>
  <div class="header-container">
    <div class="header-left">
      <div class="page-indicator">
        <span class="indicator-dot"></span>
        <span class="indicator-text">{{ currentPageName }}</span>
      </div>
    </div>

    <div class="header-right">
      <el-dropdown @command="switchLang" trigger="click">
        <el-button class="theme-btn" size="small" circle>
          <span style="font-size:12px;font-weight:700">{{ locale === 'zh-CN' ? '中' : 'EN' }}</span>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="zh-CN">中文</el-dropdown-item>
            <el-dropdown-item command="en">English</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-tooltip :content="isDark ? '切换浅色' : '切换深色'" placement="bottom">
        <el-button class="theme-btn" size="small" circle @click="toggleTheme">
          <el-icon :size="16"><Sunny v-if="isDark" /><Moon v-else /></el-icon>
        </el-button>
      </el-tooltip>

      <div class="user-section" @click="handleUserClick">
        <el-avatar class="user-avatar" :size="32">
          <el-icon :size="18"><User /></el-icon>
        </el-avatar>
        <div class="user-info">
          <span class="user-name">{{ displayName }}</span>
          <span class="user-role">{{ loggedIn ? '已登录' : '点击登录' }}</span>
        </div>
      </div>

      <el-tooltip v-if="loggedIn" content="退出登录" placement="bottom">
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
import { useI18n } from "vue-i18n";
import { ElMessageBox } from "element-plus";
import { User, Sunny, Moon, SwitchButton } from "@element-plus/icons-vue";
import { getSession, clearAuthState, checkAuth, authVersion } from "../utils/auth";

const { locale, t } = useI18n();

const switchLang = (lang) => {
  locale.value = lang;
  localStorage.setItem("rsod-locale", lang);
};

const emit = defineEmits(["openLogin"]);

const route = useRoute();
const router = useRouter();
const isDark = ref(true);
const THEME_KEY = "rsod-theme";

const loggedIn = computed(() => {
  authVersion.value;
  return !!getSession();
});
const displayName = computed(() => {
  authVersion.value;
  const s = getSession();
  return s ? s.username : "未登录";
});

const currentPageName = computed(() => {
  const map = {
    "/detection": t("nav.detection"),
    "/change-detection": t("nav.changeDetection"),
    "/video": t("nav.video"),
    "/history": t("nav.history"),
    "/statistics": t("nav.statistics"),
    "/qa": t("nav.qa"),
    "/targets": t("nav.targets"),
    "/profile": t("nav.profile"),
  };
  return map[route.path] || t("nav.detection");
});

const applyTheme = (dark) => {
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  isDark.value = dark;
  localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
};
const toggleTheme = () => applyTheme(!isDark.value);

const handleUserClick = () => {
  if (loggedIn.value) {
    router.push("/profile");
  } else {
    emit("openLogin");
  }
};

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm("确定要退出登录吗？", "退出登录", {
      confirmButtonText: "退出", cancelButtonText: "取消", type: "warning",
    });
    clearAuthState();
    router.push("/detection");
  } catch (e) { /* cancelled */ }
};

onMounted(async () => {
  const saved = localStorage.getItem(THEME_KEY);
  applyTheme(saved !== "light");
  // 启动时校验登录态，token 失效则自动清除并同步 UI
  await checkAuth();
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
