<template>
  <div class="targets-page">
    <div class="page-header">
      <h1 class="page-title">{{ $t('nav.targets') }}</h1>
      <p class="page-subtitle">{{ $t('targets.subtitle') }}</p>
    </div>

    <div class="targets-tabs">
      <div v-for="tab in tabs" :key="tab.key" class="t-tab"
           :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
        <el-icon :size="16"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </div>
    </div>

    <!-- DOTA 15 类 -->
    <template v-if="activeTab === 'detection'">
      <div class="targets-grid">
        <div v-for="t in detTargets" :key="t.id" class="target-card">
          <div class="target-icon"><el-icon :size="22"><Aim /></el-icon></div>
          <div class="target-body">
            <span class="target-name">{{ $t('targets.dota.' + t.name) }}</span>
            <span class="target-desc" v-if="$te('targets.dotaDesc.' + t.name)">{{ $t('targets.dotaDesc.' + t.name) }}</span>
          </div>
          <span class="target-id mono">{{ String(t.id).padStart(2, '0') }}</span>
        </div>
      </div>
    </template>

    <!-- 变化检测说明 -->
    <template v-if="activeTab === 'change'">
      <div class="cd-intro">
        <el-icon :size="48"><Connection /></el-icon>
        <h3>{{ $t('targets.cd.title') }}</h3>
        <p>{{ $t('targets.cd.line1') }}</p>
        <p>{{ $t('targets.cd.line2') }}</p>
        <p>{{ $t('targets.cd.line3') }}</p>
        <p>{{ $t('targets.cd.line4') }}</p>
      </div>
    </template>

    <!-- COCO 类别 -->
    <template v-if="activeTab === 'video'">
      <div v-for="(grp, gidx) in cocoGroups" :key="gidx" class="coco-group">
        <h3 class="group-title">{{ grp.label }}</h3>
        <div class="coco-grid">
          <div v-for="c in grp.classes" :key="c.id" class="coco-card">
            <span class="coco-id mono">{{ String(c.id).padStart(2, '0') }}</span>
            <span class="coco-name">{{ $t('targets.coco.' + c.name) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useI18n } from "vue-i18n";
import { Aim, Connection, VideoCamera } from "@element-plus/icons-vue";
import { getTargetList } from "../api/detection";
import { requireLogin } from "../utils/request";

const { t } = useI18n();

const tabs = computed(() => [
  { key: "detection", label: t("targets.detectionTab"), icon: Aim },
  { key: "change", label: t("nav.changeDetection"), icon: Connection },
  { key: "video", label: t("targets.videoTab"), icon: VideoCamera },
]);

const activeTab = ref("detection");
const detTargets = ref([]);

const cocoGroups = computed(() => [
  { label: t("targets.groupPerson"), classes: [
    { id: 0, name: "person" }, { id: 1, name: "bicycle" }, { id: 2, name: "car" },
    { id: 3, name: "motorcycle" }, { id: 5, name: "bus" }, { id: 7, name: "truck" },
  ]},
  { label: t("targets.groupVehicle"), classes: [
    { id: 4, name: "airplane" }, { id: 6, name: "train" }, { id: 8, name: "boat" },
    { id: 9, name: "traffic light" }, { id: 10, name: "fire hydrant" },
    { id: 11, name: "stop sign" }, { id: 12, name: "parking meter" },
  ]},
  { label: t("targets.groupAnimal"), classes: [
    { id: 14, name: "bird" }, { id: 15, name: "cat" }, { id: 16, name: "dog" },
    { id: 17, name: "horse" }, { id: 18, name: "sheep" }, { id: 19, name: "cow" },
    { id: 20, name: "elephant" }, { id: 21, name: "bear" }, { id: 22, name: "zebra" },
    { id: 23, name: "giraffe" },
  ]},
  { label: t("targets.groupIndoor"), classes: [
    { id: 13, name: "bench" }, { id: 56, name: "chair" }, { id: 57, name: "couch" },
    { id: 59, name: "bed" }, { id: 60, name: "dining table" }, { id: 61, name: "toilet" },
    { id: 58, name: "potted plant" }, { id: 62, name: "tv" }, { id: 63, name: "laptop" },
    { id: 64, name: "mouse" }, { id: 66, name: "keyboard" }, { id: 67, name: "cell phone" },
    { id: 73, name: "book" }, { id: 74, name: "clock" }, { id: 75, name: "vase" },
    { id: 76, name: "scissors" },
  ]},
  { label: t("targets.groupKitchen"), classes: [
    { id: 39, name: "bottle" }, { id: 40, name: "wine glass" }, { id: 41, name: "cup" },
    { id: 42, name: "fork" }, { id: 43, name: "knife" }, { id: 44, name: "spoon" },
    { id: 45, name: "bowl" }, { id: 68, name: "microwave" }, { id: 69, name: "oven" },
    { id: 70, name: "toaster" }, { id: 71, name: "sink" }, { id: 72, name: "refrigerator" },
  ]},
  { label: t("targets.groupFood"), classes: [
    { id: 46, name: "banana" }, { id: 47, name: "apple" }, { id: 48, name: "sandwich" },
    { id: 49, name: "orange" }, { id: 50, name: "broccoli" }, { id: 51, name: "carrot" },
    { id: 52, name: "hot dog" }, { id: 53, name: "pizza" }, { id: 54, name: "donut" },
    { id: 55, name: "cake" },
  ]},
  { label: t("targets.groupAccessory"), classes: [
    { id: 24, name: "backpack" }, { id: 25, name: "umbrella" }, { id: 26, name: "handbag" },
    { id: 27, name: "tie" }, { id: 28, name: "suitcase" },
  ]},
  { label: t("targets.groupSports"), classes: [
    { id: 29, name: "frisbee" }, { id: 30, name: "skis" }, { id: 31, name: "snowboard" },
    { id: 32, name: "sports ball" }, { id: 33, name: "kite" }, { id: 34, name: "baseball bat" },
    { id: 35, name: "baseball glove" }, { id: 36, name: "skateboard" },
    { id: 37, name: "surfboard" }, { id: 38, name: "tennis racket" },
  ]},
  { label: t("targets.groupAppliance"), classes: [
    { id: 65, name: "remote" }, { id: 77, name: "teddy bear" },
    { id: 78, name: "hair drier" }, { id: 79, name: "toothbrush" },
  ]},
]);

onMounted(async () => {
  if (!(await requireLogin())) return;
  try {
    const res = await getTargetList();
    if (res.data) detTargets.value = res.data;
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
</style>
