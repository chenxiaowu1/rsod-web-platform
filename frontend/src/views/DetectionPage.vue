<template>
  <div class="detection-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">智能检测</h1>
        <p class="page-subtitle">上传遥感影像，立即识别多类目标</p>
      </div>
      <div class="header-right">
        <div class="model-config-box">
          <span class="config-label">模型配置</span>
          <div class="config-controls">
            <el-popover placement="bottom" :width="280" trigger="hover">
              <template #reference>
                <div class="sahi-toggle" @click="useSahi = !useSahi" :class="{ on: useSahi }">
                  <span class="sahi-dot"></span>
                  <span class="sahi-label">SAHI 切片</span>
                </div>
              </template>
              <div class="sahi-explain">
                <p><strong>SAHI 切片推理</strong> — 将大图切成 640×640 小块逐块检测后合并。</p>
                <p style="margin-top:6px"><span class="tag-rec">推荐开启</span> 影像边长 > 2000px，切片推理提升小目标检出率</p>
                <p style="margin-top:4px"><span class="tag-off">建议关闭</span> 影像边长 ≤ 2000px，标准推理即可</p>
              </div>
            </el-popover>
            <el-select v-model="selectedModel" class="model-select" @change="onModelChange">
              <el-option
                v-for="m in availableModels"
                :key="m.key"
                :label="m.display"
                :value="m.key"
              >
                <div class="model-option">
                  <span class="model-opt-name">{{ m.display }}</span>
                  <span class="model-opt-desc">{{ m.desc }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
        </div>
      </div>
    </div>

    <!-- 阈值调节 -->
    <div class="threshold-bar">
      <div class="threshold-item">
        <span class="threshold-label">置信度阈值</span>
        <el-slider v-model="confThreshold" :min="0.1" :max="0.9" :step="0.05" :show-tooltip="true" class="threshold-slider" />
        <span class="threshold-value">{{ confThreshold.toFixed(2) }}</span>
      </div>
      <div class="threshold-item">
        <span class="threshold-label">IoU 阈值</span>
        <el-slider v-model="iouThreshold" :min="0.1" :max="0.9" :step="0.05" :show-tooltip="true" class="threshold-slider" />
        <span class="threshold-value">{{ iouThreshold.toFixed(2) }}</span>
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

    <!-- 上传区域 -->
    <div class="upload-zone" v-if="activeTab === 'single'" @click="$refs.singleInput.click()">
      <input ref="singleInput" type="file" :accept="functionTabs[0].accept" class="hidden-input" @change.stop="(e) => handleFileChange(e, 'single')" />
      <el-icon :size="28"><Picture /></el-icon>
      <span class="upload-text">点击此处上传遥感影像</span>
      <span class="upload-hint">支持 JPG / PNG / TIF / TIFF</span>
    </div>
    <div class="upload-zone" v-if="activeTab === 'batch'" @click="$refs.folderInput.click()">
      <input ref="folderInput" type="file" :accept="functionTabs[1].accept" webkitdirectory class="hidden-input" @change.stop="(e) => handleFileChange(e, 'batch')" />
      <el-icon :size="28"><FolderOpened /></el-icon>
      <span class="upload-text">点击此处上传整个文件夹</span>
      <span class="upload-hint">支持 JPG / PNG / TIF / TIFF</span>
    </div>

    <!-- 下载栏 -->
    <div class="download-bar" v-if="(activeTab === 'single' && singleResult) || (activeTab === 'batch' && batchDone > 0)">
      <span class="download-bar-label">结果图下载</span>
      <el-button v-if="activeTab === 'single' && singleResultImg" size="small" type="primary" @click="downloadResult(singleResultImg)">
        <el-icon :size="14"><Download /></el-icon> 下载结果图
      </el-button>
      <el-button v-if="activeTab === 'batch' && batchDone > 0" size="small" type="primary" @click="downloadAllResults">
        <el-icon :size="14"><Download /></el-icon> 下载全部结果图 ({{ batchDone }} 张 · ZIP)
      </el-button>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">

      <!-- ====== 单图模式 ====== -->
      <template v-if="activeTab === 'single'">
        <div class="left-panel">
          <div class="panel-topbar">
            <span class="panel-label">检测预览</span>
            <div class="panel-status" style="display:flex;align-items:center;gap:10px">
              <span v-if="loading" class="status processing"><span class="status-dot"></span>检测中...</span>
              <span v-else-if="singleResult" class="status done"><span class="status-dot"></span>检测完成</span>
              <span v-else class="status idle"><span class="status-dot"></span>等待上传</span>
              <el-button v-if="singleResult || singleOriginal" size="small" @click="resetSingle" circle><el-icon :size="14"><Close /></el-icon></el-button>
            </div>
          </div>

          <!-- 有内容：显示原图+结果图对比 -->
          <div class="image-compare-single" v-if="singleResult || singleOriginal">
            <div class="image-card">
              <img v-if="singleOriginal" :src="singleOriginal" class="compare-image" />
              <div v-else class="placeholder"><el-icon :size="40"><Picture /></el-icon><span>原始图片</span></div>
              <div class="image-label">原图</div>
            </div>
            <div class="image-card">
              <img v-if="singleResultImg" :src="singleResultImg" class="compare-image" />
              <div v-else class="placeholder"><el-icon :size="40"><Aim /></el-icon><span>检测结果</span></div>
              <div class="image-label result-label">检测结果</div>
              <div v-if="singleResult" class="detection-badge">{{ singleResult.total_objects }}</div>
              <el-button
                v-if="singleResultImg"
                class="download-btn"
                size="small"
                circle
                @click.stop="downloadResult(singleResultImg)"
              >
                <el-icon :size="16"><Download /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="batch-empty">
            <el-icon :size="48"><Picture /></el-icon>
            <p>点击上方「单图检测」上传遥感影像进行检测</p>
          </div>
        </div>

        <div class="right-panel" v-if="singleResult || singleOriginal">
          <div class="info-card">
            <div class="info-row"><span class="info-label">检测模型</span><span class="info-value accent">{{ selectedModel }}</span></div>
            <div class="info-row"><span class="info-label">检测耗时</span><span class="info-value mono">{{ singleResult?.detection_time || '-' }}s</span></div>
            <div class="info-row"><span class="info-label">检测数量</span><span class="info-value mono">{{ singleResult?.total_objects || 0 }}</span></div>
          </div>
          <div class="export-row" v-if="singleResult && singleResult.boxes.length">
            <span class="export-label">导出标注</span>
            <div class="export-btns">
              <el-button size="small" @click="doExport(singleResult.detection_id, 'coco')">COCO</el-button>
              <el-button size="small" @click="doExport(singleResult.detection_id, 'yolo')">YOLO</el-button>
              <el-button size="small" @click="doExport(singleResult.detection_id, 'geojson')">GeoJSON</el-button>
            </div>
          </div>
          <div class="result-card">
            <div class="card-header"><span class="card-title">识别清单</span><span v-if="singleResult" class="card-badge">{{ singleResult.boxes.length }}</span></div>
            <div v-if="singleResult && singleResult.boxes.length" class="box-list">
              <div v-for="(box, idx) in singleResult.boxes" :key="idx" class="box-item">
                <div class="box-left"><span class="box-index">{{ String(idx+1).padStart(2,'0') }}</span><span class="box-class">{{ box.class_name }}</span></div>
                <span class="box-conf">{{ (box.confidence*100).toFixed(1) }}%</span>
              </div>
            </div>
            <div v-else class="box-empty">暂无检测目标</div>
          </div>
          <el-button class="reset-btn" @click="resetSingle"><el-icon><Refresh /></el-icon>重新检测</el-button>
        </div>
      </template>

      <!-- ====== 批量 / 文件夹模式 ====== -->
      <template v-else>
        <div class="left-panel">
          <!-- 顶部状态栏 -->
          <div class="panel-topbar">
            <span class="panel-label">
              批量检测
              <span class="panel-count">共 {{ batchFiles.length }} 张</span>
            </span>
            <div class="panel-status" style="display:flex;align-items:center;gap:10px">
              <span v-if="batchLoading" class="status processing">
                <span class="status-dot"></span>检测中 {{ batchDone }}/{{ batchFiles.length }}...
                <el-button size="small" type="danger" @click="stopDetection" style="margin-left:10px">停止</el-button>
              </span>
              <span v-else-if="batchDone > 0" class="status done">
                <span class="status-dot"></span>全部完成 · {{ batchTotalObjects }} 个目标 · {{ batchTotalTime }}s
              </span>
              <span v-else class="status idle"><span class="status-dot"></span>等待上传</span>
              <el-button v-if="batchFiles.length" size="small" @click="resetBatch" circle><el-icon :size="14"><Close /></el-icon></el-button>
            </div>
          </div>

          <!-- 图片网格 -->
          <div class="batch-grid" v-if="batchFiles.length">
            <div
              v-for="(item, idx) in batchFiles"
              :key="idx"
              class="batch-card"
              :class="{ 'has-result': item.done, 'selected': batchSelectedIdx === idx }"
              @click="selectBatchItem(idx)"
            >
              <img v-if="item.preview" :src="item.preview" class="batch-thumb" />
              <div v-else class="batch-thumb-placeholder">
                <el-icon :size="28"><Picture /></el-icon>
              </div>
              <div class="batch-file-name">{{ item.filename }}</div>
              <div v-if="item.done" class="batch-card-badge">{{ item.total_objects }}</div>
              <div v-if="!item.done && batchLoading && batchCurrentIdx === idx" class="batch-card-loading">
                <span class="mini-loader"></span>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="batch-empty">
            <el-icon :size="48"><FolderOpened /></el-icon>
            <p>点击上方「批量检测」上传整个文件夹进行检测</p>
          </div>
        </div>

        <!-- 右侧详情（选中某张图后展示） -->
        <div class="right-panel" v-if="selectedBatchItem">
          <div class="info-card">
            <div class="info-row"><span class="info-label">文件名</span><span class="info-value" style="font-size:12px">{{ selectedBatchItem.filename }}</span></div>
            <div class="info-row"><span class="info-label">检测耗时</span><span class="info-value mono">{{ selectedBatchItem.detection_time || '-' }}s</span></div>
            <div class="info-row"><span class="info-label">检测数量</span><span class="info-value mono">{{ selectedBatchItem.total_objects || 0 }}</span></div>
          </div>
          <div class="export-row" v-if="selectedBatchItem.boxes && selectedBatchItem.boxes.length && selectedBatchItem.detection_id">
            <span class="export-label">导出标注</span>
            <div class="export-btns">
              <el-button size="small" @click="doExport(selectedBatchItem.detection_id, 'coco')">COCO</el-button>
              <el-button size="small" @click="doExport(selectedBatchItem.detection_id, 'yolo')">YOLO</el-button>
              <el-button size="small" @click="doExport(selectedBatchItem.detection_id, 'geojson')">GeoJSON</el-button>
            </div>
          </div>

          <!-- 原图 + 结果图对比 -->
          <div class="image-compare-mini" v-if="selectedBatchItem.result_url">
            <div class="mini-img-card">
              <img v-if="selectedBatchItem.original_url" :src="selectedBatchItem.original_url" class="mini-img" />
              <div class="mini-label">原图</div>
            </div>
            <div class="mini-img-card">
              <img :src="selectedBatchItem.result_url" class="mini-img" />
              <div class="mini-label result-label">检测结果</div>
              <el-button
                class="mini-download-btn"
                size="small"
                circle
                @click.stop="downloadResult(selectedBatchItem.result_url)"
              >
                <el-icon :size="14"><Download /></el-icon>
              </el-button>
            </div>
          </div>

          <div class="result-card">
            <div class="card-header"><span class="card-title">识别清单</span><span v-if="selectedBatchItem.boxes" class="card-badge">{{ selectedBatchItem.boxes.length }}</span></div>
            <div v-if="selectedBatchItem.boxes && selectedBatchItem.boxes.length" class="box-list">
              <div v-for="(box, idx) in selectedBatchItem.boxes" :key="idx" class="box-item">
                <div class="box-left"><span class="box-index">{{ String(idx+1).padStart(2,'0') }}</span><span class="box-class">{{ box.class_name }}</span></div>
                <span class="box-conf">{{ (box.confidence*100).toFixed(1) }}%</span>
              </div>
            </div>
            <div v-else class="box-empty">暂无检测目标</div>
          </div>
          <el-button class="reset-btn" @click="resetBatch"><el-icon><Refresh /></el-icon>重新检测</el-button>
        </div>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { detectSingleImage, getModels, switchModel, exportDetection, previewImage, downloadResultsZip } from "../api/detection";
import { requireLogin } from "../utils/request";
import { Picture, Aim, Close, Folder, Refresh, FolderOpened, Download } from "@element-plus/icons-vue";

const selectedModel = ref("");
const availableModels = ref([]);
const activeTab = ref("single");
const loading = ref(false);
const confThreshold = ref(0.5);
const iouThreshold = ref(0.45);
const useSahi = ref(false);
const singleOriginal = ref(sessionStorage.getItem('rsod_single_original') || "");
const singleResultImg = ref(sessionStorage.getItem('rsod_single_result_img') || "");
const singleResult = ref(JSON.parse(sessionStorage.getItem('rsod_single_result') || 'null'));
const singleInput = ref(null);
const folderInput = ref(null);

// ── 批量状态 ──
const batchFiles = ref([]);
const batchLoading = ref(false);
const batchDone = ref(0);
const batchCurrentIdx = ref(-1);
const batchTotalObjects = ref(0);
const batchTotalTime = ref(0);
const batchSelectedIdx = ref(-1);
const stopRequested = ref(false);
const currentAbortController = ref(null);

const functionTabs = [
  { key: "single", name: "单图检测", desc: "识别单张遥感影像", icon: Picture, accept: "image/*,.tif,.tiff" },
  { key: "batch", name: "批量检测", desc: "上传整个文件夹", icon: Folder, accept: "image/*,.tif,.tiff" },
];

const selectedBatchItem = ref(null);

// 解析图片 URL — 绝对路径直接用, 相对路径拼接后端地址
const resolveUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("blob:")) {
    return url;
  }
  return `http://localhost:8000${url}`;
};

