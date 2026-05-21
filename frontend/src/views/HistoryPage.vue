<template>
  <div class="history-page">
    <div class="page-header">
      <h1 class="page-title">历史记录</h1>
      <p class="page-subtitle">查看和管理所有检测记录</p>
    </div>

    <div class="history-tabs">
      <div v-for="tab in tabs" :key="tab.key" class="h-tab"
           :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        <el-icon :size="16"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </div>
    </div>

    <div class="search-bar">
      <el-input v-model="searchQuery" placeholder="搜索文件名..." class="search-input" clearable @input="onSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <div v-if="loading" class="loading-state"><span class="loader"></span><span>加载中...</span></div>

    <div v-else class="history-list">
      <!-- 智能检测 -->
      <template v-if="activeTab === 'detection'">
        <div v-for="r in records" :key="r.id" class="history-card" @click="viewRecord(r)">
          <div class="card-preview">
            <img :src="r.result_image_url || r.image_url" class="preview-img" @error="onImgError" />
            <span class="card-status" :class="r.status">{{ r.status === 'completed' ? '完成' : '失败' }}</span>
          </div>
          <div class="card-body">
            <div class="card-title-row"><span class="card-filename">{{ r.filename }}</span><span class="card-model">{{ r.model_name }}</span></div>
            <div class="card-meta">
              <span><el-icon><Clock /></el-icon>{{ formatTime(r.created_at) }}</span>
              <span><el-icon><Aim /></el-icon>{{ r.total_objects }} 目标</span>
            </div>
            <div class="card-tags" v-if="r.detected_classes?.length">
              <span v-for="cls in r.detected_classes" :key="cls" class="tag">{{ classNameMap[cls] || cls }}</span>
            </div>
          </div>
          <div class="card-actions" @click.stop>
            <el-button size="small" @click="viewRecord(r)"><el-icon><View /></el-icon></el-button>
            <el-button size="small" type="danger" @click="deleteRecord(r)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>
      </template>

      <!-- 变化检测 -->
      <template v-if="activeTab === 'change'">
        <div v-for="r in records" :key="r.id" class="history-card" @click="viewRecord(r)">
          <div class="card-preview">
            <img v-if="r.result_url" :src="r.result_url" class="preview-img" @error="onImgError" />
            <div v-else class="preview-placeholder"><el-icon :size="24"><Picture /></el-icon></div>
            <span class="card-status completed" v-if="r.status === 'completed'">完成</span>
          </div>
          <div class="card-body">
            <div class="card-title-row">
              <span class="card-filename">{{ r.filename_a }} ↔ {{ r.filename_b }}</span>
              <span class="card-model">{{ r.model_name }}</span>
            </div>
            <div class="card-meta">
              <span><el-icon><Clock /></el-icon>{{ formatTime(r.created_at) }}</span>
              <span>变化: {{ (r.change_ratio * 100).toFixed(2) }}%</span>
            </div>
          </div>
          <div class="card-actions" @click.stop>
            <el-button size="small" type="danger" @click="deleteRecord(r)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>
      </template>

      <!-- 视频流 -->
      <template v-if="activeTab === 'video'">
        <div v-for="r in records" :key="r.id" class="history-card">
          <div class="card-preview video-preview">
            <el-icon :size="32"><VideoCamera /></el-icon>
          </div>
          <div class="card-body">
            <div class="card-title-row"><span class="card-filename">{{ r.filename }}</span><span class="card-model">{{ r.model_name }}</span></div>
            <div class="card-meta">
              <span><el-icon><Clock /></el-icon>{{ formatTime(r.created_at) }}</span>
              <span>{{ r.total_frames }} 帧</span>
              <span>{{ r.total_objects }} 目标</span>
              <span>{{ r.detection_time }}s</span>
            </div>
          </div>
          <div class="card-actions" @click.stop>
            <el-button size="small" type="danger" @click="deleteRecord(r)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>
      </template>

      <div v-if="records.length === 0 && !loading" class="empty-state">
        <el-icon :size="48"><FolderOpened /></el-icon>
        <p class="empty-text">暂无记录</p>
      </div>
    </div>

    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination :total="total" :page-size="pageSize" :current-page="currentPage"
        @current-change="onPageChange" layout="prev, pager, next" />
    </div>

    <!-- 检测详情弹窗 -->
    <el-dialog v-model="detailVisible" title="检测详情" width="720px">
      <div v-if="detailLoading" class="detail-loading"><span class="loader"></span></div>
      <div v-else-if="detailData" class="detail-content">
        <div class="detail-compare">
          <div class="detail-img-card">
            <img v-if="detailData.image_url" :src="detailData.image_url" class="detail-img" />
            <div class="detail-img-label">原图</div>
          </div>
          <div class="detail-img-card">
            <img :src="detailData.result_image_url" class="detail-img" />
            <div class="detail-img-label result">检测结果</div>
          </div>
        </div>
        <div class="detail-meta">
          <p><strong>检测ID:</strong> {{ detailData.detection_id }}</p>
          <p><strong>目标数:</strong> {{ detailData.total_objects }} 个</p>
          <p><strong>耗时:</strong> {{ detailData.detection_time }}s</p>
        </div>
        <div v-if="detailData.boxes?.length" class="detail-boxes">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <h4>识别清单</h4>
            <div class="detail-export-btns">
              <el-button size="small" @click="doExport(detailData.detection_id, 'coco')">COCO</el-button>
              <el-button size="small" @click="doExport(detailData.detection_id, 'yolo')">YOLO</el-button>
              <el-button size="small" @click="doExport(detailData.detection_id, 'geojson')">GeoJSON</el-button>
            </div>
          </div>
          <div v-for="(box, idx) in detailData.boxes" :key="idx" class="d-box-item">
            <span class="d-box-index">{{ String(idx+1).padStart(2,'0') }}</span>
            <span class="d-box-name">{{ box.class_name }}</span>
            <span class="d-box-conf">{{ (box.confidence*100).toFixed(1) }}%</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Search, Clock, Aim, View, Delete, FolderOpened, Picture, Connection, VideoCamera } from "@element-plus/icons-vue";
