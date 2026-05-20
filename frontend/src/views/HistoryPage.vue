<template>
  <div class="history-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">历史记录</h1>
        <p class="page-subtitle">查看和管理所有检测记录</p>
      </div>
    </div>

    <div class="search-bar">
      <el-input v-model="searchQuery" placeholder="搜索文件名..." size="default" class="search-input" clearable @input="onSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="filterStatus" placeholder="状态筛选" size="default" class="filter-select" @change="fetchHistory">
        <el-option label="全部" value="" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
      </el-select>
    </div>

    <div v-if="loading" class="loading-state">
      <span class="loader"></span>
      <span>加载中...</span>
    </div>

    <div v-else class="history-list">
      <div v-for="record in records" :key="record.id" class="history-card" @click="viewRecord(record)">
        <div class="card-preview">
          <img :src="record.result_image_url || record.image_url" class="preview-img" @error="onImgError" />
          <span class="card-status" :class="record.status">
            {{ record.status === 'completed' ? '完成' : '失败' }}
          </span>
        </div>

        <div class="card-body">
          <div class="card-title-row">
            <span class="card-filename">{{ record.filename }}</span>
            <span class="card-model">{{ record.model_name }}</span>
          </div>
          <div class="card-meta">
            <span><el-icon><Clock /></el-icon>{{ formatTime(record.created_at) }}</span>
            <span><el-icon><Aim /></el-icon>{{ record.total_objects }} 目标</span>
          </div>
          <div class="card-tags" v-if="record.detected_classes && record.detected_classes.length">
            <span v-for="cls in record.detected_classes" :key="cls" class="tag">{{ classNameMap[cls] || cls }}</span>
          </div>
        </div>

        <div class="card-actions" @click.stop>
          <el-button size="small" @click="viewRecord(record)"><el-icon><View /></el-icon></el-button>
          <el-button size="small" type="danger" @click="deleteRecord(record)"><el-icon><Delete /></el-icon></el-button>
        </div>
      </div>

      <div v-if="records.length === 0 && !loading" class="empty-state">
        <el-icon :size="48"><FolderOpened /></el-icon>
        <p class="empty-text">暂无检测记录</p>
        <el-button type="primary" @click="goToDetection">开始检测</el-button>
      </div>
    </div>

    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination :total="total" :page-size="pageSize" :current-page="currentPage" @current-change="onPageChange" layout="prev, pager, next" />
    </div>

    <el-dialog v-model="detailVisible" title="检测详情" width="680px">
      <div v-if="detailLoading" class="detail-loading"><span class="loader"></span></div>
      <div v-else-if="detailData" class="detail-content">
        <img :src="detailData.result_image_url" class="detail-img" />
        <div class="detail-meta">
          <p><strong>检测ID:</strong> {{ detailData.detection_id }}</p>
          <p><strong>目标数:</strong> {{ detailData.total_objects }} 个</p>
          <p><strong>耗时:</strong> {{ detailData.detection_time }}s</p>
        </div>
        <div v-if="detailData.boxes && detailData.boxes.length" class="detail-boxes">
          <h4>识别清单</h4>
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
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Search, Clock, Aim, View, Delete, FolderOpened } from "@element-plus/icons-vue";
import { getDetectionHistory, getDetectionDetail, deleteDetectionRecord } from "../api/detection";

const router = useRouter();
const loading = ref(false);
const searchQuery = ref("");
const filterStatus = ref("");
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
const fetchHistory = async () => {
  loading.value = true;
  try {
    const res = await getDetectionHistory({ page: currentPage.value, page_size: pageSize.value, keyword: searchQuery.value, status: filterStatus.value });
    records.value = res.data || [];
    total.value = res.total || 0;
  } catch (e) {
    ElMessage.error("获取历史记录失败");
  } finally { loading.value = false; }
};

const onSearch = () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { currentPage.value = 1; fetchHistory(); }, 300); };
const onPageChange = (p) => { currentPage.value = p; fetchHistory(); };

const viewRecord = async (record) => {
  detailVisible.value = true; detailLoading.value = true; detailData.value = null;
  try {
    const res = await getDetectionDetail(record.id);
    detailData.value = res.data;
  } catch (e) { ElMessage.error("获取详情失败"); detailVisible.value = false; }
  finally { detailLoading.value = false; }
};

const deleteRecord = async (record) => {
  try {
    await ElMessageBox.confirm("确定要删除该记录吗？", "确认", { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" });
    await deleteDetectionRecord(record.id);
    ElMessage.success("已删除");
    fetchHistory();
  } catch (e) { /* cancelled */ }
};

const goToDetection = () => router.push("/detection");
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
.header-left .page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.header-left .page-subtitle { font-size: 13px; color: var(--text-muted); }

.search-bar { display: flex; gap: 14px; margin-bottom: 24px; }
.search-input { flex: 1; max-width: 320px; }
.filter-select { width: 130px; }

.loading-state { display: flex; align-items: center; gap: 10px; padding: 60px 0; justify-content: center; color: var(--text-muted); }
.loader { width: 20px; height: 20px; border: 2px solid var(--border-color); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.history-list { display: flex; flex-direction: column; gap: 12px; }

.history-card {
  display: flex; align-items: center; gap: 18px; padding: 18px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;
}
.history-card:hover { border-color: var(--border-light); box-shadow: var(--card-shadow-hover); }

.card-preview {
  position: relative; width: 120px; height: 80px; border-radius: var(--radius-sm);
  overflow: hidden; background: var(--bg-input); flex-shrink: 0;
}
.preview-img { width: 100%; height: 100%; object-fit: cover; }
.card-status {
  position: absolute; bottom: 6px; left: 6px;
  padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 700; letter-spacing: 1px;
  font-family: var(--mono);
}
.card-status.completed { background: var(--accent-dim); color: var(--accent); }
.card-status.failed { background: rgba(255, 171, 0, 0.15); color: var(--warning); }

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
.detail-img { width: 100%; border-radius: var(--radius-md); margin-bottom: 16px; }
.detail-meta { margin-bottom: 16px; }
.detail-meta p { margin: 6px 0; font-size: 13px; color: var(--text-secondary); }
.detail-boxes {
  border-top: 1px solid var(--border-color); padding-top: 14px;
  h4 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; }
}
.d-box-item {
  display: flex; align-items: center; gap: 10px; padding: 6px 0;
  border-bottom: 1px solid var(--border-color); font-size: 13px;
  &:last-child { border-bottom: none; }
}
.d-box-index { font-family: var(--mono); font-size: 11px; color: var(--text-muted); width: 20px; }
.d-box-name { flex: 1; color: var(--text-primary); }
.d-box-conf { font-family: var(--mono); color: var(--accent); font-weight: 600; }
</style>
