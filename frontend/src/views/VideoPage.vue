<template>
  <div class="video-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ $t('nav.video') }}</h1>
        <p class="page-subtitle">{{ activeTab === 'video' ? $t('video.subtitle') : $t('video.cameraSubtitle') }}</p>
      </div>
      <div class="header-right">
        <div class="model-config-box">
          <span class="config-label">{{ $t('video.modelConfig') }}</span>
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

    <!-- 模式切换 -->
    <div class="function-tabs">
      <div v-for="tab in functionTabs" :key="tab.key" class="function-tab"
           :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        <el-icon :size="20" class="tab-icon"><component :is="tab.icon" /></el-icon>
        <div class="tab-content">
          <span class="tab-text">{{ tab.name }}</span>
          <span class="tab-desc">{{ tab.desc }}</span>
        </div>
      </div>
    </div>

    <!-- 上传 / 启动区 -->
    <div class="upload-zone" v-if="activeTab === 'video'" @click="handleUploadClick">
      <input ref="videoInput" type="file" accept="video/*" class="hidden-input"
        @click.stop="(e) => { e.target.value = null; }" @change.stop="handleVideoFile" />
      <el-icon :size="28"><VideoCamera /></el-icon>
      <span class="upload-text">{{ $t('video.clickToUpload') }}</span>
      <span class="upload-hint">{{ $t('video.supportedFormats') }}</span>
    </div>
    <div class="upload-zone" v-if="activeTab === 'camera' && !cameraActive" @click="startCamera">
      <el-icon :size="28"><VideoCamera /></el-icon>
      <span class="upload-text">{{ $t('video.startCamera') }}</span>
      <span class="upload-hint">{{ $t('video.cameraHint') }}</span>
    </div>

    <!-- 统一下载栏 -->
    <div class="download-bar" v-if="(activeTab === 'video' && result && !processing) || (activeTab === 'camera' && cameraSavedResult)">
      <span class="download-bar-label">{{ $t('video.resultDownload') }}</span>
      <el-button v-if="activeTab === 'video' && result && !processing" size="small" type="primary" @click="doDownload">
        <el-icon :size="14"><Download /></el-icon> {{ $t('video.downloadAnnotated') }}
      </el-button>
      <el-button v-if="activeTab === 'camera' && cameraSavedResult" size="small" type="primary" @click="downloadCameraResult">
        <el-icon :size="14"><Download /></el-icon> {{ $t('video.download') }}
      </el-button>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">

      <!-- ====== 视频模式 ====== -->
      <template v-if="activeTab === 'video' && videoFile">
        <div class="left-panel">
          <div class="panel-topbar">
            <span class="panel-label">{{ $t('video.preview') }}</span>
            <div class="panel-status">
              <span v-if="processing" class="status processing"><span class="status-dot"></span>{{ $t('video.detecting') }}</span>
              <span v-else-if="result" class="status done"><span class="status-dot"></span>{{ $t('video.detectionDone') }}</span>
              <span v-else class="status idle"><span class="status-dot"></span>{{ $t('video.ready') }}</span>
              <el-button size="small" @click="resetAll" circle><el-icon :size="14"><Close /></el-icon></el-button>
            </div>
          </div>

          <!-- 视频预览 -->
          <div class="video-preview-wrap">
            <!-- 检测前：原始上传视频 -->
            <video v-if="videoPreviewUrl && (!result || !resultPreviewUrl) && !processing" ref="videoPlayer" :src="videoPreviewUrl" controls
              class="preview-video" />
            <!-- 检测后：结果视频 -->
            <video v-if="resultPreviewUrl && result && !processing" :src="resultPreviewUrl" controls
              class="preview-video" />
            <div v-if="processing" class="processing-overlay">
              <span class="loader"></span>
              <span>{{ $t('video.largeVideoHint') }}</span>
            </div>
          </div>

        </div>

        <div class="right-panel" v-if="result && !processing">
          <div class="info-card">
            <div class="info-row"><span class="info-label">{{ $t('video.modelNameLabel') }}</span><span class="info-value accent">{{ result.model_name }}</span></div>
            <div class="info-row"><span class="info-label">{{ $t('video.processingTime') }}</span><span class="info-value mono">{{ result.detection_time }}s</span></div>
            <div class="info-row"><span class="info-label">{{ $t('video.frameCount') }}</span><span class="info-value mono">{{ result.total_frames }}</span></div>
            <div class="info-row"><span class="info-label">{{ $t('video.objectsDetected') }}</span><span class="info-value mono">{{ result.total_objects }}{{ $t('video.countSuffix') }}</span></div>
            <div class="info-row"><span class="info-label">{{ $t('video.originalFps') }}</span><span class="info-value mono">{{ result.fps_original }} FPS</span></div>
          </div>

          <div class="result-card">
            <div class="card-header">
              <span class="card-title">{{ $t('video.perFrameList') }}</span>
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
            <div v-else class="box-empty">{{ $t('video.noObjects') }}</div>
          </div>

          <el-button class="reset-btn" @click="reDetectVideo"><el-icon><Refresh /></el-icon>{{ $t('video.reDetect') }}</el-button>
        </div>
      </template>

      <!-- ====== 摄像头模式 ====== -->
      <template v-if="activeTab === 'camera' && cameraActive">
        <div class="left-panel">
          <div class="panel-topbar">
            <span class="panel-label">{{ $t('video.cameraLive') }}</span>
            <div class="panel-status">
              <span v-if="cameraDetecting" class="status processing"><span class="status-dot"></span>{{ $t('video.detecting') }}</span>
              <span v-else-if="cameraPaused" class="status idle"><span class="status-dot"></span>{{ $t('video.cameraPaused') }}</span>
              <span v-else class="status idle"><span class="status-dot"></span>{{ $t('video.cameraReady') }}</span>
              <el-button size="small" @click="stopCamera" circle><el-icon :size="14"><Close /></el-icon></el-button>
            </div>
          </div>

          <div class="camera-wrap">
            <video ref="cameraVideo" autoplay muted playsinline class="camera-feed" />
            <canvas ref="cameraCanvas" class="camera-overlay" />
          </div>

          <div class="camera-controls">
            <el-button v-if="!cameraDetecting && !cameraPaused" type="primary" @click="startCameraDetection">
              <el-icon :size="14"><Aim /></el-icon> {{ $t('video.startDetect') }}
            </el-button>
            <template v-if="cameraPaused || cameraDetecting">
              <el-button type="danger" @click="stopAndSaveCamera" :loading="cameraSaving">
                {{ $t('video.stopSave') }}
              </el-button>
              <el-button v-if="cameraDetecting" @click="stopCameraDetection">
                {{ $t('video.pauseDetect') }}
              </el-button>
              <el-button v-if="cameraPaused" type="primary" @click="startCameraDetection">
                {{ $t('video.resumeDetect') }}
              </el-button>
            </template>
          </div>
          <div class="camera-stats" v-if="cameraDetecting || cameraFrames.length">
            <span>{{ $t('video.frames') }}: {{ cameraFrames.length }}</span>
            <span v-if="cameraSavedResult">| {{ $t('video.objects') }}: {{ cameraSavedResult.total_objects }}</span>
          </div>
        </div>

        <div class="right-panel" v-if="cameraBoxes.length > 0 || cameraDetecting">
          <div class="info-card">
            <div class="info-row"><span class="info-label">{{ $t('video.objectsDetected') }}</span><span class="info-value accent mono">{{ cameraBoxes.length }}</span></div>
            <div class="info-row"><span class="info-label">{{ $t('video.modelNameLabel') }}</span><span class="info-value mono">{{ selectedModel }}</span></div>
          </div>

          <div class="result-card">
            <div class="card-header">
              <span class="card-title">{{ $t('video.detectionList') }}</span>
              <span class="card-badge">{{ cameraBoxes.length }}</span>
            </div>
            <div v-if="cameraBoxes.length" class="box-list">
              <div v-for="(box, idx) in cameraBoxes" :key="idx" class="box-item">
                <div class="box-left"><span class="box-index">{{ String(idx+1).padStart(2,'0') }}</span><span class="box-class">{{ box.class_name }}</span></div>
                <span class="box-conf">{{ (box.confidence*100).toFixed(1) }}%</span>
              </div>
            </div>
            <div v-else class="box-empty">{{ $t('video.noObjects') }}</div>
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <div class="empty-state" v-if="(activeTab === 'video' && !videoFile) || (activeTab === 'camera' && !cameraActive)">
        <el-icon :size="48"><VideoCamera /></el-icon>
        <p>{{ activeTab === 'video' ? $t('video.emptyHint') : $t('video.cameraEmptyHint') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useI18n } from "vue-i18n";
import { ElMessage } from "element-plus";
import { detectVideo, getVideoModels, switchVideoModel, downloadVideo, detectVideoFrame, saveCameraSession } from "../api/detection";
import { requireLogin } from "../utils/request";
import { getSession } from "../utils/auth";
import { useVideoStore } from "../stores/videoStore";
import { VideoCamera, Picture, Close, Download, Refresh, Aim } from "@element-plus/icons-vue";

const { t } = useI18n();
const store = useVideoStore();

const activeTab = ref(store._activeTab || "video");
const availableModels = ref([]);
const videoInput = ref(null);

// 计算代理 store
const selectedModel = computed({ get: () => store.selectedModel, set: (v) => { store.selectedModel = v; } });
const result = computed({ get: () => store.result, set: (v) => { store.result = v; } });
const processing = computed({ get: () => store.processing, set: (v) => { store.processing = v; } });

// ── 视频模式 local state ──
const videoFile = ref(null);
const videoPreviewUrl = ref(store._videoPreviewUrl || "");
const resultPreviewUrl = ref(store._resultPreviewUrl || "");

// ── 摄像头模式 ──
const cameraActive = ref(false);
const cameraDetecting = ref(false);
const cameraPaused = ref(false);
const cameraVideo = ref(null);
const cameraCanvas = ref(null);
const cameraBoxes = ref([]);
const cameraSaving = ref(false);
const cameraFrames = ref([]);       // 收集的 base64 帧列表
const cameraSavedResult = ref(null); // 保存后的结果（含 video_id 用于下载）
let cameraStream = null;
let cameraTimer = null;
let cameraFailCount = 0;

const functionTabs = computed(() => [
  { key: "video", name: t("video.tabVideo"), desc: t("video.tabVideoDesc"), icon: VideoCamera },
  { key: "camera", name: t("video.tabCamera"), desc: t("video.tabCameraDesc"), icon: Picture },
]);

const buildVideoPreviewUrl = (videoId) => {
  if (!videoId) return "";
  const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
  return `${base}/video/preview/${videoId}?t=${Date.now()}`;
};

const switchTab = (key) => {
  activeTab.value = key;
  store._activeTab = key;
};

// ── 上传入口 ──
const handleUploadClick = () => {
  if (getSession()) { videoInput.value?.click(); return; }
  requireLogin();
};

const handleVideoFile = (e) => {
  const f = e.target.files[0];
  if (!f) return;
  e.target.value = "";
  videoFile.value = f;
  videoPreviewUrl.value = URL.createObjectURL(f);
  store._videoPreviewUrl = videoPreviewUrl.value;
  store.videoFileName = f.name;

  // 自动开始检测
  startVideoDetection(f);
};

const startVideoDetection = async (f) => {
  const fd = new FormData();
  fd.append("file", f);
  fd.append("model_key", store.selectedModel || "yolo11m");

  store.processing = true;
  store.result = null;
  // 清理旧的结果预览
  if (resultPreviewUrl.value && resultPreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(resultPreviewUrl.value);
  }
  resultPreviewUrl.value = "";
  store._resultPreviewUrl = "";
  try {
    const res = await detectVideo(fd);
    store.result = res;
    // 拉取结果视频 blob 用于预览
    if (res.video_id) {
      try {
        resultPreviewUrl.value = buildVideoPreviewUrl(res.video_id);
        store._resultPreviewUrl = resultPreviewUrl.value;
      } catch (e) { /* 下载失败不影响结果展示 */ }
    }
  } catch (err) {
    ElMessage.error(t("video.detectFailed"));
  } finally {
    store.processing = false;
  }
};

const classStats = computed(() => {
  if (!store.result?.boxes) return [];
  const map = {};
  for (const b of store.result.boxes) {
    const k = b.class_name;
    if (!map[k]) map[k] = 0;
    map[k]++;
  }
  return Object.entries(map).sort((a, b) => b[1] - a[1]).map(([name, count]) => ({ name, count }));
});

const maxCount = computed(() => classStats.value.length ? Math.max(...classStats.value.map(c => c.count)) : 1);
const barW = (val) => (maxCount.value === 0 ? 0 : (val / maxCount.value) * 100);

const doDownload = async () => {
  if (!store.result?.video_id) return;
  try {
    const blob = await downloadVideo(store.result.video_id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `detected_${store.result.video_id.slice(0, 8)}.mp4`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    ElMessage.success(t("video.downloadSuccess"));
  } catch (e) { ElMessage.error(t("video.downloadFailed")); }
};

// ── 摄像头 ──
const startCamera = async () => {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    cameraActive.value = true;
    // 等 DOM 更新后绑定 stream
    setTimeout(() => {
      const el = document.querySelector('.camera-feed');
      if (el && cameraStream) el.srcObject = cameraStream;
    }, 100);
  } catch (e) {
    ElMessage.error(t("video.cameraError") || "无法访问摄像头");
  }
};

const startCameraDetection = () => {
  cameraDetecting.value = true;
  cameraBoxes.value = [];
  cameraFrames.value = [];
  cameraSavedResult.value = null;
  cameraFailCount = 0;
  captureAndDetect();
};

const stopCameraDetection = () => {
  cameraDetecting.value = false;
  cameraPaused.value = true;
  if (cameraTimer) { clearTimeout(cameraTimer); cameraTimer = null; }
};

const stopAndSaveCamera = async () => {
  stopCameraDetection();
  if (!cameraFrames.value.length) { ElMessage.warning("没有可保存的帧"); return; }
  cameraSaving.value = true;
  try {
    const res = await saveCameraSession({
      frames: cameraFrames.value,
      model_key: store.selectedModel || "yolo11m",
      fps: 10,
      filename: `camera_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}`,
    });
    if (res.success) {
      cameraSavedResult.value = res.data;
      ElMessage.success(`摄像头会话已保存: ${res.data.total_frames} 帧, ${res.data.total_objects} 目标`);
    }
  } catch (e) {
    ElMessage.error("摄像头会话保存失败");
  } finally {
    cameraSaving.value = false;
  }
};

const captureAndDetect = async () => {
  if (!cameraDetecting.value) return;
  const videoEl = document.querySelector('.camera-feed');
  const canvasEl = document.querySelector('.camera-overlay');
  if (!videoEl || !canvasEl) { cameraTimer = setTimeout(captureAndDetect, 500); return; }

  const w = videoEl.videoWidth || 640;
  const h = videoEl.videoHeight || 480;
  canvasEl.width = w;
  canvasEl.height = h;
  const ctx = canvasEl.getContext("2d");

  // 抓帧
  const capCanvas = document.createElement("canvas");
  capCanvas.width = w;
  capCanvas.height = h;
  const capCtx = capCanvas.getContext("2d");
  capCtx.drawImage(videoEl, 0, 0, w, h);
  const base64 = capCanvas.toDataURL("image/jpeg", 0.8).split(",")[1];
  cameraFrames.value.push(base64);

  try {
    const res = await detectVideoFrame(base64, store.selectedModel || "yolo11m");
    cameraBoxes.value = res.boxes || [];
    cameraFailCount = 0;

    ctx.clearRect(0, 0, w, h);
    const colors = ["#FF4444", "#44FF44", "#4444FF", "#FFFF44", "#FF44FF", "#44FFFF"];
    for (const b of cameraBoxes.value) {
      const color = colors[b.class_id % colors.length];
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(b.x1, b.y1, b.x2 - b.x1, b.y2 - b.y1);
      ctx.fillStyle = color;
      ctx.font = "14px monospace";
      ctx.fillText(`${b.class_name} ${(b.confidence * 100).toFixed(0)}%`, b.x1, Math.max(b.y1 - 5, 15));
    }
  } catch (e) {
    cameraFailCount++;
    var detail = '';
    if (e.response && e.response.data) {
      detail = e.response.data.detail || e.response.data.message || '';
    }
    if (cameraFailCount === 1 && detail) {
      ElMessage.error(detail);
    }
    if (cameraFailCount >= 5) {
      ElMessage.error(t("video.cameraError") || "帧检测连续失败，请检查视频引擎是否启动");
      stopCameraDetection();
      return;
    }
  }

  cameraTimer = setTimeout(captureAndDetect, 400);
};

const downloadCameraResult = async () => {
  const vid = cameraSavedResult.value?.video_id;
  if (!vid) return;
  try {
    const blob = await downloadVideo(vid);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `camera_detected_${vid.slice(0, 8)}.mp4`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    ElMessage.success(t("video.downloadSuccess"));
  } catch (e) { ElMessage.error(t("video.downloadFailed")); }
};

const stopCamera = () => {
  cameraDetecting.value = false;
  if (cameraTimer) { clearTimeout(cameraTimer); cameraTimer = null; }
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }
  cameraActive.value = false;
  cameraPaused.value = false;
  cameraBoxes.value = [];
  cameraFrames.value = [];
  cameraSavedResult.value = null;
  const videoEl = document.querySelector('.camera-feed');
  if (videoEl) videoEl.srcObject = null;
  const canvasEl = document.querySelector('.camera-overlay');
  if (canvasEl) { const ctx = canvasEl.getContext("2d"); ctx.clearRect(0, 0, canvasEl.width, canvasEl.height); }
};

