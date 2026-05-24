<template>
  <div class="cd-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ $t('nav.changeDetection') }}</h1>
        <p class="page-subtitle">{{ $t('changeDetection.subtitle') }}</p>
      </div>
      <div class="header-right">
        <div class="model-config-box">
          <span class="config-label">{{ $t('changeDetection.modelConfig') }}</span>
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
      <div
        v-for="tab in functionTabs"
        :key="tab.key"
        class="function-tab"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        <el-icon :size="20" class="tab-icon"><component :is="tab.icon" /></el-icon>
        <div class="tab-content">
          <span class="tab-text">{{ tab.name }}</span>
          <span class="tab-desc">{{ tab.desc }}</span>
        </div>
      </div>
    </div>

    <!-- 上传区域 — 单图 -->
    <div class="upload-row" v-if="activeTab === 'single'">
      <div class="upload-zone" @click="handleUploadClick('a')">
        <input ref="inputA" type="file" accept="image/*,.tif,.tiff" class="hidden-input" @change.stop="(e) => handleFileSingle(e, 'A')" />
        <el-icon :size="28"><Picture /></el-icon>
        <span class="upload-text">{{ $t('changeDetection.phase1') }}</span>
        <span class="upload-hint">{{ fileAName || 'JPG / PNG / TIF' }}</span>
      </div>
      <div class="upload-zone" @click="handleUploadClick('b')">
        <input ref="inputB" type="file" accept="image/*,.tif,.tiff" class="hidden-input" @change.stop="(e) => handleFileSingle(e, 'B')" />
        <el-icon :size="28"><Picture /></el-icon>
        <span class="upload-text">{{ $t('changeDetection.phase2') }}</span>
        <span class="upload-hint">{{ fileBName || 'JPG / PNG / TIF' }}</span>
      </div>
    </div>

    <!-- 上传区域 — 批量 -->
    <div class="upload-row" v-if="activeTab === 'batch'">
      <div class="upload-zone" @click="handleUploadClick('folderA')">
        <input ref="folderA" type="file" accept="image/*,.tif,.tiff" webkitdirectory class="hidden-input" @change.stop="(e) => handleFolder(e, 'A')" />
        <el-icon :size="28"><FolderOpened /></el-icon>
        <span class="upload-text">{{ $t('changeDetection.phase1Folder') }}</span>
        <span class="upload-hint">{{ folderACount ? folderACount + ' ' + $t('statistics.images') : $t('changeDetection.selectFolder') }}</span>
      </div>
      <div class="upload-zone" @click="handleUploadClick('folderB')">
        <input ref="folderB" type="file" accept="image/*,.tif,.tiff" webkitdirectory class="hidden-input" @change.stop="(e) => handleFolder(e, 'B')" />
        <el-icon :size="28"><FolderOpened /></el-icon>
        <span class="upload-text">{{ $t('changeDetection.phase2Folder') }}</span>
        <span class="upload-hint">{{ folderBCount ? folderBCount + ' ' + $t('statistics.images') : $t('changeDetection.selectFolder') }}</span>
      </div>
    </div>

    <!-- 下载栏 -->
    <div class="download-bar" v-if="(activeTab === 'single' && singleResultUrl) || (activeTab === 'batch' && batchDone > 0)">
      <span class="download-bar-label">{{ $t('changeDetection.resultDownload') }}</span>
      <el-button v-if="activeTab === 'single' && singleResultUrl" size="small" type="primary" @click="downloadResult(singleResultUrl)">
        <el-icon :size="14"><Download /></el-icon> {{ $t('changeDetection.downloadResult') }}
      </el-button>
      <el-button v-if="activeTab === 'batch' && batchDone > 0" size="small" type="primary" @click="downloadBatchResults">
        <el-icon :size="14"><Download /></el-icon> {{ $t('changeDetection.downloadAllResults') }} ({{ batchDone }}{{ $t('statistics.images') }} · ZIP)
      </el-button>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">

      <!-- ====== 单图模式 ====== -->
      <template v-if="activeTab === 'single'">
        <div class="left-panel">
          <div class="panel-topbar">
            <span class="panel-label">{{ $t('nav.changeDetection') }}</span>
            <div class="panel-status">
              <span v-if="loading" class="status processing"><span class="status-dot"></span>{{ $t('changeDetection.detecting') }}</span>
              <span v-else-if="singleResult" class="status done"><span class="status-dot"></span>{{ $t('changeDetection.detectionDone') }}</span>
              <span v-else class="status idle"><span class="status-dot"></span>{{ $t('changeDetection.waitingUpload') }}</span>
              <el-button v-if="hasSingleState" size="small" @click="resetSingle" circle><el-icon :size="14"><Close /></el-icon></el-button>
            </div>
          </div>

          <!-- 三栏预览：时相1 + 时相2 + 变化结果 -->
          <div class="image-compare-triple" v-if="hasSingleState">
            <div class="image-card">
              <img v-if="singleImgA" :src="singleImgA" class="compare-image" />
              <div v-else class="placeholder"><el-icon :size="40"><Picture /></el-icon><span>{{ $t('changeDetection.phase1') }}</span></div>
              <div class="image-label">{{ $t('changeDetection.phase1') }}</div>
            </div>
            <div class="image-card">
              <img v-if="singleImgB" :src="singleImgB" class="compare-image" />
              <div v-else class="placeholder"><el-icon :size="40"><Picture /></el-icon><span>{{ $t('changeDetection.phase2') }}</span></div>
              <div class="image-label">{{ $t('changeDetection.phase2') }}</div>
            </div>
            <div class="image-card">
              <img v-if="singleResultUrl" :src="singleResultUrl" class="compare-image" />
              <div v-else class="placeholder"><el-icon :size="40"><Aim /></el-icon><span>{{ $t('changeDetection.changeResult') }}</span></div>
              <div class="image-label result-label">{{ $t('changeDetection.changeAreaLabel') }}</div>
              <div v-if="singleResult" class="detection-badge">{{ (singleResult.change_ratio * 100).toFixed(1) }}%</div>
            </div>
          </div>

          <div v-else class="batch-empty">
            <el-icon :size="48"><Picture /></el-icon>
            <p>{{ $t('changeDetection.uploadTwoImages') }}</p>
          </div>
        </div>

        <div class="right-panel" v-if="singleResult">
          <div class="info-card">
            <div class="info-row"><span class="info-label">{{ $t('changeDetection.modelNameLabel') }}</span><span class="info-value accent">{{ singleResult.model_name }}</span></div>
            <div class="info-row"><span class="info-label">{{ $t('changeDetection.detectionTimeLabel') }}</span><span class="info-value mono">{{ singleResult.detection_time }}s</span></div>
            <div class="info-row"><span class="info-label">{{ $t('changeDetection.changeRatioLabel') }}</span><span class="info-value mono">{{ (singleResult.change_ratio * 100).toFixed(2) }}%</span></div>
          </div>
          <el-button class="reset-btn" @click="runSingleDetection"><el-icon><Refresh /></el-icon>{{ $t('changeDetection.reDetect') }}</el-button>
        </div>
      </template>

      <!-- ====== 批量模式 ====== -->
      <template v-else>
        <div class="left-panel">
          <div class="panel-topbar">
            <span class="panel-label">{{ $t('changeDetection.batchDetection') }} <span class="panel-count">{{ batchPairs.length }}{{ $t('statistics.pairs') }}</span></span>
            <div class="panel-status">
              <span v-if="batchLoading" class="status processing"><span class="status-dot"></span>{{ $t('changeDetection.detectingProgress') }} {{ batchDone }}/{{ batchPairs.length }}...</span>
              <span v-else-if="batchDone > 0" class="status done"><span class="status-dot"></span>{{ $t('changeDetection.allDone') }} · {{ batchTotalTime }}s</span>
              <span v-else class="status idle"><span class="status-dot"></span>{{ $t('changeDetection.waitingUpload') }}</span>
              <el-button v-if="batchPairs.length" size="small" @click="resetBatch" circle><el-icon :size="14"><Close /></el-icon></el-button>
            </div>
          </div>

          <div class="batch-grid" v-if="batchPairs.length">
            <div
              v-for="(item, idx) in batchPairs"
              :key="idx"
              class="batch-card"
              :class="{ 'has-result': item.done }"
            >
              <img v-if="item.result_url" :src="item.result_url" class="batch-thumb" />
              <div v-else class="batch-thumb-placeholder">
                <el-icon :size="28"><Picture /></el-icon>
              </div>
              <div class="batch-file-name">{{ item.filename_a }} ↔ {{ item.filename_b }}</div>
              <div v-if="item.done" class="batch-card-badge">{{ (item.change_ratio * 100).toFixed(1) }}%</div>
              <div v-if="!item.done && batchLoading && batchCurrentIdx === idx" class="batch-card-loading">
                <span class="mini-loader"></span>
              </div>
            </div>
          </div>

          <div v-else class="batch-empty">
            <el-icon :size="48"><FolderOpened /></el-icon>
            <p>{{ $t('changeDetection.uploadTwoFolders') }}</p>
          </div>
        </div>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { useI18n } from "vue-i18n";
