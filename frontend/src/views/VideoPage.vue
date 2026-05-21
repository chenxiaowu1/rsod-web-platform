<template>
  <div class="video-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">视频流检测</h1>
        <p class="page-subtitle">上传无人机视频，逐帧推理，实时标注</p>
      </div>
      <div class="header-right">
        <div class="model-config-box">
          <span class="config-label">模型配置</span>
          <el-select v-model="selectedModel" class="model-select" @change="onModelChange">
            <el-option v-for="m in availableModels" :key="m.key" :label="m.display" :value="m.key">
              <div class="model-option">
                <span class="model-opt-name">{{ m.display }}</span>
                <span class="model-opt-desc">{{ m.desc }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
      </div>
    </div>

    <!-- 上传区 -->
    <div class="upload-zone" v-if="!result" @click="$refs.videoInput.click()">
      <input ref="videoInput" type="file" accept="video/*" class="hidden-input" @change.stop="handleFile" />
      <el-icon :size="32"><VideoCamera /></el-icon>
      <span class="upload-text">点击上传无人机视频</span>
      <span class="upload-hint">支持 MP4 / AVI / MOV / MKV</span>
    </div>

    <!-- 处理中 -->
    <div v-if="processing" class="processing-card">
      <span class="loader"></span>
      <span class="processing-text">正在逐帧检测中...</span>
      <span class="processing-hint">大视频可能需要几分钟，请耐心等待</span>
    </div>

    <!-- 结果区 -->
    <div class="result-section" v-if="result && !processing">
      <div class="download-bar">
        <span class="download-bar-label">结果下载</span>
        <el-button size="small" type="primary" @click="doDownload">
          <el-icon :size="14"><Download /></el-icon> 下载标注视频
        </el-button>
      </div>

      <div class="result-info-row">
        <div class="info-card">
          <div class="info-row"><span class="info-label">检测模型</span><span class="info-value accent">{{ result.model_name }}</span></div>
          <div class="info-row"><span class="info-label">处理耗时</span><span class="info-value mono">{{ result.detection_time }}s</span></div>
          <div class="info-row"><span class="info-label">视频帧数</span><span class="info-value mono">{{ result.total_frames }}</span></div>
          <div class="info-row"><span class="info-label">检出目标</span><span class="info-value mono">{{ result.total_objects }} 个</span></div>
          <div class="info-row"><span class="info-label">原始帧率</span><span class="info-value mono">{{ result.fps_original }} FPS</span></div>
        </div>

        <div class="result-card">
          <div class="card-header">
            <span class="card-title">逐帧目标清单</span>
            <span class="card-badge">{{ result.total_objects }}</span>
          </div>
          <div v-if="classStats.length" class="class-stats">
            <div v-for="(c, idx) in classStats" :key="c.name" class="stat-row">
              <span class="stat-idx">{{ String(idx + 1).padStart(2, '0') }}</span>
              <span class="stat-name">{{ c.name }}</span>
              <span class="stat-count">{{ c.count }}</span>
              <div class="stat-bar-track"><div class="stat-bar-fill" :style="{ width: barW(c.count) + '%' }"></div></div>
            </div>
          </div>
          <div v-else class="box-empty">暂无检测目标</div>
        </div>
      </div>

      <el-button class="reset-btn" @click="resetAll"><el-icon><Refresh /></el-icon>重新检测</el-button>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!result && !processing">
      <el-icon :size="48"><VideoCamera /></el-icon>
      <p>上传无人机视频进行目标检测</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { detectVideo, getVideoModels, switchVideoModel, downloadVideo } from "../api/detection";
import { requireLogin } from "../utils/request";
import { VideoCamera, Download, Refresh } from "@element-plus/icons-vue";

const selectedModel = ref("");
const availableModels = ref([]);
const processing = ref(false);
const result = ref(null);

const handleFile = async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  if (!(await requireLogin())) { e.target.value = ""; return; }
  e.target.value = "";

  const fd = new FormData();
  fd.append("file", f);
  fd.append("model_key", selectedModel.value || "yolo11m");

  processing.value = true;
  result.value = null;
  try {
    const res = await detectVideo(fd);
    result.value = res;
  } catch (err) {
    ElMessage.error("检测失败");
  } finally {
    processing.value = false;
  }
};

const classStats = computed(() => {
  if (!result.value?.boxes) return [];
  const map = {};
  for (const b of result.value.boxes) {
    const k = b.class_name;
    if (!map[k]) map[k] = 0;
    map[k]++;
  }
  return Object.entries(map).sort((a, b) => b[1] - a[1]).map(([name, count]) => ({ name, count }));
});