// ── 事件处理 ──
const handleFileChange = async (event, tabKey) => {
  const files = event.target.files;
  if (!files || !files.length) return;
  if (!(await requireLogin())) { event.target.value = ""; return; }

  if (tabKey === "single") {
    await processSingle(files[0]);
  } else {
    await processBatch(Array.from(files));
  }
  event.target.value = "";
};

const processSingle = async (file) => {
  const isGeoTiff = file.name.toLowerCase().endsWith('.tif') || file.name.toLowerCase().endsWith('.tiff');

  // TIF: 先调 preview 接口拿 PNG 预览，立即显示原图
  if (isGeoTiff) {
    const previewFd = new FormData();
    previewFd.append("file", file);
    try {
      const previewRes = await previewImage(previewFd);
      if (previewRes.success) {
        singleOriginal.value = resolveUrl(previewRes.data.preview_url);
      }
    } catch (e) { /* 预览失败不影响检测 */ }
  } else {
    singleOriginal.value = URL.createObjectURL(file);
  }

  const fd = new FormData();
  fd.append("file", file);
  fd.append("model_name", selectedModel.value);
  fd.append("conf_threshold", confThreshold.value);
  fd.append("iou_threshold", iouThreshold.value);
  fd.append("use_sahi", useSahi.value);
  loading.value = true;
  try {
    const res = await detectSingleImage(fd);
    if (res.success) {
      singleResult.value = res.data;
      singleResultImg.value = resolveUrl(res.data.result_image_url);
      singleOriginal.value = resolveUrl(res.data.image_url);
      sessionStorage.setItem('rsod_single_original', singleOriginal.value);
      sessionStorage.setItem('rsod_single_result_img', singleResultImg.value);
      sessionStorage.setItem('rsod_single_result', JSON.stringify(res.data));
    }
  } catch (e) {
    ElMessage.error("检测失败");
  } finally { loading.value = false; }
};