const reDetectVideo = () => {
  if (!videoFile.value || !(videoFile.value instanceof File)) {
    ElMessage.warning("请重新上传视频文件");
    return;
  }
  startVideoDetection(videoFile.value);
};

// ── Reset ──
const resetAll = () => {
  if (videoPreviewUrl.value && videoPreviewUrl.value.startsWith("blob:")) {
    URL.revokeObjectURL(videoPreviewUrl.value);
  }
  if (resultPreviewUrl.value && resultPreviewUrl.value.startsWith("blob:")) {
    URL.revokeObjectURL(resultPreviewUrl.value);
  }
  videoFile.value = null;
  videoPreviewUrl.value = "";
  resultPreviewUrl.value = "";
  store._videoPreviewUrl = "";
  store._resultPreviewUrl = "";
  store.resetAll();
};

// ── 模型 ──
const onModelChange = async (key) => {
  try {
    const res = await switchVideoModel(key);
    if (res.success) ElMessage.success(res.message);
  } catch (e) { ElMessage.error(t("video.modelSwitchFailed")); }
};

onMounted(async () => {
  try {
    const res = await getVideoModels();
    if (res.data && res.data.length) {
      availableModels.value = res.data;
      const loaded = res.data.find(m => m.loaded);
      store.selectedModel = loaded ? loaded.key : res.data[0].key;
    }
  } catch (e) { /* defaults */ }
  // 恢复 sessionStorage 的视频文件预览 URL
  if (store._videoPreviewUrl) {
    videoPreviewUrl.value = store._videoPreviewUrl;
    if (store.result) videoFile.value = { name: store.videoFileName };
  }
  if (store.result?.video_id) {
    resultPreviewUrl.value = buildVideoPreviewUrl(store.result.video_id);
    store._resultPreviewUrl = resultPreviewUrl.value;
  } else if (store._resultPreviewUrl) {
    resultPreviewUrl.value = store._resultPreviewUrl;
  }
});