const maxCount = computed(() => {
  if (!classStats.value.length) return 1;
  return Math.max(...classStats.value.map(c => c.count));
});

const barW = (val) => (maxCount.value === 0 ? 0 : (val / maxCount.value) * 100);

const doDownload = async () => {
  if (!result.value?.video_id) return;
  try {
    const blob = await downloadVideo(result.value.video_id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `detected_video_${result.value.video_id.slice(0, 8)}.mp4`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    ElMessage.success("下载成功");
  } catch (e) {
    ElMessage.error("下载失败");
  }
};

const resetAll = () => {
  result.value = null;
  processing.value = false;
};

const onModelChange = async (key) => {
  try {
    const res = await switchVideoModel(key);
    if (res.success) ElMessage.success(res.message);
  } catch (e) { ElMessage.error("模型切换失败"); }
};

onMounted(async () => {
  try {
    const res = await getVideoModels();
    if (res.data && res.data.length) {
      availableModels.value = res.data;
      const loaded = res.data.find(m => m.loaded);
      selectedModel.value = loaded ? loaded.key : res.data[0].key;
    }
  } catch (e) { /* defaults */ }
});
</script>

<style scoped>
.video-page { width: 100%; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.header-left .page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.header-left .page-subtitle { font-size: 13px; color: var(--text-muted); }

.model-config-box {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 14px; background: var(--bg-card);
  border: 1px solid var(--border-color); border-radius: var(--radius-md);
}
.config-label { font-size: 11px; color: var(--accent); font-weight: 700; white-space: nowrap; }
.model-select { width: 200px; }

.hidden-input { display: none; }

.upload-zone {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 64px 20px; margin-bottom: 20px;
  background: var(--bg-card); border: 2px dashed var(--border-light);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;
}
.upload-zone:hover { border-color: var(--accent); background: var(--bg-card-hover); }
.upload-text { font-size: 15px; font-weight: 600; color: var(--text-secondary); }
.upload-hint { font-size: 12px; color: var(--text-muted); }

.processing-card {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 60px 20px; background: var(--bg-card);
  border: 1px solid var(--border-color); border-radius: var(--radius-lg);
  margin-bottom: 20px;
}
.loader { width: 36px; height: 36px; border: 3px solid var(--border-color); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.processing-text { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.processing-hint { font-size: 13px; color: var(--text-muted); }

.download-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
  padding: 10px 16px; background: var(--bg-card);
  border: 1px solid var(--accent-dim); border-radius: var(--radius-md);
}
.download-bar-label { font-size: 12px; color: var(--accent); font-weight: 600; }

.result-info-row { display: flex; gap: 20px; margin-bottom: 16px; }

.info-card {
  width: 260px; flex-shrink: 0;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 16px;
}
.info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-color); }
.info-row:last-child { border-bottom: none; }
.info-label { font-size: 13px; color: var(--text-muted); }
.info-value { font-size: 13px; color: var(--text-primary); font-weight: 500; }
.info-value.accent { color: var(--accent); }
.info-value.mono { font-family: var(--mono); }

.result-card {
  flex: 1; max-height: 360px; overflow-y: auto;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 16px;
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.card-badge { padding: 1px 8px; border-radius: 10px; background: var(--accent-dim); color: var(--accent); font-size: 12px; font-family: var(--mono); }
.box-empty { text-align: center; padding: 40px 0; color: var(--text-muted); font-size: 13px; }

.class-stats { display: flex; flex-direction: column; gap: 6px; }
.stat-row { display: flex; align-items: center; gap: 8px; }
.stat-idx { font-family: var(--mono); font-size: 11px; color: var(--text-muted); min-width: 20px; }
.stat-name { font-size: 13px; color: var(--text-primary); min-width: 80px; }
.stat-count { font-family: var(--mono); font-size: 12px; color: var(--accent); min-width: 40px; }
.stat-bar-track { flex: 1; height: 8px; background: var(--bg-input); border-radius: 4px; overflow: hidden; }
.stat-bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-dim)); border-radius: 4px; transition: width 0.4s; }

.reset-btn { width: 100%; height: 40px; border-radius: var(--radius-md); }

.empty-state { display: flex; flex-direction: column; align-items: center; padding: 80px 0; gap: 12px; color: var(--text-muted); }

.model-option { display: flex; flex-direction: column; gap: 2px; }
.model-opt-name { font-size: 13px; font-weight: 600; }
.model-opt-desc { font-size: 11px; color: var(--text-muted); }
</style>
