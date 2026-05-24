<template>
  <div class="profile-page">
    <div class="page-header">
      <h1 class="page-title">{{ $t('nav.profile') }}</h1>
      <p class="page-subtitle">{{ $t('profile.subtitle') }}</p>
    </div>

    <div class="profile-grid">
      <!-- 左侧：用户卡片 + 快捷入口 -->
      <div class="user-card">
        <div class="user-avatar-wrap">
          <el-avatar :size="72" class="user-avatar">
            <el-icon :size="36"><User /></el-icon>
          </el-avatar>
          <div class="avatar-ring"></div>
        </div>
        <div class="user-name">{{ profile.username }}</div>
        <div class="user-role">{{ profile.role === 'admin' ? $t('profile.roleAdmin') : $t('profile.roleUser') }}</div>
        <div class="user-since">{{ $t('profile.joinDate') }} {{ profile.created_at }}</div>
        <div class="user-divider"></div>
        <div class="user-actions">
          <el-button size="small" class="action-btn" @click="showEditDialog = true">
            <el-icon><Edit /></el-icon>{{ $t('profile.editProfile') }}
          </el-button>
          <el-button size="small" class="action-btn" @click="showPwdDialog = true">
            <el-icon><Lock /></el-icon>{{ $t('profile.changePassword') }}
          </el-button>
        </div>
        <div class="user-divider"></div>
        <div class="user-links-label">{{ $t('profile.quickLinks') }}</div>
        <div class="user-links">
          <div class="user-link" @click="$router.push('/detection')">
            <el-icon><Aim /></el-icon><span>{{ $t('nav.detection') }}</span>
          </div>
          <div class="user-link" @click="$router.push('/change-detection')">
            <el-icon><Connection /></el-icon><span>{{ $t('nav.changeDetection') }}</span>
          </div>
          <div class="user-link" @click="$router.push('/video')">
            <el-icon><VideoCamera /></el-icon><span>{{ $t('nav.video') }}</span>
          </div>
          <div class="user-link" @click="$router.push('/history')">
            <el-icon><Clock /></el-icon><span>{{ $t('nav.history') }}</span>
          </div>
          <div class="user-link" @click="$router.push('/targets')">
            <el-icon><DataLine /></el-icon><span>{{ $t('nav.targets') }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧：统计概览 -->
      <div class="stats-area">
        <!-- 四张统计卡片 -->
        <div class="stats-row">
          <div class="stat-card" @click="$router.push('/history')">
            <div class="stat-icon st0"><el-icon><FolderOpened /></el-icon></div>
            <div class="stat-body">
              <span class="stat-val">{{ profile.stats.total_tasks }}</span>
              <span class="stat-lbl">{{ $t('profile.totalTasks') }}</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon st1"><el-icon><Picture /></el-icon></div>
            <div class="stat-body">
              <span class="stat-val">{{ profile.stats.total_detections }}</span>
              <span class="stat-lbl">{{ $t('profile.totalDetections') }}</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon st2"><el-icon><Connection /></el-icon></div>
            <div class="stat-body">
              <span class="stat-val">{{ profile.stats.total_change_detections }}</span>
              <span class="stat-lbl">{{ $t('profile.totalChange') }}</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon st3"><el-icon><VideoCamera /></el-icon></div>
            <div class="stat-body">
              <span class="stat-val">{{ profile.stats.total_video_detections }}</span>
              <span class="stat-lbl">{{ $t('profile.totalVideo') }}</span>
            </div>
          </div>
        </div>

        <!-- 二级统计（次要指标） -->
        <div class="stats-row-mini">
          <div class="mini-stat">
            <span class="mini-val">{{ profile.stats.total_objects }}</span>
            <span class="mini-lbl">{{ $t('profile.totalObjects') }}</span>
          </div>
          <div class="mini-stat">
            <span class="mini-val">{{ profile.stats.total_time }}s</span>
            <span class="mini-lbl">{{ $t('profile.totalTime') }}</span>
          </div>
          <div class="mini-stat">
            <span class="mini-val">{{ profile.stats.active_days }}</span>
            <span class="mini-lbl">{{ $t('profile.activeDays') }}</span>
          </div>
          <div class="mini-stat">
            <span class="mini-val small">{{ profile.stats.top_model }}</span>
            <span class="mini-lbl">{{ $t('profile.topModel') }}</span>
          </div>
        </div>

        <!-- 任务类型分布 + 模型使用 -->
        <div class="bottom-row">
          <div class="panel">
            <div class="panel-header">{{ $t('profile.taskDist') }}</div>
            <div class="task-dist-chart" v-if="hasData">
              <div v-for="t in profile.task_dist" :key="t.type" class="task-bar-row">
                <span class="task-label">{{ taskTypeLabel(t.type) }}</span>
                <div class="task-bar-wrap">
                  <div class="task-bar" :class="'task-' + t.type"
                    :style="{ width: barWidth(t.count, profile.task_dist) + '%' }"></div>
                </div>
                <span class="task-count">{{ t.count }}</span>
              </div>
            </div>
            <div v-else class="no-data">{{ $t('common.noData') }}</div>
          </div>

          <div class="panel">
            <div class="panel-header">{{ $t('profile.modelUsage') }}</div>
            <div class="model-list" v-if="profile.model_usage && profile.model_usage.length">
              <div v-for="m in profile.model_usage" :key="m.key" class="model-row">
                <span class="model-type-tag" :class="'mt-' + m.type">{{ modelTypeLabel(m.type) }}</span>
                <span class="model-name-text">{{ m.name }}</span>
                <span class="model-count">{{ m.count }}</span>
              </div>
            </div>
            <div v-else class="no-data">{{ $t('common.noData') }}</div>
          </div>
        </div>

        <!-- 类别分布（仅智能检测） -->
        <div class="panel" v-if="profile.class_dist && profile.class_dist.length">
          <div class="panel-header">{{ $t('profile.classDistribution') }}</div>
          <div class="class-list">
            <div v-for="item in profile.class_dist" :key="item.name" class="class-row">
              <span class="class-cn">{{ $t('targets.dota.' + item.name) }}</span>
              <div class="class-bar-wrap">
                <div class="class-bar" :style="{ width: barWidth(item.count, profile.class_dist) + '%' }"></div>
              </div>
              <span class="class-count">{{ item.count }}</span>
            </div>
          </div>
        </div>

        <!-- 最近活动 -->
        <div class="panel" v-if="profile.recent_activity && profile.recent_activity.length">
          <div class="panel-header">{{ $t('profile.recentActivity') }}</div>
          <div class="recent-list">
            <div v-for="r in profile.recent_activity" :key="r.id" class="recent-row" @click="goRecent(r)">
              <span class="recent-type" :class="'rect-' + r.record_type">{{ recTypeLabel(r.record_type) }}</span>
              <span class="recent-filename">{{ r.filename }}</span>
              <span class="recent-model">{{ r.model_name }}</span>
              <span class="recent-date">{{ r.date }}</span>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!hasData" class="empty-hint">
          <el-icon :size="40"><FolderOpened /></el-icon>
          <p>{{ $t('profile.noRecords') }}<a href="/detection">{{ $t('profile.noRecordsLink') }}</a>{{ $t('profile.noRecordsSuffix') }}</p>
        </div>
      </div>
    </div>

    <!-- 编辑资料 -->
    <el-dialog v-model="showEditDialog" :title="$t('profile.editProfileTitle')" width="420px">
      <el-form :model="editForm" label-width="70px">
        <el-form-item :label="$t('profile.username')">
          <el-input v-model="editForm.username" :placeholder="$t('profile.usernamePlaceholder')" />
        </el-form-item>
        <el-form-item label="Email">
          <el-input v-model="editForm.email" placeholder="Email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">{{ $t('profile.cancel') }}</el-button>
        <el-button type="primary" @click="saveProfile" :loading="saving">{{ $t('profile.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码 -->
    <el-dialog v-model="showPwdDialog" :title="$t('profile.changePasswordTitle')" width="420px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="80px">
        <el-form-item :label="$t('profile.currentPassword')" prop="oldPassword">
          <el-input v-model="pwdForm.oldPassword" type="password" :placeholder="$t('profile.currentPasswordPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('profile.newPassword')" prop="newPassword">
          <el-input v-model="pwdForm.newPassword" type="password" :placeholder="$t('profile.newPasswordPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('profile.confirmPassword')" prop="confirmPassword">
          <el-input v-model="pwdForm.confirmPassword" type="password" :placeholder="$t('profile.confirmPasswordPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPwdDialog = false">{{ $t('profile.cancel') }}</el-button>
        <el-button type="primary" @click="changePassword" :loading="savingPwd">{{ $t('profile.confirmModify') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { User, Edit, Lock, Clock, Aim, Connection, VideoCamera, Picture, FolderOpened, DataLine } from "@element-plus/icons-vue";
import { getSession, refreshAuth } from "../utils/auth";
import { useI18n } from "vue-i18n";
import { getUserProfile, updateUserProfile, changeUserPassword } from "../api/detection";
import { requireLogin } from "../utils/request";

const router = useRouter();
const session = getSession();
const { t } = useI18n();

const profile = reactive({
  username: session?.username || t('profile.notLoggedIn'),
  role: "user",
  avatar: "", email: "",
  created_at: "-",
  stats: { total_tasks: 0, total_detections: 0, total_change_detections: 0, total_video_detections: 0, total_objects: 0, total_time: 0, active_days: 0, top_model: "-" },
  task_dist: [],
  model_usage: [],
  class_dist: [],
  recent_activity: [],
});

const hasData = computed(() => profile.stats.total_tasks > 0);

const barWidth = (val, arr) => {
  const max = Math.max(...arr.map(i => i.count || i.change_ratio || 0), 1);
  return (val / max) * 100;
};

const recTypeLabel = (type) => ({ detection: t('nav.detection'), change: t('nav.changeDetection'), video: t('nav.video') }[type] || type);

const taskTypeLabel = (type) => ({ detection: t('nav.detection'), change: t('nav.changeDetection'), video: t('nav.video') }[type] || type);

const modelTypeLabel = (type) => ({ detection: t('profile.typeDetection'), change: t('profile.typeChange'), video: t('profile.typeVideo') }[type] || type);

const goRecent = (r) => {
  if (r.record_type === 'detection') router.push('/history');
  else if (r.record_type === 'change') router.push('/history');
  else router.push('/history');
};

// ── 编辑资料 ──
const showEditDialog = ref(false);
const saving = ref(false);
const editForm = reactive({ username: profile.username, email: profile.email });

const saveProfile = async () => {
  if (!editForm.username.trim()) { ElMessage.warning(t('profile.usernameRequired')); return; }
  saving.value = true;
  try {
    const res = await updateUserProfile({ username: editForm.username.trim(), email: editForm.email.trim() });
    if (res.success) {
      profile.username = res.data.username;
      profile.email = res.data.email;
      ElMessage.success(t('profile.profileUpdated'));
      showEditDialog.value = false;
      refreshAuth();
    }
  } catch (e) { ElMessage.error(e.response?.data?.detail || t('common.error')); }
  finally { saving.value = false; }
};

// ── 修改密码 ──
const showPwdDialog = ref(false);
const savingPwd = ref(false);
const pwdFormRef = ref(null);
const pwdForm = reactive({ oldPassword: "", newPassword: "", confirmPassword: "" });
const pwdRules = {
  oldPassword: [{ required: true, message: t('profile.currentPasswordRequired'), trigger: "blur" }],
  newPassword: [
    { required: true, message: t('profile.newPasswordRequired'), trigger: "blur" },
    { min: 6, message: t('profile.passwordMinLength'), trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: t('profile.confirmPasswordRequired'), trigger: "blur" },
    { validator: (_, v, cb) => v !== pwdForm.newPassword ? cb(new Error(t('profile.passwordMismatch'))) : cb(), trigger: "blur" },
  ],
};

const changePassword = () => {
  pwdFormRef.value?.validate(async (valid) => {
    if (!valid) return;
    savingPwd.value = true;
    try {
      await changeUserPassword({ old_password: pwdForm.oldPassword, new_password: pwdForm.newPassword });
      pwdForm.oldPassword = ""; pwdForm.newPassword = ""; pwdForm.confirmPassword = "";
      showPwdDialog.value = false;
      ElMessage.success(t('profile.passwordChanged'));
    } catch (e) { ElMessage.error(e.response?.data?.detail || t('common.error')); }
    finally { savingPwd.value = false; }
  });
};

onMounted(async () => {
  if (!(await requireLogin())) return;
  const s = getSession();
  if (s?.username) profile.username = s.username;
  try {
    const res = await getUserProfile();
    if (res.data) Object.assign(profile, res.data);
    if (s?.username) profile.username = s.username;
  } catch (e) { /* use defaults */ }
});
</script>

<style scoped>
.profile-page { width: 100%; }
.page-header { margin-bottom: 28px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 13px; color: var(--text-muted); }
.profile-grid { display: flex; gap: 24px; align-items: flex-start; }

/* 用户卡片 */
.user-card {
  width: 240px; flex-shrink: 0;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 32px 24px; text-align: center;
}
.user-avatar-wrap { position: relative; display: inline-block; margin-bottom: 16px; }
.user-avatar { background: linear-gradient(135deg, var(--accent), var(--accent-secondary)); }
.avatar-ring { position: absolute; inset: -4px; border-radius: 50%; border: 2px solid var(--accent); opacity: 0.3; }
.user-name { font-size: 18px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.user-role { font-size: 13px; color: var(--accent); margin-bottom: 8px; }
.user-since { font-size: 12px; color: var(--text-muted); }
.user-divider { height: 1px; background: var(--border-color); margin: 16px 0; }
.user-actions { display: flex; flex-direction: column; gap: 6px; }
.action-btn { width: 100%; justify-content: flex-start; color: var(--text-secondary) !important; background: transparent !important; border-color: var(--border-color) !important; }
.action-btn:hover { color: var(--accent) !important; border-color: var(--accent) !important; }
.user-links-label { font-size: 11px; color: var(--text-muted); text-align: left; margin-bottom: 6px; letter-spacing: 1px; }
.user-links { display: flex; flex-direction: column; gap: 4px; }
.user-link { display: flex; align-items: center; gap: 8px; padding: 7px 12px; border-radius: var(--radius-sm); cursor: pointer; transition: all 0.2s; font-size: 13px; color: var(--text-secondary); }
.user-link:hover { background: var(--bg-card-hover); color: var(--accent); }

/* 统计区 */
.stats-area { flex: 1; display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat-card {
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); padding: 18px; display: flex; align-items: center; gap: 14px;
  cursor: pointer; transition: border-color 0.2s;
}
.stat-card:hover { border-color: var(--border-light); }
.stat-icon { width: 40px; height: 40px; border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; font-size: 18px; }
.stat-icon.st0 { background: rgba(139,92,246,0.12); color: #8b5cf6; }
.stat-icon.st1 { background: var(--accent-dim); color: var(--accent); }
.stat-icon.st2 { background: rgba(0,184,212,0.12); color: var(--accent-secondary); }
.stat-icon.st3 { background: rgba(255,171,0,0.12); color: var(--warning); }
.stat-body { display: flex; flex-direction: column; }
.stat-val { font-size: 22px; font-weight: 700; color: var(--text-primary); font-family: var(--mono); }
.stat-val.small { font-size: 14px; }
.stat-lbl { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.stats-row-mini { display: flex; gap: 14px; }
.mini-stat { flex: 1; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 12px 16px; display: flex; flex-direction: column; align-items: center; }
.mini-val { font-size: 16px; font-weight: 700; color: var(--text-primary); font-family: var(--mono); }
.mini-val.small { font-size: 13px; }
.mini-lbl { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

/* 面板 */
.bottom-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 18px; }
.panel-header { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 14px; }

/* 任务类型分布 */
.task-bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.task-label { width: 70px; font-size: 12px; color: var(--text-secondary); flex-shrink: 0; }
.task-bar-wrap { flex: 1; height: 10px; border-radius: 5px; background: var(--bg-input); overflow: hidden; }
.task-bar { height: 100%; border-radius: 5px; transition: width 0.6s; }
.task-detection { background: var(--accent); }
.task-change { background: var(--accent-secondary); }
.task-video { background: var(--warning); }
.task-count { font-size: 12px; color: var(--text-muted); font-family: var(--mono); width: 30px; text-align: right; }

/* 模型使用 */
.model-list { display: flex; flex-direction: column; gap: 8px; }
.model-row { display: flex; align-items: center; gap: 8px; }
.model-type-tag { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; flex-shrink: 0; }
.mt-detection { background: var(--accent-dim); color: var(--accent); }
.mt-change { background: rgba(0,184,212,0.12); color: var(--accent-secondary); }
.mt-video { background: rgba(255,171,0,0.12); color: var(--warning); }
.model-name-text { font-size: 13px; color: var(--text-primary); flex: 1; }
.model-count { font-size: 12px; color: var(--text-muted); font-family: var(--mono); }

/* 类别分布 */
.class-list { display: flex; flex-direction: column; gap: 8px; }
.class-row { display: flex; align-items: center; gap: 10px; }
.class-cn { width: 72px; font-size: 12px; color: var(--text-secondary); flex-shrink: 0; text-align: right; }
.class-bar-wrap { flex: 1; height: 8px; border-radius: 4px; background: var(--bg-input); overflow: hidden; }
.class-bar { height: 100%; border-radius: 4px; background: var(--accent); transition: width 0.6s ease; }
.class-count { width: 32px; font-size: 12px; color: var(--accent); font-family: var(--mono); text-align: right; }

/* 最近活动 */
.recent-list { display: flex; flex-direction: column; gap: 6px; }
.recent-row { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: var(--radius-sm); cursor: pointer; transition: background 0.15s; }
.recent-row:hover { background: var(--bg-card-hover); }
.recent-type { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; flex-shrink: 0; }
.rect-detection { background: var(--accent-dim); color: var(--accent); }
.rect-change { background: rgba(0,184,212,0.12); color: var(--accent-secondary); }
.rect-video { background: rgba(255,171,0,0.12); color: var(--warning); }
.recent-filename { font-size: 12px; color: var(--text-primary); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recent-model { font-size: 11px; color: var(--text-muted); font-family: var(--mono); }
.recent-date { font-size: 11px; color: var(--text-muted); flex-shrink: 0; }

.no-data { text-align: center; padding: 20px; color: var(--text-muted); font-size: 13px; }
.empty-hint { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 40px; color: var(--text-muted); font-size: 13px; }
.empty-hint a { color: var(--accent); }
</style>