onUnmounted(() => {
  stopCamera();
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
  }
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

/* 模式 tabs */
.function-tabs { display: flex; gap: 10px; margin-bottom: 16px; }
.function-tab {
  flex: 1; display: flex; align-items: center; padding: 14px 16px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;
  user-select: none;
}
.function-tab:hover { border-color: var(--border-light); background: var(--bg-card-hover); }
.function-tab.active { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent-glow); }
.tab-icon { color: var(--accent); margin-right: 12px; flex-shrink: 0; }
.tab-content { display: flex; flex-direction: column; }
.tab-text { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.tab-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* 上传区 */
.upload-zone {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 52px 20px; margin-bottom: 20px;
  background: var(--bg-card); border: 2px dashed var(--border-light);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;
}
.upload-zone:hover { border-color: var(--accent); background: var(--bg-card-hover); }
.upload-text { font-size: 15px; font-weight: 600; color: var(--text-secondary); }
.upload-hint { font-size: 12px; color: var(--text-muted); }
.hidden-input { display: none; }

.download-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
  padding: 10px 16px; background: var(--bg-card);
  border: 1px solid var(--accent-dim); border-radius: var(--radius-md);
}
.download-bar-label { font-size: 12px; color: var(--accent); font-weight: 600; white-space: nowrap; }

