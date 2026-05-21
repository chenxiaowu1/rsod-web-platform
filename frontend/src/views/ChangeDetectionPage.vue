<template>
  <div class="cd-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">变化检测</h1>
        <p class="page-subtitle">上传双时相遥感影像，识别变化区域</p>
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
      <div class="upload-zone" @click="$refs.inputA.click()">
        <input ref="inputA" type="file" accept="image/*,.tif,.tiff" class="hidden-input" @change.stop="(e) => handleFileSingle(e, 'A')" />
        <el-icon :size="28"><Picture /></el-icon>
        <span class="upload-text">时相 1 (旧图)</span>
        <span class="upload-hint">{{ fileAName || 'JPG / PNG / TIF' }}</span>
      </div>
      <div class="upload-zone" @click="$refs.inputB.click()">
        <input ref="inputB" type="file" accept="image/*,.tif,.tiff" class="hidden-input" @change.stop="(e) => handleFileSingle(e, 'B')" />
        <el-icon :size="28"><Picture /></el-icon>
        <span class="upload-text">时相 2 (新图)</span>
        <span class="upload-hint">{{ fileBName || 'JPG / PNG / TIF' }}</span>
      </div>
    </div>

    <!-- 上传区域 — 批量 -->
    <div class="upload-row" v-if="activeTab === 'batch'">
      <div class="upload-zone" @click="$refs.folderA.click()">
        <input ref="folderA" type="file" accept="image/*,.tif,.tiff" webkitdirectory class="hidden-input" @change.stop="(e) => handleFolder(e, 'A')" />
        <el-icon :size="28"><FolderOpened /></el-icon>
        <span class="upload-text">时相 1 文件夹</span>
        <span class="upload-hint">{{ folderACount ? folderACount + ' 张' : '选择整个文件夹' }}</span>
      </div>
      <div class="upload-zone" @click="$refs.folderB.click()">
        <input ref="folderB" type="file" accept="image/*,.tif,.tiff" webkitdirectory class="hidden-input" @change.stop="(e) => handleFolder(e, 'B')" />
        <el-icon :size="28"><FolderOpened /></el-icon>
        <span class="upload-text">时相 2 文件夹</span>
        <span class="upload-hint">{{ folderBCount ? folderBCount + ' 张' : '选择整个文件夹' }}</span>
      </div>
    </div>

    <!-- 下载栏 -->
    <div class="download-bar" v-if="(activeTab === 'single' && singleResultUrl) || (activeTab === 'batch' && batchDone > 0)">
      <span class="download-bar-label">结果图下载</span>
      <el-button v-if="activeTab === 'single' && singleResultUrl" size="small" type="primary" @click="downloadResult(singleResultUrl)">
        <el-icon :size="14"><Download /></el-icon> 下载结果图
      </el-button>
      <el-button v-if="activeTab === 'batch' && batchDone > 0" size="small" type="primary" @click="downloadBatchResults">
        <el-icon :size="14"><Download /></el-icon> 下载全部结果图 ({{ batchDone }} 张 · ZIP)
      </el-button>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">

      <!-- ====== 单图模式 ====== -->
      <template v-if="activeTab === 'single'">
        <div class="left-panel">
          <div class="panel-topbar">
            <span class="panel-label">变化检测</span>
            <div class="panel-status">
              <span v-if="loading" class="status processing"><span class="status-dot"></span>检测中...</span>
              <span v-else-if="singleResult" class="status done"><span class="status-dot"></span>检测完成</span>
              <span v-else class="status idle"><span class="status-dot"></span>等待上传</span>
              <el-button v-if="singleResult" size="small" @click="resetSingle" circle><el-icon :size="14"><Close /></el-icon></el-button>
            </div>
          </div>

          <!-- 三栏预览：时相1 + 时相2 + 变化结果 -->
          <div class="image-compare-triple" v-if="singleResult || fileA || fileB">
            <div class="image-card">
              <img v-if="singleImgA" :src="singleImgA" class="compare-image" />
              <div v-else class="placeholder"><el-icon :size="40"><Picture /></el-icon><span>时相 1</span></div>
              <div class="image-label">时相 1</div>
            </div>
            <div class="image-card">
              <img v-if="singleImgB" :src="singleImgB" class="compare-image" />
              <div v-else class="placeholder"><el-icon :size="40"><Picture /></el-icon><span>时相 2</span></div>
              <div class="image-label">时相 2</div>
            </div>
            <div class="image-card">
              <img v-if="singleResultUrl" :src="singleResultUrl" class="compare-image" />
              <div v-else class="placeholder"><el-icon :size="40"><Aim /></el-icon><span>变化结果</span></div>
              <div class="image-label result-label">变化区域</div>
              <div v-if="singleResult" class="detection-badge">{{ (singleResult.change_ratio * 100).toFixed(1) }}%</div>
            </div>
          </div>

          <div v-else class="batch-empty">
            <el-icon :size="48"><Picture /></el-icon>
            <p>上传两张不同时相的遥感影像进行变化检测</p>
          </div>
        </div>

        <div class="right-panel" v-if="singleResult">
          <div class="info-card">
            <div class="info-row"><span class="info-label">检测模型</span><span class="info-value accent">{{ singleResult.model_name }}</span></div>
            <div class="info-row"><span class="info-label">检测耗时</span><span class="info-value mono">{{ singleResult.detection_time }}s</span></div>
            <div class="info-row"><span class="info-label">变化比例</span><span class="info-value mono">{{ (singleResult.change_ratio * 100).toFixed(2) }}%</span></div>
          </div>
          <el-button class="reset-btn" @click="resetSingle"><el-icon><Refresh /></el-icon>重新检测</el-button>
        </div>
      </template>

      <!-- ====== 批量模式 ====== -->
      <template v-else>
        <div class="left-panel">
          <div class="panel-topbar">
            <span class="panel-label">批量检测 <span class="panel-count">共 {{ batchPairs.length }} 对</span></span>
            <div class="panel-status">
              <span v-if="batchLoading" class="status processing"><span class="status-dot"></span>检测中 {{ batchDone }}/{{ batchPairs.length }}...</span>
              <span v-else-if="batchDone > 0" class="status done"><span class="status-dot"></span>全部完成 · {{ batchTotalTime }}s</span>
              <span v-else class="status idle"><span class="status-dot"></span>等待上传</span>
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
            <p>上传两个文件夹，按文件名排序配对检测</p>
          </div>
        </div>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { detectChangeSingle, detectChangeBatch, getChangeModels, switchChangeModel } from "../api/detection";
