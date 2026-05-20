<template>
  <div class="sidebar-container">
    <div class="logo-section">
      <div class="logo-icon">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <circle cx="12" cy="12" r="3"/>
          <line x1="12" y1="2" x2="12" y2="9"/>
          <line x1="12" y1="15" x2="12" y2="22"/>
          <line x1="2" y1="12" x2="9" y2="12"/>
          <line x1="15" y1="12" x2="22" y2="12"/>
        </svg>
      </div>
      <div class="logo-text">
        <div class="logo-title">遥感目标检测</div>
        <div class="logo-subtitle">遥感目标检测</div>
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
        <el-icon :size="18" class="nav-icon"><component :is="item.icon" /></el-icon>
        <span class="nav-text">{{ item.name }}</span>
        <span v-if="currentPath === item.path" class="active-indicator"></span>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="status-dot"></div>
      <span class="status-text">YOLO11x-OBB · DOTA v1.0</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { Picture, Clock, ChatDotRound, DataLine, User } from "@element-plus/icons-vue";

const router = useRouter();
const route = useRoute();

const menuList = [
  { name: "智能检测", icon: Picture, path: "/detection" },
  { name: "历史记录", icon: Clock, path: "/history" },
  { name: "AI 问答", icon: ChatDotRound, path: "/qa" },
  { name: "目标库", icon: DataLine, path: "/targets" },
  { name: "个人中心", icon: User, path: "/profile" },
];

const currentPath = computed(() => route.path);
const handleMenuClick = (item) => router.push(item.path);
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.logo-section {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-color);
}

.logo-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--on-accent);
  margin-right: 12px;
  flex-shrink: 0;
}

.logo-text { overflow: hidden; }
.logo-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}
.logo-subtitle {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
}

.nav-menu {
  flex: 1;
  padding: 16px 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  margin-bottom: 4px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  color: var(--text-secondary);
}

.nav-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-dim);
  color: var(--accent);
  font-weight: 500;
}

.active-indicator {
  position: absolute;
  left: -10px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 8px var(--accent-glow);
}

.nav-icon {
  margin-right: 12px;
  flex-shrink: 0;
  font-size: 18px;
}

.nav-text {
  font-size: 13px;
}

.sidebar-footer {
  padding: 14px 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 6px var(--accent-glow);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.status-text {
  font-size: 11px;
  color: var(--text-muted);
}
</style>
