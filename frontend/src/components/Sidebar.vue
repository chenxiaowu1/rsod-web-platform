<template>
  <div class="sidebar-container">
    <div class="logo-section">
      <div class="logo-mark">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <circle cx="12" cy="12" r="3"/>
          <line x1="12" y1="2" x2="12" y2="9"/>
          <line x1="12" y1="15" x2="12" y2="22"/>
          <line x1="2" y1="12" x2="9" y2="12"/>
          <line x1="15" y1="12" x2="22" y2="12"/>
        </svg>
      </div>
      <div class="logo-text">
        <div class="logo-title">RSOD</div>
        <div class="logo-subtitle">Remote Sensing</div>
      </div>
    </div>

    <div class="nav-menu">
      <div
        v-for="item in menuList"
        :key="item.path"
        class="nav-item"
        :class="{ active: currentPath === item.path }"
        @click="handleMenuClick(item)"
      >
        <el-icon :size="17" class="nav-icon"><component :is="item.icon" /></el-icon>
        <div class="nav-text-wrap">
          <span class="nav-text">{{ item.name }}</span>
          <span class="nav-desc">{{ item.desc }}</span>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="footer-divider"></div>
      <div class="footer-row">
        <span class="status-dot"></span>
        <span class="status-text">检测 · 变化 · 视频流</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import { Picture, Clock, TrendCharts, ChatDotRound, DataLine, User, Connection, VideoCamera } from "@element-plus/icons-vue";

const router = useRouter();
const route = useRoute();
const { t } = useI18n();

const menuList = computed(() => [
  { name: t("nav.detection"), desc: t("detection.subtitle"), icon: Picture, path: "/detection" },
  { name: t("nav.changeDetection"), desc: t("changeDetection.subtitle"), icon: Connection, path: "/change-detection" },
  { name: t("nav.video"), desc: t("video.subtitle"), icon: VideoCamera, path: "/video" },
  { name: t("nav.qa"), desc: t("qa.subtitle"), icon: ChatDotRound, path: "/qa" },
  { name: t("nav.history"), desc: t("history.subtitle"), icon: Clock, path: "/history" },
  { name: t("nav.statistics"), desc: t("statistics.subtitle"), icon: TrendCharts, path: "/statistics" },
  { name: t("nav.targets"), desc: t("targets.subtitle"), icon: DataLine, path: "/targets" },
  { name: t("nav.profile"), desc: t("profile.subtitle"), icon: User, path: "/profile" },
]);

const currentPath = computed(() => route.path);
const handleMenuClick = (item) => router.push(item.path);
</script>

<style scoped>
.sidebar-container {
  height: 100%; display: flex; flex-direction: column;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-color);
}

.logo-section {
  height: 56px; display: flex; align-items: center; gap: 10px;
  padding: 0 16px; border-bottom: 1px solid var(--border-color);
}
.logo-mark {
  width: 34px; height: 34px; border-radius: 6px;
  background: linear-gradient(135deg, var(--accent-dim), transparent);
  border: 1px solid rgba(0, 194, 232, 0.15);
  display: flex; align-items: center; justify-content: center;
  color: var(--accent); flex-shrink: 0;
}
.logo-text { overflow: hidden; }
.logo-title {
  font-size: 14px; font-weight: 700; color: var(--text-primary);
  letter-spacing: 0.5px; font-family: var(--mono);
}
.logo-subtitle {
  font-size: 10px; color: var(--text-muted); letter-spacing: 0.5px;
}

.nav-menu { flex: 1; padding: 12px 8px; }

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: var(--radius-md); margin-bottom: 1px;
  cursor: pointer; transition: all 0.15s; color: var(--text-secondary);
  position: relative;
}
.nav-item:hover { background: var(--bg-card-hover); color: var(--text-primary); }
.nav-item.active {
  background: var(--accent-dim); color: var(--accent); font-weight: 500;
}
.nav-item.active::before {
  content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 2px; height: 18px; background: var(--accent); border-radius: 0 2px 2px 0;
}

.nav-icon { flex-shrink: 0; opacity: 0.8; }
.nav-item.active .nav-icon { opacity: 1; }

.nav-text-wrap { display: flex; flex-direction: column; gap: 1px; overflow: hidden; }
.nav-text { font-size: 13px; line-height: 1.3; }
.nav-desc { font-size: 10px; color: var(--text-muted); line-height: 1.3; white-space: nowrap; }
.nav-item.active .nav-desc { color: var(--accent); opacity: 0.6; }

.sidebar-footer { padding: 12px 16px; }
.footer-divider { height: 1px; background: var(--border-color); margin-bottom: 12px; }
.footer-row { display: flex; align-items: center; gap: 8px; }
.status-dot {
  width: 5px; height: 5px; border-radius: 50%; background: var(--accent);
  box-shadow: 0 0 4px var(--accent-glow);
}
.status-text { font-size: 10px; color: var(--text-muted); font-family: var(--mono); letter-spacing: 0.5px; }
</style>