import { getDetectionHistory, getDetectionDetail, deleteDetectionRecord, exportDetection,
         getChangeHistory, deleteChangeRecord,
         } from "../api/detection";
import request from "../utils/request";

const tabs = [
  { key: "detection", label: "智能检测", icon: Aim },
  { key: "change", label: "变化检测", icon: Connection },
  { key: "video", label: "视频流检测", icon: VideoCamera },
];

const activeTab = ref("detection");
const loading = ref(false);
const searchQuery = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const records = ref([]);
const total = ref(0);
const detailVisible = ref(false);
const detailLoading = ref(false);
const detailData = ref(null);

const classNameMap = {
  plane: "飞机", ship: "船舶", "storage-tank": "储罐", "baseball-diamond": "棒球场",
  "tennis-court": "网球场", "basketball-court": "篮球场", "ground-track-field": "田径场",
  harbor: "港口", bridge: "桥梁", "large-vehicle": "大型车辆", "small-vehicle": "小型车辆",
  helicopter: "直升机", roundabout: "环岛", "soccer-ball-field": "足球场", "swimming-pool": "游泳池",
};

let searchTimer = null;

const apiMap = {
  detection: (p) => getDetectionHistory({ page: p.page, page_size: p.pageSize, keyword: p.keyword, status: "" }),
  change: (p) => getChangeHistory({ page: p.page, page_size: p.pageSize }),
  video: (p) => request({ url: "/video/history", method: "get", params: { page: p.page, page_size: p.pageSize } }),
};

const fetchHistory = async () => {
  loading.value = true;
  try {
    const res = await apiMap[activeTab.value]({ page: currentPage.value, pageSize: pageSize.value, keyword: searchQuery.value });
    records.value = res.data || [];
    total.value = res.total || 0;
  } catch (e) { ElMessage.error("获取失败"); }
  finally { loading.value = false; }
};

const switchTab = (key) => { activeTab.value = key; currentPage.value = 1; searchQuery.value = ""; fetchHistory(); };
const onSearch = () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { currentPage.value = 1; fetchHistory(); }, 300); };
const onPageChange = (p) => { currentPage.value = p; fetchHistory(); };

const viewRecord = async (r) => {
  if (activeTab.value !== "detection") return;
  detailVisible.value = true; detailLoading.value = true; detailData.value = null;
  try {
    const res = await getDetectionDetail(r.id);
    detailData.value = res.data;
  } catch (e) { ElMessage.error("获取详情失败"); detailVisible.value = false; }
  finally { detailLoading.value = false; }
};

