import { createRouter, createWebHistory } from "vue-router";

const routes = [
  { path: "/", redirect: "/detection" },
  { path: "/detection", name: "智能检测", component: () => import("../views/DetectionPage.vue") },
  { path: "/change-detection", name: "变化检测", component: () => import("../views/ChangeDetectionPage.vue") },
  { path: "/video", name: "视频流检测", component: () => import("../views/VideoPage.vue") },
  { path: "/qa", name: "AI问答", component: () => import("../views/QAPage.vue") },
  { path: "/history", name: "历史记录", component: () => import("../views/HistoryPage.vue") },
  { path: "/statistics", name: "检测统计", component: () => import("../views/StatisticsPage.vue") },
  { path: "/targets", name: "目标库", component: () => import("../views/TargetsPage.vue") },
  { path: "/profile", name: "个人中心", component: () => import("../views/ProfilePage.vue") },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