import { ElMessage } from "element-plus";
import { detectChangeSingle, detectChangeBatch, getChangeModels, switchChangeModel, previewImage, downloadChangeResultsZip } from "../api/detection";
import { requireLogin } from "../utils/request";
import { getSession, authVersion } from "../utils/auth";
import { useChangeDetectionStore } from "../stores/changeDetectionStore";
import { Picture, Aim, Close, FolderOpened, Refresh, Download } from "@element-plus/icons-vue";

const { t } = useI18n();
const store = useChangeDetectionStore();

// 退出登录后自动清空检测状态
watch(authVersion, () => {
  if (!getSession()) {
    store.clearAll();
  }
});

const availableModels = ref([]);
const loading = ref(false);
const batchLoading = ref(false);

// ── 不可序列化的 File / DOM 引用（本地保留）──
const fileA = ref(null);
const fileB = ref(null);
const filesAList = ref([]);
const filesBList = ref([]);
const inputA = ref(null);
const inputB = ref(null);
const folderA = ref(null);
const folderB = ref(null);

// 计算属性代理 store 以便模板使用
const selectedModel = computed({ get: () => store.selectedModel, set: (v) => { store.selectedModel = v; } });
const activeTab = computed({ get: () => store.activeTab, set: (v) => { store.activeTab = v; } });
const fileAName = computed({ get: () => store.fileAName, set: (v) => { store.fileAName = v; } });
const fileBName = computed({ get: () => store.fileBName, set: (v) => { store.fileBName = v; } });
const singleImgA = computed({ get: () => store.singleImgA, set: (v) => { store.singleImgA = v; } });
const singleImgB = computed({ get: () => store.singleImgB, set: (v) => { store.singleImgB = v; } });
const singleResultUrl = computed({ get: () => store.singleResultUrl, set: (v) => { store.singleResultUrl = v; } });
const singleResult = computed({ get: () => store.singleResult, set: (v) => { store.singleResult = v; } });
const batchPairs = computed({ get: () => store.batchPairs, set: (v) => { store.batchPairs = v; } });
const batchDone = computed({ get: () => store.batchDone, set: (v) => { store.batchDone = v; } });
const batchCurrentIdx = computed({ get: () => store.batchCurrentIdx, set: (v) => { store.batchCurrentIdx = v; } });
const batchTotalTime = computed({ get: () => store.batchTotalTime, set: (v) => { store.batchTotalTime = v; } });
const folderACount = computed({ get: () => store.folderACount, set: (v) => { store.folderACount = v; } });
const folderBCount = computed({ get: () => store.folderBCount, set: (v) => { store.folderBCount = v; } });
const hasSingleState = computed(() => !!(
  singleResult.value ||
  singleImgA.value ||
  singleImgB.value ||
  fileAName.value ||
  fileBName.value
));