import { requireLogin } from "../utils/request";
import { Picture, Aim, Close, FolderOpened, Refresh, Download } from "@element-plus/icons-vue";

const selectedModel = ref("");
const availableModels = ref([]);
const activeTab = ref("single");
const loading = ref(false);

// ── 单图 ──
const fileA = ref(null);
const fileB = ref(null);
const fileAName = ref("");
const fileBName = ref("");
const singleImgA = ref("");
const singleImgB = ref("");
const singleResultUrl = ref("");
const singleResult = ref(null);

// ── 批量 ──
const batchPairs = ref([]);
const batchLoading = ref(false);
const batchDone = ref(0);
const batchCurrentIdx = ref(-1);
const batchTotalTime = ref(0);
const folderACount = ref(0);
const folderBCount = ref(0);
const filesAList = ref([]);
const filesBList = ref([]);

const functionTabs = [
  { key: "single", name: "单图检测", desc: "对比两张遥感影像", icon: Picture },
  { key: "batch", name: "批量检测", desc: "上传两个文件夹", icon: FolderOpened },
];

const resolveUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("blob:")) return url;
  return `http://localhost:8000${url}`;
};

// ── 单图 ──
const handleFileSingle = async (event, which) => {
  const f = event.target.files[0];
  if (!f) return;
  if (!(await requireLogin())) { event.target.value = ""; return; }
  if (which === "A") { fileA.value = f; fileAName.value = f.name; singleImgA.value = URL.createObjectURL(f); }
  else { fileB.value = f; fileBName.value = f.name; singleImgB.value = URL.createObjectURL(f); }

  if (fileA.value && fileB.value) runSingleDetection();
  event.target.value = "";
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
    ElMessage.error("检测失败");
  } finally { loading.value = false; }
};

const resetSingle = () => {
  fileA.value = null; fileB.value = null;
  fileAName.value = ""; fileBName.value = "";
  singleImgA.value = ""; singleImgB.value = "";
  singleResultUrl.value = "";
  singleResult.value = null;
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
    ElMessage.success("下载成功");
  } catch (e) {
    ElMessage.error("下载失败");
  }
};

// ── 批量 ──
const handleFolder = async (event, which) => {
  const files = Array.from(event.target.files).filter(f => /\.(jpg|jpeg|png|bmp|tif|tiff)$/i.test(f.name));
  files.sort((a, b) => a.name.localeCompare(b.name));
  if (!(await requireLogin())) { event.target.value = ""; return; }
  if (which === "A") { filesAList.value = files; folderACount.value = files.length; }
  else { filesBList.value = files; folderBCount.value = files.length; }

  if (filesAList.value.length && filesBList.value.length) runBatchDetection();
  event.target.value = "";
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
      }
    } catch (e) { /* skip failed */ }
    batchDone.value = i + 1;
  }

  batchTotalTime.value = ((performance.now() - tStart) / 1000).toFixed(1);
  batchLoading.value = false;
  batchCurrentIdx.value = -1;
};

const downloadBatchResults = async () => {
  const urls = batchPairs.value.filter(f => f.done && f.result_url).map(f => f.result_url);
  if (!urls.length) { ElMessage.error("没有可下载的结果图"); return; }
  try {
    const blobs = await Promise.all(urls.map(url => fetch(url).then(r => r.blob())));
    // single-file download for each — zip would need a library, so download sequentially
    for (let i = 0; i < blobs.length; i++) {
      const item = batchPairs.value.find(f => f.result_url === urls[i]);
      const name = item ? `change_${item.filename_a}_${item.filename_b}.jpg` : `result_${i}.jpg`;
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blobs[i]);
      a.download = name;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      if (i < blobs.length - 1) await new Promise(r => setTimeout(r, 200));
    }
    ElMessage.success(`已下载 ${blobs.length} 张结果图`);
  } catch (e) {
    ElMessage.error("批量下载失败");
  }
};

const resetBatch = () => {
  batchPairs.value = [];
  batchDone.value = 0;
  folderACount.value = 0; folderBCount.value = 0;
  filesAList.value = []; filesBList.value = [];
};

// ── 模型 ──
onMounted(async () => {
  try {
    const res = await getChangeModels();
    if (res.data && res.data.length) {
      availableModels.value = res.data;
      const loaded = res.data.find(m => m.loaded);
      selectedModel.value = loaded ? loaded.key : res.data[0].key;
    }
  } catch (e) { /* defaults */ }
});

const onModelChange = async (key) => {
  try {
    const res = await switchChangeModel(key);
    if (res.success) ElMessage.success(res.message);
  } catch (e) { ElMessage.error("模型切换失败"); }
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