.main-content { display: flex; gap: 20px; }

/* 左右面板 */
.left-panel {
  flex: 1; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 20px;
}
.panel-topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.panel-status { display: flex; align-items: center; gap: 10px; }
.panel-status .status { display: flex; align-items: center; gap: 6px; font-size: 12px; }
.status .status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status.processing .status-dot { background: var(--warning); animation: pulse 1.5s ease-in-out infinite; }
.status.done .status-dot { background: var(--accent); box-shadow: 0 0 6px var(--accent-glow); }
.status.idle .status-dot { background: var(--text-muted); }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

.video-preview-wrap { position: relative; border-radius: var(--radius-md); overflow: hidden; background: #000; }
.preview-video { width: 100%; max-height: 380px; display: block; }
.processing-overlay {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
  background: rgba(0,0,0,0.7); color: #fff; font-size: 14px;
}
.loader { width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.25); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.result-info-row { margin-top: 14px; }

.right-panel { width: 320px; display: flex; flex-direction: column; gap: 14px; flex-shrink: 0; }

.info-card {
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
  flex: 1; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 16px; overflow-y: auto; max-height: 360px;
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

.box-list { max-height: 260px; overflow-y: auto; }
.box-item { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid var(--border-color); }
.box-item:last-child { border-bottom: none; }
.box-left { display: flex; align-items: center; gap: 10px; }
.box-index { font-family: var(--mono); font-size: 11px; color: var(--text-muted); }
.box-class { font-size: 13px; color: var(--text-primary); }
.box-conf { font-family: var(--mono); font-size: 12px; color: var(--accent); }

.reset-btn { width: 100%; height: 40px; border-radius: var(--radius-md); }

/* 摄像头 */
.camera-wrap { position: relative; border-radius: var(--radius-md); overflow: hidden; background: #000; }
.camera-feed { width: 100%; max-height: 400px; display: block; }
.camera-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
.camera-controls { display: flex; gap: 10px; margin-top: 14px; justify-content: center; flex-wrap: wrap; }
.camera-stats { text-align: center; margin-top: 10px; font-size: 12px; color: var(--text-muted); font-family: var(--mono); }

.empty-state { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 80px 0; gap: 12px; color: var(--text-muted); }

.model-option { display: flex; flex-direction: column; gap: 2px; }
.model-opt-name { font-size: 13px; font-weight: 600; }
.model-opt-desc { font-size: 11px; color: var(--text-muted); }
</style>
