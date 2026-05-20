<template>
  <div class="targets-page">
    <div class="page-header">
      <h1 class="page-title">目标检测库</h1>
      <p class="page-subtitle">DOTA v1.0 · 15 类遥感目标</p>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-value mono">{{ targets.length }}</span>
        <span class="stat-label">目标类别</span>
      </div>
      <div class="stat-card">
        <span class="stat-value mono">15</span>
        <span class="stat-label">DOTA v1.0</span>
      </div>
    </div>

    <div class="search-bar">
      <el-input v-model="searchQuery" placeholder="搜索类别..." size="default" class="search-input" clearable>
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <div class="targets-grid">
      <div v-for="t in filteredTargets" :key="t.id" class="target-card">
        <div class="target-icon">
          <el-icon :size="22"><Aim /></el-icon>
        </div>
        <div class="target-body">
          <span class="target-name">{{ t.chinese_name }}</span>
          <span class="target-en">{{ t.name }}</span>
          <span class="target-desc" v-if="t.description">{{ t.description }}</span>
        </div>
        <span class="target-id mono">{{ String(t.id).padStart(2, '0') }}</span>
      </div>

      <div v-if="filteredTargets.length === 0" class="empty-state">
        <p class="empty-text">未找到匹配类别</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { Search, Aim } from "@element-plus/icons-vue";
import { getTargetList } from "../api/detection";

const searchQuery = ref("");
const targets = ref([]);

onMounted(async () => {
  try {
    const res = await getTargetList();
    if (res.data) targets.value = res.data;
  } catch (e) { /* use empty */ }
});

const filteredTargets = computed(() => {
  if (!searchQuery.value) return targets.value;
  const q = searchQuery.value.toLowerCase();
  return targets.value.filter(t =>
    t.name.toLowerCase().includes(q) || t.chinese_name.includes(q)
  );
});
</script>

<style scoped>
.targets-page { width: 100%; }

.page-header { margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 13px; color: var(--text-muted); }

.stats-row { display: flex; gap: 14px; margin-bottom: 24px; }
.stat-card {
  flex: 1; max-width: 180px; padding: 18px 20px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); display: flex; flex-direction: column; gap: 4px;
}
.stat-value { font-size: 28px; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 12px; color: var(--text-muted); }
.mono { font-family: var(--mono); }

.search-bar { margin-bottom: 24px; }
.search-input { max-width: 280px; }

.targets-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }

.target-card {
  display: flex; align-items: center; gap: 14px; padding: 16px 18px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); transition: all 0.2s;
}
.target-card:hover { border-color: var(--border-light); box-shadow: var(--card-shadow-hover); }

.target-icon {
  width: 42px; height: 42px; border-radius: var(--radius-sm);
  background: var(--accent-dim); color: var(--accent);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.target-body { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.target-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.target-en { font-size: 11px; color: var(--text-muted); font-family: var(--mono); }
.target-desc { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.target-id { font-size: 13px; color: var(--text-muted); font-weight: 600; }

.empty-state { grid-column: 1 / -1; padding: 60px 0; text-align: center; }
.empty-text { font-size: 14px; color: var(--text-muted); }
</style>