const resetSingle = () => {
  singleOriginal.value = "";
  singleResultImg.value = "";
  singleResult.value = null;
  sessionStorage.removeItem('rsod_single_original');
  sessionStorage.removeItem('rsod_single_result_img');
  sessionStorage.removeItem('rsod_single_result');
};

const downloadResult = async (url) => {
  try {
    const resp = await fetch(url);
    const blob = await resp.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `detection_result_${Date.now()}.jpg`;
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
const processBatch = async (files) => {
  // 初始化
  batchFiles.value = files.map(f => ({
    filename: f.name,
    preview: URL.createObjectURL(f),
    file: f,
    done: false,
    total_objects: 0,
    detection_time: 0,
    boxes: [],
    result_url: "",
    original_url: "",
    detection_id: "",
  }));
  batchSelectedIdx.value = -1;
  selectedBatchItem.value = null;
  batchDone.value = 0;
  batchTotalObjects.value = 0;
  batchTotalTime.value = 0;
  stopRequested.value = false;

  const tStart = performance.now();
  batchLoading.value = true;

  for (let i = 0; i < batchFiles.value.length; i++) {
    if (stopRequested.value) break;

    batchCurrentIdx.value = i;
    const item = batchFiles.value[i];
    const fd = new FormData();
    fd.append("file", item.file);
    fd.append("model_name", selectedModel.value);
    fd.append("conf_threshold", confThreshold.value);
    fd.append("iou_threshold", iouThreshold.value);
    fd.append("use_sahi", useSahi.value);
    try {
      const res = await detectSingleImage(fd);
      if (res.success) {
        item.done = true;
        item.total_objects = res.data.total_objects;
        item.detection_time = res.data.detection_time;
        item.boxes = res.data.boxes;
        item.result_url = resolveUrl(res.data.result_image_url);
        item.original_url = resolveUrl(res.data.image_url);
        item.preview = item.original_url;
        item.detection_id = res.data.detection_id;
        batchTotalObjects.value += res.data.total_objects;
        // 预加载原图+结果图，切换时两者同时出现
        new Image().src = item.original_url;
        new Image().src = item.result_url;
      }
    } catch (e) {
      item.done = true;
      item.total_objects = 0;
      item.boxes = [];
    }
    batchDone.value = i + 1;
  }

  batchTotalTime.value = ((performance.now() - tStart) / 1000).toFixed(1);
  batchLoading.value = false;
  batchCurrentIdx.value = -1;

  const firstDone = batchFiles.value.find(f => f.done && f.total_objects > 0);
  if (firstDone) {
    const idx = batchFiles.value.indexOf(firstDone);
    batchSelectedIdx.value = idx;
    selectedBatchItem.value = firstDone;
  }
};

const stopDetection = () => {
  stopRequested.value = true;
  ElMessage.warning("正在停止...");
};

const clearImageCache = () => {
  batchFiles.value.forEach(item => {
    if (item.preview && item.preview.startsWith('blob:')) {
      URL.revokeObjectURL(item.preview);
    }
  });
  ElMessage.success("本地图片缓存已清理");
};

const downloadAllResults = async () => {
  const ids = batchFiles.value.filter(f => f.detection_id).map(f => f.detection_id);
  if (!ids.length) { ElMessage.error("没有可下载的结果图"); return; }
  try {
    const blob = await downloadResultsZip(ids);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `detection_results_${Date.now()}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    ElMessage.success(`已下载 ${ids.length} 张结果图`);
  } catch (e) {
    ElMessage.error("批量下载失败");
  }
};

const selectBatchItem = (idx) => {
  if (batchSelectedIdx.value === idx) {
    // 再点同一个取消选中
    batchSelectedIdx.value = -1;
    selectedBatchItem.value = null;
  } else {
    batchSelectedIdx.value = idx;
    selectedBatchItem.value = batchFiles.value[idx];
  }
};

// ── 模型切换 ──
onMounted(async () => {
  try {
    const res = await getModels();
    if (res.data && res.data.length) {
      availableModels.value = res.data;
      const loaded = res.data.find(m => m.loaded);
      selectedModel.value = loaded ? loaded.key : res.data[0].key;
    }
  } catch (e) { /* use defaults */ }
});

const onModelChange = async (key) => {
  try {
    const res = await switchModel(key);
    if (res.success) {
      ElMessage.success(res.message);
      resetSingle();
      resetBatch();
    } else {
      ElMessage.error(res.message);
    }
  } catch (e) {
    ElMessage.error("模型切换失败");
  }
};

const doExport = async (recordId, format) => {
  try {
    const blob = await exportDetection(recordId, format);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const extMap = { coco: "json", yolo: "txt", geojson: "geojson" };
    a.download = `detection_${recordId.slice(0, 8)}.${extMap[format]}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    ElMessage.success(`已导出 ${format.toUpperCase()} 格式`);
  } catch (e) {
    ElMessage.error("导出失败");
  }
};

const resetBatch = () => {
  batchFiles.value = [];
  batchSelectedIdx.value = -1;
  selectedBatchItem.value = null;
  batchDone.value = 0;
  batchTotalObjects.value = 0;
  batchTotalTime.value = 0;
};
</script>

<style scoped>
.detection-page { width: 100%; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.header-left .page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.header-left .page-subtitle { font-size: 13px; color: var(--text-muted); }
.model-select { width: 180px; }

/* 模型配置框 */
.model-config-box {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 14px; background: var(--bg-card);
  border: 1px solid var(--border-color); border-radius: var(--radius-md);
}
.config-label { font-size: 11px; color: var(--accent); font-weight: 700; letter-spacing: 1px; white-space: nowrap; }
.config-controls { display: flex; align-items: center; gap: 10px; }

/* SAHI 开关 */
.sahi-toggle {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 14px; border-radius: 20px;
  background: var(--bg-input); border: 1px solid var(--border-color);
  cursor: pointer; transition: all 0.2s; user-select: none;
  white-space: nowrap;
}
.sahi-toggle:hover { border-color: var(--border-light); }
.sahi-toggle.on { background: var(--accent-dim); border-color: var(--accent); }
.sahi-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--text-muted); transition: all 0.2s;
}
.sahi-toggle.on .sahi-dot { background: var(--accent); box-shadow: 0 0 6px var(--accent-glow); }
.sahi-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.sahi-toggle.on .sahi-label { color: var(--accent); }

/* SAHI 说明气泡 */
.sahi-explain { font-size: 12px; color: var(--text-secondary); line-height: 1.6; }
.sahi-explain strong { color: var(--text-primary); }
.tag-rec { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; background: var(--accent-dim); color: var(--accent); font-weight: 600; }
.tag-off { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; background: var(--bg-input); color: var(--text-muted); font-weight: 600; }

/* 阈值调节 */
.threshold-bar {
  display: flex; gap: 24px; margin-bottom: 20px;
  padding: 14px 18px; background: var(--bg-card);
  border: 1px solid var(--border-color); border-radius: var(--radius-md);
}
.threshold-item { flex: 1; display: flex; align-items: center; gap: 12px; }
.threshold-label { font-size: 12px; color: var(--text-muted); white-space: nowrap; min-width: 64px; }
.threshold-slider { flex: 1; }
.threshold-value {
  font-family: var(--mono); font-size: 12px; color: var(--accent);
  min-width: 36px; text-align: right;
}

/* 选项卡 */
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

/* 上传区域 */
.upload-zone {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 52px 20px; margin-bottom: 20px;
  background: var(--bg-card); border: 2px dashed var(--border-light);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;
  position: relative;
}
.upload-zone:hover { border-color: var(--accent); background: var(--bg-card-hover); }
.upload-text { font-size: 15px; font-weight: 600; color: var(--text-secondary); }
.upload-hint { font-size: 12px; color: var(--text-muted); }
.hidden-input { display: none; }

/* 下载栏 */
.download-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
  padding: 10px 16px; background: var(--bg-card);
  border: 1px solid var(--accent-dim); border-radius: var(--radius-md);
}
.download-bar-label { font-size: 12px; color: var(--accent); font-weight: 600; white-space: nowrap; }

