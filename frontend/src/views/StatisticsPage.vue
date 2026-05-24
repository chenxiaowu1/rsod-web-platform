<template>
  <div class="stats-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ $t('nav.statistics') }}</h1>
        <p class="page-subtitle">{{ $t('statistics.subtitle') }}</p>
      </div>
      <el-button @click="fetchData" :loading="loading">{{ $t('statistics.refresh') }}</el-button>
    </div>

    <div class="stats-tabs">
      <div v-for="tab in tabs" :key="tab.key" class="s-tab"
           :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key; fetchData()">
        <el-icon :size="16"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state"><span class="loader"></span><span>{{ $t('statistics.loading') }}</span></div>

    <!-- {{ $t('nav.detection') }}统计 -->
    <template v-else-if="activeTab === 'detection' && stats">
      <div class="overview-cards">
        <div class="ov-card"><span class="ov-value">{{ stats.total_images }}</span><span class="ov-label">{{ $t('statistics.detectionImages') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ stats.total_objects }}</span><span class="ov-label">{{ $t('statistics.totalObjectsDetected') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ stats.avg_objects_per_image }}</span><span class="ov-label">{{ $t('statistics.avgObjectsPerImage') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ stats.avg_detection_time }}s</span><span class="ov-label">{{ $t('statistics.avgDetectionTime') }}</span></div>
      </div>

      <div class="section-card" v-if="stats.daily_trend?.length">
        <div class="section-header"><h3>{{ $t('statistics.dailyDetectionTrend') }}</h3></div>
        <div class="trend-chart"><div class="trend-bars">
          <div v-for="day in stats.daily_trend" :key="day.date" class="trend-bar-col" :title="`${day.date}: ${day.count}${$t('statistics.times')}, ${day.objects}${$t('statistics.videos')}`">
            <div class="trend-bar-wrap"><div class="trend-bar" :style="{ height: barH(day.objects, maxDaily) + '%' }"></div></div>
            <span class="trend-date">{{ day.date.slice(5) }}</span><span class="trend-val">{{ day.objects }}</span>
          </div>
        </div></div>
      </div>

      <div class="two-col">
        <div class="section-card" v-if="stats.model_distribution?.length">
          <div class="section-header"><h3>{{ $t('statistics.modelDistribution') }}</h3></div>
          <div v-for="m in stats.model_distribution" :key="m.model" class="bar-row">
            <span class="bar-label">{{ m.model }}</span><span class="bar-num">{{ m.count }}{{ $t('statistics.times') }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: barW(m.count, maxModel) + '%' }"></div></div>
          </div>
        </div>
        <div class="section-card" v-if="stats.confidence_distribution?.length">
          <div class="section-header"><h3>{{ $t('statistics.confidenceDistribution') }}</h3></div>
          <div v-for="bin in stats.confidence_distribution" :key="bin.range" class="bar-row">
            <span class="bar-label">{{ bin.range }}</span><span class="bar-num">{{ bin.count }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: barW(bin.count, maxConf) + '%' }"></div></div>
          </div>
        </div>
      </div>

      <div class="section-card" v-if="stats.per_class?.length">
        <div class="section-header"><h3>{{ $t('statistics.perClassStats') }}</h3></div>
        <div v-for="cls in stats.per_class" :key="cls.class_name" class="bar-row">
          <span class="bar-label">{{ cls.chinese_name }} <em>{{ cls.class_name }}</em></span>
          <span class="bar-num">{{ cls.count }}</span>
          <div class="bar-track"><div class="bar-fill" :style="{ width: barW(cls.count, maxClass) + '%' }"></div></div>
        </div>
      </div>
    </template>

    <!-- {{ $t('nav.changeDetection') }}统计 -->
    <template v-else-if="activeTab === 'change' && stats">
      <div class="overview-cards">
        <div class="ov-card"><span class="ov-value">{{ stats.total_pairs }}</span><span class="ov-label">{{ $t('statistics.detectionPairs') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ (stats.avg_change_ratio * 100).toFixed(2) }}%</span><span class="ov-label">{{ $t('statistics.avgChangeRatio') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ stats.avg_time }}s</span><span class="ov-label">{{ $t('statistics.avgTimePerPair') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ stats.total_time }}s</span><span class="ov-label">{{ $t('statistics.totalTime') }}</span></div>
      </div>

      <div class="two-col">
        <div class="section-card" v-if="stats.daily_trend?.length">
          <div class="section-header"><h3>{{ $t('statistics.dailyChangeTrend') }}</h3></div>
          <div v-for="d in stats.daily_trend" :key="d.date" class="bar-row">
            <span class="bar-label">{{ d.date }}</span><span class="bar-num">{{ d.count }}{{ $t('statistics.pairs') }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: barW(d.count, maxDaily2) + '%' }"></div></div>
          </div>
        </div>
        <div class="section-card" v-if="stats.model_usage?.length">
          <div class="section-header"><h3>{{ $t('statistics.modelDistribution') }}</h3></div>
          <div v-for="m in stats.model_usage" :key="m.model" class="bar-row">
            <span class="bar-label">{{ m.model }}</span><span class="bar-num">{{ m.count }}{{ $t('statistics.times') }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: barW(m.count, maxModel2) + '%' }"></div></div>
          </div>
        </div>
      </div>
    </template>

    <!-- 视频统计 -->
    <template v-else-if="activeTab === 'video' && stats">
      <div class="overview-cards">
        <div class="ov-card"><span class="ov-value">{{ stats.total_videos }}</span><span class="ov-label">{{ $t('statistics.totalVideos') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ stats.total_frames }}</span><span class="ov-label">{{ $t('statistics.totalFrames') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ stats.total_objects }}</span><span class="ov-label">{{ $t('statistics.totalObjectsDetected') }}</span></div>
        <div class="ov-card"><span class="ov-value">{{ stats.avg_time }}s</span><span class="ov-label">{{ $t('statistics.avgTimePerVideo') }}</span></div>
      </div>

      <div class="two-col">
        <div class="section-card" v-if="stats.daily_trend?.length">
          <div class="section-header"><h3>{{ $t('statistics.dailyProcessing') }}</h3></div>
          <div v-for="d in stats.daily_trend" :key="d.date" class="bar-row">
            <span class="bar-label">{{ d.date }}</span><span class="bar-num">{{ d.count }}{{ $t('statistics.videos') }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: barW(d.count, maxDaily3) + '%' }"></div></div>
          </div>
        </div>
        <div class="section-card" v-if="stats.model_usage?.length">
          <div class="section-header"><h3>{{ $t('statistics.modelDistribution') }}</h3></div>
          <div v-for="m in stats.model_usage" :key="m.model" class="bar-row">
            <span class="bar-label">{{ m.model }}</span><span class="bar-num">{{ m.count }}{{ $t('statistics.times') }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: barW(m.count, maxModel3) + '%' }"></div></div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">
      <el-icon :size="48"><DataLine /></el-icon>
      <p class="empty-text">{{ $t('statistics.noData') }}</p>
      <el-button type="primary" @click="$router.push('/detection')">{{ $t('statistics.startDetection') }}</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { ElMessage } from "element-plus";