const functionTabs = computed(() => [
  { key: "single", name: t("changeDetection.singleMode"), desc: t("changeDetection.singleModeDesc"), icon: Picture },
  { key: "batch", name: t("changeDetection.batchMode"), desc: t("changeDetection.batchModeDesc"), icon: FolderOpened },
]);

const resolveUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("blob:")) return url;
  return `http://localhost:8000${url}`;
};

// ── 上传入口 ──
const handleUploadClick = (which) => {
  if (getSession()) {
    const refMap = { a: inputA, b: inputB, folderA, folderB };
    refMap[which]?.value?.click();
    return
  }
  requireLogin()
};

// ── 单图（不再重复检查登录）──
const setPreview = async (f, which) => {
  const isTif = f.name.toLowerCase().endsWith('.tif') || f.name.toLowerCase().endsWith('.tiff')
  if (isTif) {
    const fd = new FormData()
    fd.append('file', f)
    try {
      const previewRes = await previewImage(fd)
      if (previewRes.success) {
        const url = resolveUrl(previewRes.data.preview_url)
        if (which === 'A') singleImgA.value = url
        else singleImgB.value = url
      } else {
        if (which === 'A') singleImgA.value = ''
        else singleImgB.value = ''
      }
    } catch { /* 预览失败不影响检测 */ }
  } else {
    if (which === 'A') singleImgA.value = URL.createObjectURL(f)
    else singleImgB.value = URL.createObjectURL(f)
  }
}