.main-content { display: flex; gap: 20px; }

/* ── 单图 ── */
.left-panel {
  flex: 1; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 20px;
}
.panel-topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.panel-count { font-size: 12px; color: var(--text-muted); margin-left: 8px; font-weight: 400; }
.panel-status .status { display: flex; align-items: center; gap: 6px; font-size: 12px; }
.status .status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status.processing .status-dot { background: var(--warning); animation: pulse 1.5s ease-in-out infinite; }
.status.done .status-dot { background: var(--accent); box-shadow: 0 0 6px var(--accent-glow); }
.status.idle .status-dot { background: var(--text-muted); }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

.image-compare-single { display: flex; gap: 14px; height: 360px; }
.image-card {
  flex: 1; position: relative; border-radius: var(--radius-md);
  overflow: hidden; background: var(--bg-input);
  border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center;
}
.compare-image { width: 100%; height: 100%; object-fit: cover; }
.placeholder { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-muted); font-size: 13px; }
.image-label {
  position: absolute; top: 10px; left: 10px;
  padding: 4px 10px; background: rgba(0,0,0,0.85); color: #fff;
  font-size: 11px; font-weight: 700; letter-spacing: 1px; border-radius: 4px;
  font-family: var(--mono);
  backdrop-filter: blur(4px);
}
.result-label { color: var(--accent); background: rgba(0,0,0,0.9); }
.detection-badge {
  position: absolute; top: 10px; right: 10px;
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--accent); color: var(--on-accent); font-weight: 700; font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 12px var(--accent-glow);
}