const deleteRecord = async (r) => {
  try {
    await ElMessageBox.confirm("确定要删除吗？", "确认", { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" });
    if (activeTab.value === "detection") await deleteDetectionRecord(r.id);
    else if (activeTab.value === "change") await deleteChangeRecord(r.id);
    else await request({ url: `/video/history/${r.id}`, method: "delete" });
    ElMessage.success("已删除");
    fetchHistory();
  } catch (e) { /* cancelled */ }
};

const doExport = async (recordId, format) => {
  try {
    const blob = await exportDetection(recordId, format);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `detection_${recordId.slice(0, 8)}.${format === "yolo" ? "txt" : "json"}`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    ElMessage.success(`已导出 ${format.toUpperCase()}`);
  } catch (e) { ElMessage.error("导出失败"); }
};

const formatTime = (t) => {
  if (!t) return "-";
  const d = new Date(t);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};
const onImgError = (e) => { e.target.style.display = "none"; };
onMounted(() => fetchHistory());
</script>

<style scoped>
.history-page { width: 100%; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 13px; color: var(--text-muted); }

.history-tabs { display: flex; gap: 8px; margin-bottom: 18px; }
.h-tab {
  display: flex; align-items: center; gap: 6px; padding: 8px 18px;
  border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 500;
  background: var(--bg-card); border: 1px solid var(--border-color);
  color: var(--text-muted); transition: all 0.2s;
}
.h-tab:hover { border-color: var(--border-light); color: var(--text-secondary); }
.h-tab.active { background: var(--accent-dim); border-color: var(--accent); color: var(--accent); }

.search-bar { display: flex; gap: 14px; margin-bottom: 24px; }
.search-input { flex: 1; max-width: 320px; }

.loading-state { display: flex; align-items: center; gap: 10px; padding: 60px 0; justify-content: center; color: var(--text-muted); }
.loader { width: 20px; height: 20px; border: 2px solid var(--border-color); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.history-list { display: flex; flex-direction: column; gap: 12px; }
.history-card {
  display: flex; align-items: center; gap: 18px; padding: 18px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;
}
.history-card:hover { border-color: var(--border-light); }

.card-preview {
  position: relative; width: 120px; height: 80px; border-radius: var(--radius-sm);
  overflow: hidden; background: var(--bg-input); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.preview-img { width: 100%; height: 100%; object-fit: cover; }
.preview-placeholder { color: var(--text-muted); }
.card-status {
  position: absolute; bottom: 6px; left: 6px;
  padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 700;
  font-family: var(--mono);
}
.card-status.completed { background: var(--accent-dim); color: var(--accent); }

.card-body { flex: 1; min-width: 0; }
.card-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.card-filename { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.card-model { font-size: 11px; color: var(--text-muted); font-family: var(--mono); }
.card-meta { display: flex; gap: 18px; margin-bottom: 6px; font-size: 12px; color: var(--text-muted); }
.card-meta span { display: flex; align-items: center; gap: 4px; }
.card-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 2px 8px; border-radius: 4px; background: var(--accent-dim); color: var(--accent); font-size: 11px; }

.card-actions { display: flex; gap: 6px; flex-shrink: 0; }

.empty-state { display: flex; flex-direction: column; align-items: center; padding: 80px 0; gap: 12px; color: var(--text-muted); }
.empty-text { font-size: 14px; }

.pagination-wrap { display: flex; justify-content: center; margin-top: 28px; }

.detail-loading { display: flex; justify-content: center; padding: 40px; }
.detail-compare { display: flex; gap: 10px; margin-bottom: 16px; }
.detail-img-card { flex: 1; position: relative; border-radius: var(--radius-md); overflow: hidden; background: var(--bg-input); border: 1px solid var(--border-color); }
.detail-img { width: 100%; display: block; max-height: 280px; object-fit: cover; }
.detail-img-label { position: absolute; top: 8px; left: 8px; padding: 2px 8px; background: rgba(0,0,0,0.85); color: #fff; font-size: 10px; font-weight: 700; font-family: var(--mono); border-radius: 3px; }
.detail-img-label.result { color: var(--accent); background: rgba(0,0,0,0.9); }
.detail-meta { margin-bottom: 16px; }
.detail-meta p { margin: 6px 0; font-size: 13px; color: var(--text-secondary); }
.detail-boxes { border-top: 1px solid var(--border-color); padding-top: 14px; }
.detail-boxes h4 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; }
.d-box-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--border-color); font-size: 13px; }
.d-box-item:last-child { border-bottom: none; }
.d-box-index { font-family: var(--mono); font-size: 11px; color: var(--text-muted); width: 20px; }
.d-box-name { flex: 1; color: var(--text-primary); }
.d-box-conf { font-family: var(--mono); color: var(--accent); font-weight: 600; }
.detail-export-btns { display: flex; gap: 6px; }
.video-preview { width: 120px; height: 80px; }
</style>