const handleFileSingle = async (event, which) => {
  const f = event.target.files[0];
  if (!f) return;
  event.target.value = "";

  if (which === "A") { fileA.value = f; fileAName.value = f.name; setPreview(f, 'A'); }
  else { fileB.value = f; fileBName.value = f.name; setPreview(f, 'B'); }

  if (fileA.value && fileB.value) runSingleDetection();
};

const runSingleDetection = async () => {
  const fd = new FormData();
  fd.append("file_a", fileA.value);
  fd.append("file_b", fileB.value);
  fd.append("model_key", selectedModel.value);
  loading.value = true;
  try {
    const res = await detectChangeSingle(fd);
    if (res.success) {
      singleResult.value = res.data;
      singleResultUrl.value = resolveUrl(res.data.result_url);
      singleImgA.value = resolveUrl(res.data.image_a_url);
      singleImgB.value = resolveUrl(res.data.image_b_url);
    }
  } catch (e) {
    ElMessage.error(t("changeDetection.detectFailed"));
  } finally { loading.value = false; }
};

const resetSingle = () => {
  fileA.value = null; fileB.value = null;
  store.resetSingle();
};

const downloadResult = async (url) => {
  try {
    const resp = await fetch(url);
    const blob = await resp.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `change_detection_${Date.now()}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
    ElMessage.success(t("changeDetection.downloadSuccess"));
  } catch (e) {
    ElMessage.error(t("changeDetection.downloadFailed"));
  }
};

// ── 批量 ──
const handleFolder = async (event, which) => {
  const files = Array.from(event.target.files).filter(f => /\.(jpg|jpeg|png|bmp|tif|tiff)$/i.test(f.name));
  files.sort((a, b) => a.name.localeCompare(b.name));
  event.target.value = "";

  if (which === "A") { filesAList.value = files; folderACount.value = files.length; }
  else { filesBList.value = files; folderBCount.value = files.length; }

  if (filesAList.value.length && filesBList.value.length) runBatchDetection();
};

const runBatchDetection = async () => {
  const count = Math.min(filesAList.value.length, filesBList.value.length);
  batchPairs.value = [];
  for (let i = 0; i < count; i++) {
    batchPairs.value.push({
      filename_a: filesAList.value[i].name,
      filename_b: filesBList.value[i].name,
      file_a: filesAList.value[i],
      file_b: filesBList.value[i],
      done: false, result_url: "", change_ratio: 0,
      detection_id: "",
    });
  }
  batchDone.value = 0;
  batchLoading.value = true;
  const tStart = performance.now();

  for (let i = 0; i < batchPairs.value.length; i++) {
    batchCurrentIdx.value = i;
    const fd = new FormData();
    fd.append("file_a", batchPairs.value[i].file_a);
    fd.append("file_b", batchPairs.value[i].file_b);
    fd.append("model_key", selectedModel.value);
    try {
      const res = await detectChangeSingle(fd);
      if (res.success) {
        batchPairs.value[i].done = true;
        batchPairs.value[i].result_url = resolveUrl(res.data.result_url);
        batchPairs.value[i].change_ratio = res.data.change_ratio;
        batchPairs.value[i].detection_id = res.data.detection_id;
      }
    } catch (e) { /* skip failed */ }
    batchDone.value = i + 1;
  }

  batchTotalTime.value = ((performance.now() - tStart) / 1000).toFixed(1);
  batchLoading.value = false;
  batchCurrentIdx.value = -1;
};

const downloadBatchResults = async () => {
  const ids = batchPairs.value.filter(f => f.detection_id).map(f => f.detection_id);
  if (!ids.length) { ElMessage.error(t("changeDetection.noResults")); return; }
  try {
    const blob = await downloadChangeResultsZip(ids);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `change_detection_results_${Date.now()}.zip`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    ElMessage.success(t("changeDetection.downloadedN", { n: ids.length }));
  } catch (e) {
    ElMessage.error(t("changeDetection.batchDownloadFailed"));
  }
};

const resetBatch = () => {
  filesAList.value = []; filesBList.value = [];
  store.resetBatch();
};

// ── 模型 ──
onMounted(async () => {
  try {
    const res = await getChangeModels();
    if (res.data && res.data.length) {
      availableModels.value = res.data;
      const loaded = res.data.find(m => m.loaded);
      store.selectedModel = loaded ? loaded.key : res.data[0].key;
    }
  } catch (e) { /* defaults */ }
});

const onModelChange = async (key) => {
  try {
    const res = await switchChangeModel(key);
    if (res.success) ElMessage.success(res.message);
  } catch (e) { ElMessage.error(t("changeDetection.modelSwitchFailed")); }
};
</script>

<style scoped>
.cd-page { width: 100%; }

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

.function-tabs { display: flex; gap: 10px; margin-bottom: 16px; }
.function-tab {
  flex: 1; display: flex; align-items: center; padding: 14px 16px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;
}
.function-tab:hover { border-color: var(--border-light); }
.function-tab.active { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent-glow); }
.tab-icon { color: var(--accent); margin-right: 12px; flex-shrink: 0; }
.tab-content { display: flex; flex-direction: column; }
.tab-text { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.tab-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.hidden-input { display: none; }

.upload-row { display: flex; gap: 16px; margin-bottom: 20px; }

.upload-zone {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 40px 20px;
  background: var(--bg-card); border: 2px dashed var(--border-light);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;
}
.upload-zone:hover { border-color: var(--accent); background: var(--bg-card-hover); }
.upload-text { font-size: 15px; font-weight: 600; color: var(--text-secondary); }
.upload-hint { font-size: 12px; color: var(--text-muted); }

.main-content { display: flex; gap: 20px; }

.left-panel {
  flex: 1; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 20px;
}
.panel-topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.panel-count { font-size: 12px; color: var(--text-muted); margin-left: 8px; font-weight: 400; }
.panel-status { display: flex; align-items: center; gap: 10px; }
.panel-status .status { display: flex; align-items: center; gap: 6px; font-size: 12px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status.processing .status-dot { background: var(--warning); animation: pulse 1.5s ease-in-out infinite; }
.status.done .status-dot { background: var(--accent); box-shadow: 0 0 6px var(--accent-glow); }
.status.idle .status-dot { background: var(--text-muted); }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

/* 下载栏 */
.download-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
  padding: 10px 16px; background: var(--bg-card);
  border: 1px solid var(--accent-dim); border-radius: var(--radius-md);
}
.download-bar-label { font-size: 12px; color: var(--accent); font-weight: 600; white-space: nowrap; }

.image-compare-triple { display: flex; gap: 10px; height: 320px; }
.placeholder { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-muted); font-size: 13px; }
.image-card {
  flex: 1; position: relative; border-radius: var(--radius-md);
  overflow: hidden; background: var(--bg-input);
  border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center;
}
.compare-image { width: 100%; height: 100%; object-fit: cover; }
.image-label {
  position: absolute; top: 10px; left: 10px;
  padding: 4px 10px; background: rgba(0,0,0,0.85); color: #fff;
  font-size: 11px; font-weight: 700; border-radius: 4px;
  font-family: var(--mono);
}
.result-label { color: var(--accent); background: rgba(0,0,0,0.9); }
.detection-badge {
  position: absolute; top: 10px; right: 10px;
  padding: 4px 12px; border-radius: 12px;
  background: var(--accent); color: var(--on-accent); font-weight: 700; font-size: 13px;
  font-family: var(--mono);
}
.download-btn {
  position: absolute; bottom: 12px; right: 12px;
  background: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  color: var(--accent) !important;
  opacity: 0; transition: opacity 0.2s;
}
.image-card:hover .download-btn { opacity: 1; }

.right-panel { width: 280px; display: flex; flex-direction: column; gap: 14px; flex-shrink: 0; }
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

.reset-btn { width: 100%; height: 40px; border-radius: var(--radius-md); }

/* batch */
.batch-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
}
.batch-card {
  background: var(--bg-input); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); overflow: hidden; transition: all 0.2s; position: relative;
}
.batch-card.has-result { border-color: #ff444466; }
.batch-thumb { width: 100%; height: 120px; object-fit: cover; display: block; }
.batch-thumb-placeholder {
  width: 100%; height: 120px; display: flex; align-items: center; justify-content: center;
  background: var(--bg-deep); color: var(--text-muted);
}
.batch-file-name {
  padding: 6px 8px; font-size: 10px; color: var(--text-secondary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.batch-card-badge {
  position: absolute; top: 6px; right: 6px;
  padding: 2px 8px; border-radius: 10px;
  background: #ff4444; color: #fff; font-size: 10px; font-weight: 700;
}
.batch-card-loading {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.6);
}
.mini-loader {
  width: 24px; height: 24px; border: 2px solid var(--border-light);
  border-top-color: var(--accent); border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.batch-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; color: var(--text-muted);
}

.model-option { display: flex; flex-direction: column; gap: 2px; }
.model-opt-name { font-size: 13px; font-weight: 600; }
.model-opt-desc { font-size: 11px; color: var(--text-muted); }
</style>