.download-btn {
  position: absolute; bottom: 12px; right: 12px;
  background: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  color: var(--accent) !important;
  opacity: 0; transition: opacity 0.2s;
}
.image-card:hover .download-btn { opacity: 1; }

.right-panel { width: 320px; display: flex; flex-direction: column; gap: 14px; flex-shrink: 0; }
.right-panel.right-empty {
  align-items: center; justify-content: center; gap: 8px;
  color: var(--text-muted);
}
.right-empty-text { font-size: 14px; font-weight: 500; color: var(--text-secondary); }
.right-empty-sub { font-size: 12px; }

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
  border-radius: var(--radius-lg); padding: 16px; display: flex; flex-direction: column; overflow: hidden;
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.card-badge { padding: 1px 8px; border-radius: 10px; background: var(--accent-dim); color: var(--accent); font-size: 12px; font-family: var(--mono); }
.box-list { flex: 1; overflow-y: auto; }
.box-item { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid var(--border-color); }
.box-item:last-child { border-bottom: none; }
.box-left { display: flex; align-items: center; gap: 10px; }
.box-index { font-family: var(--mono); font-size: 11px; color: var(--text-muted); }
.box-class { font-size: 13px; color: var(--text-primary); }
.box-conf { font-family: var(--mono); font-size: 12px; color: var(--accent); }
.box-empty { flex: 1; display: flex; align-items: center; justify-content: center; font-size: 13px; color: var(--text-muted); }