import { DataLine, Aim, Connection, VideoCamera } from "@element-plus/icons-vue";
import { getStatistics } from "../api/detection";
import request from "../utils/request";
import { requireLogin } from "../utils/request";

const { t } = useI18n();

const tabs = computed(() => [
  { key: "detection", label: t("nav.detection"), icon: Aim },
  { key: "change", label: t("nav.changeDetection"), icon: Connection },
  { key: "video", label: t("nav.video"), icon: VideoCamera },
]);

const activeTab = ref("detection");
const loading = ref(false);
const stats = ref(null);

const apiMap = {
  detection: () => getStatistics(),
  change: () => request({ url: "/change-detection/statistics", method: "get" }),
  video: () => request({ url: "/video/statistics", method: "get" }),
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await apiMap[activeTab.value]();
    stats.value = res.data;
  } catch (e) { ElMessage.error(t("statistics.fetchError")); }
  finally { loading.value = false; }
};

const maxDaily = computed(() => stats.value?.daily_trend?.length ? Math.max(...stats.value.daily_trend.map(d => d.objects || 0)) : 1);
const maxModel = computed(() => stats.value?.model_distribution?.length ? Math.max(...stats.value.model_distribution.map(m => m.count)) : 1);
const maxConf = computed(() => stats.value?.confidence_distribution?.length ? Math.max(...stats.value.confidence_distribution.map(b => b.count)) : 1);
const maxClass = computed(() => stats.value?.per_class?.length ? Math.max(...stats.value.per_class.map(c => c.count)) : 1);
const maxDaily2 = computed(() => stats.value?.daily_trend?.length ? Math.max(...stats.value.daily_trend.map(d => d.count)) : 1);
const maxModel2 = computed(() => stats.value?.model_usage?.length ? Math.max(...stats.value.model_usage.map(m => m.count)) : 1);
const maxDaily3 = computed(() => stats.value?.daily_trend?.length ? Math.max(...stats.value.daily_trend.map(d => d.count)) : 1);
const maxModel3 = computed(() => stats.value?.model_usage?.length ? Math.max(...stats.value.model_usage.map(m => m.count)) : 1);

