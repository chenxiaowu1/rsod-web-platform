<template>
  <div class="targets-page">
    <div class="page-header">
      <h1 class="page-title">目标库</h1>
      <p class="page-subtitle">各类别目标说明与模型支持情况</p>
    </div>

    <div class="targets-tabs">
      <div v-for="tab in tabs" :key="tab.key" class="t-tab"
           :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
        <el-icon :size="16"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-value mono">{{ detectionModels }}</span>
        <span class="stat-label">检测模型</span>
      </div>
      <div class="stat-card">
        <span class="stat-value mono">{{ cdModels }}</span>
        <span class="stat-label">变化检测模型</span>
      </div>
      <div class="stat-card">
        <span class="stat-value mono">3</span>
        <span class="stat-label">视频流模型</span>
      </div>
    </div>

    <!-- DOTA 15 类 -->
    <template v-if="activeTab === 'detection'">
      <div class="targets-grid">
        <div v-for="t in detTargets" :key="t.id" class="target-card">
          <div class="target-icon"><el-icon :size="22"><Aim /></el-icon></div>
          <div class="target-body">
            <span class="target-name">{{ t.chinese_name }}</span>
            <span class="target-en">{{ t.name }}</span>
            <span class="target-desc" v-if="t.description">{{ t.description }}</span>
          </div>
          <span class="target-id mono">{{ String(t.id).padStart(2, '0') }}</span>
        </div>
      </div>
    </template>

    <!-- 变化检测说明 -->
    <template v-if="activeTab === 'change'">
      <div class="cd-intro">
        <el-icon :size="48"><Connection /></el-icon>
        <h3>变化检测不区分类别</h3>
        <p>输入双时相遥感影像（同一区域、不同时间），模型输出二值变化 mask。</p>
        <p>红色区域 = 发生变化，黑色区域 = 未变化。</p>
        <p>无目标类别概念，仅判断"变"与"不变"。</p>
      </div>
    </template>

    <!-- COCO 80 类 -->
    <template v-if="activeTab === 'video'">
      <div v-for="(grp, gidx) in cocoGroups" :key="gidx" class="coco-group">
        <h3 class="group-title">{{ grp.label }}</h3>
        <div class="coco-grid">
          <div v-for="c in grp.classes" :key="c.id" class="coco-card">
            <span class="coco-id mono">{{ String(c.id).padStart(2, '0') }}</span>
            <span class="coco-name">{{ c.en }}</span>
            <span class="coco-cn">{{ c.cn }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Aim, Connection, VideoCamera } from "@element-plus/icons-vue";
import { getTargetList, getModels, getChangeModels } from "../api/detection";

const tabs = [
  { key: "detection", label: "遥感检测 · DOTA", icon: Aim },
  { key: "change", label: "变化检测", icon: Connection },
  { key: "video", label: "视频流 · COCO", icon: VideoCamera },
];

const activeTab = ref("detection");
const detectionModels = ref(0);
const cdModels = ref(0);
const detTargets = ref([]);

const cocoGroups = [
  { label: "人员", classes: [
    { id: 0, en: "person", cn: "行人" },
    { id: 1, en: "bicycle", cn: "自行车" },
    { id: 2, en: "car", cn: "汽车" },
    { id: 3, en: "motorcycle", cn: "摩托车" },
  ]},
  { label: "交通", classes: [
    { id: 4, en: "airplane", cn: "飞机" },
    { id: 5, en: "bus", cn: "公交车" },
    { id: 6, en: "train", cn: "火车" },
    { id: 7, en: "truck", cn: "卡车" },
    { id: 8, en: "boat", cn: "船" },
    { id: 9, en: "traffic light", cn: "红绿灯" },
    { id: 10, en: "fire hydrant", cn: "消防栓" },
    { id: 11, en: "stop sign", cn: "停止标志" },
  ]},
  { label: "动物", classes: [
    { id: 14, en: "bird", cn: "鸟" },
    { id: 15, en: "cat", cn: "猫" },
    { id: 16, en: "dog", cn: "狗" },
    { id: 17, en: "horse", cn: "马" },
    { id: 18, en: "sheep", cn: "羊" },
    { id: 19, en: "cow", cn: "牛" },
    { id: 20, en: "elephant", cn: "大象" },
    { id: 21, en: "bear", cn: "熊" },
    { id: 22, en: "zebra", cn: "斑马" },
    { id: 23, en: "giraffe", cn: "长颈鹿" },
  ]},
  { label: "其他", classes: [
    { id: 24, en: "backpack", cn: "背包" },
    { id: 25, en: "umbrella", cn: "雨伞" },
    { id: 56, en: "chair", cn: "椅子" },
    { id: 60, en: "tv", cn: "电视" },
    { id: 63, en: "laptop", cn: "笔记本电脑" },
    { id: 73, en: "book", cn: "书" },
  ]},
];

onMounted(async () => {
  try {
    const res = await getTargetList();
    if (res.data) detTargets.value = res.data;
  } catch (e) { /* */ }
  try {
    const dm = await getModels();
    if (dm.data) detectionModels.value = dm.data.length;
  } catch (e) { /* */ }
  try {
    const cm = await getChangeModels();
    if (cm.data) cdModels.value = cm.data.length;
  } catch (e) { /* */ }
});
</script>

<style scoped>
.targets-page { width: 100%; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 13px; color: var(--text-muted); }

.targets-tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.t-tab {
  display: flex; align-items: center; gap: 6px; padding: 8px 18px;
  border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 500;
  background: var(--bg-card); border: 1px solid var(--border-color);
  color: var(--text-muted); transition: all 0.2s;
}
.t-tab:hover { border-color: var(--border-light); color: var(--text-secondary); }
.t-tab.active { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }

.stats-row { display: flex; gap: 14px; margin-bottom: 24px; }
.stat-card { flex: 1; max-width: 180px; padding: 18px 20px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); display: flex; flex-direction: column; gap: 4px; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 12px; color: var(--text-muted); }
.mono { font-family: var(--mono); }

.targets-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.target-card { display: flex; align-items: center; gap: 14px; padding: 16px 18px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); transition: all 0.2s; }
.target-card:hover { border-color: var(--border-light); }
.target-icon { width: 42px; height: 42px; border-radius: var(--radius-sm); background: var(--accent-dim); color: var(--accent); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.target-body { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.target-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.target-en { font-size: 11px; color: var(--text-muted); font-family: var(--mono); }
.target-desc { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.target-id { font-size: 13px; color: var(--text-muted); font-weight: 600; }

.cd-intro {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 80px 40px; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); text-align: center; color: var(--text-secondary);
}
.cd-intro h3 { font-size: 18px; color: var(--text-primary); }
.cd-intro p { font-size: 14px; max-width: 500px; }

.coco-group { margin-bottom: 28px; }
.group-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; padding-left: 4px; }
.coco-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.coco-card { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); }
.coco-id { font-size: 12px; color: var(--text-muted); min-width: 20px; }
.coco-name { font-size: 13px; color: var(--text-primary); flex: 1; }
.coco-cn { font-size: 11px; color: var(--text-muted); }
</style>