.reset-btn { width: 100%; height: 40px; border-radius: var(--radius-md); }

/* 导出行 */
.export-row {
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); padding: 12px 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.export-label { font-size: 12px; color: var(--text-muted); }
.export-btns { display: flex; gap: 8px; }

/* ── 批量网格 ── */
.batch-grid {
  flex: 1; overflow-y: auto; display: grid;
  grid-template-columns: repeat(4, 1fr); gap: 10px;
  align-content: start;
}

.batch-card {
  background: var(--bg-input); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); overflow: hidden; cursor: pointer; transition: all 0.2s;
  position: relative;
}
.batch-card:hover { border-color: var(--border-light); }
.batch-card.selected { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent-glow); }
.batch-card.has-result { border-color: var(--accent-dim); }

.batch-thumb {
  width: 100%; height: 120px; object-fit: cover; display: block;
}
.batch-thumb-placeholder {
  width: 100%; height: 120px; display: flex; align-items: center; justify-content: center;
  background: var(--bg-deep); color: var(--text-muted);
}

.batch-file-name {
  padding: 6px 8px; font-size: 11px; color: var(--text-secondary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.batch-card-badge {
  position: absolute; top: 6px; right: 6px;
  min-width: 22px; height: 22px; border-radius: 11px;
  background: var(--accent); color: var(--on-accent); font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  padding: 0 6px; font-family: var(--mono);
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

/* 批量结果图：原图+结果对比 */
.image-compare-mini { display: flex; gap: 8px; }
.mini-img-card {
  flex: 1; position: relative; border-radius: var(--radius-sm); overflow: hidden;
  background: var(--bg-input); border: 1px solid var(--border-color);
}
.mini-img { width: 100%; height: 150px; object-fit: cover; display: block; }
.mini-label {
  position: absolute; top: 6px; left: 6px;
  padding: 2px 7px; background: rgba(0,0,0,0.85); color: #fff;
  font-size: 10px; font-weight: 700; font-family: var(--mono); border-radius: 3px;
}
.mini-label.result-label { color: var(--accent); background: rgba(0,0,0,0.9); }
.mini-download-btn {
  position: absolute; bottom: 6px; right: 6px;
  background: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  color: var(--accent) !important;
  opacity: 0; transition: opacity 0.2s;
}
.mini-img-card:hover .mini-download-btn { opacity: 1; }

.batch-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; color: var(--text-muted);
}

/* ── 模型选择器 ── */
.model-option { display: flex; flex-direction: column; gap: 2px; }
.model-opt-name { font-size: 13px; font-weight: 600; }
.model-opt-desc { font-size: 11px; color: var(--text-muted); }
</style>