const barH = (v, m) => m ? (v / m) * 100 : 0;
const barW = (v, m) => m ? (v / m) * 100 : 0;

onMounted(async () => {
  if (!(await requireLogin())) return;
  fetchData();
});
</script>

<style scoped>
.stats-page { width: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.header-left .page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.header-left .page-subtitle { font-size: 13px; color: var(--text-muted); }

.stats-tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.s-tab {
  display: flex; align-items: center; gap: 6px; padding: 8px 18px;
  border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 500;
  background: var(--bg-card); border: 1px solid var(--border-color);
  color: var(--text-muted); transition: all 0.2s;
}
.s-tab:hover { border-color: var(--border-light); color: var(--text-secondary); }
.s-tab.active { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }

.loading-state { display: flex; align-items: center; gap: 10px; padding: 60px 0; justify-content: center; color: var(--text-muted); }
.loader { width: 20px; height: 20px; border: 2px solid var(--border-color); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.overview-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.ov-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; display: flex; flex-direction: column; gap: 6px; }
.ov-value { font-size: 28px; font-weight: 700; color: var(--accent); font-family: var(--mono); }
.ov-label { font-size: 13px; color: var(--text-muted); }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.section-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0; }

.bar-row { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
.bar-label { flex: 0 0 160px; font-size: 12px; color: var(--text-primary); }
.bar-label em { color: var(--text-muted); font-style: normal; font-family: var(--mono); margin-left: 4px; font-size: 10px; }
.bar-num { flex: 0 0 60px; font-family: var(--mono); font-size: 12px; color: var(--accent); text-align: right; }
.bar-track { flex: 1; height: 8px; background: var(--bg-input); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-dim)); border-radius: 4px; transition: width 0.4s; }

.trend-chart { padding-top: 8px; }
.trend-bars { display: flex; align-items: flex-end; gap: 12px; height: 120px; }
.trend-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 0; }
.trend-bar-wrap { flex: 1; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.trend-bar { width: 100%; max-width: 48px; min-height: 3px; background: linear-gradient(0deg, var(--accent-dim), var(--accent)); border-radius: 3px 3px 0 0; }
.trend-date { font-size: 10px; color: var(--text-muted); font-family: var(--mono); }
.trend-val { font-size: 10px; color: var(--text-secondary); font-family: var(--mono); }

.empty-state { display: flex; flex-direction: column; align-items: center; padding: 80px 0; gap: 12px; color: var(--text-muted); }
.empty-text { font-size: 14px; }
</style>
