<template>
  <div class="profile-page">
    <div class="page-header">
      <h1 class="page-title">个人中心</h1>
      <p class="page-subtitle">账户信息与检测统计</p>
    </div>

    <div class="profile-grid">
      <!-- 左侧：用户信息 -->
      <div class="user-card">
        <div class="user-avatar-wrap">
          <el-avatar :size="72" class="user-avatar">
            <el-icon :size="36"><User /></el-icon>
          </el-avatar>
          <div class="avatar-ring"></div>
        </div>
        <div class="user-name">{{ profile.username }}</div>
        <div class="user-role">{{ profile.role }}</div>
        <div class="user-since">自 {{ profile.created_at }} 加入</div>
        <div class="user-divider"></div>
        <div class="user-actions">
          <el-button size="small" class="action-btn" @click="showEditDialog = true">
            <el-icon><Edit /></el-icon>编辑资料
          </el-button>
          <el-button size="small" class="action-btn" @click="showPwdDialog = true">
            <el-icon><Lock /></el-icon>修改密码
          </el-button>
        </div>
        <div class="user-divider"></div>
        <div class="user-links">
          <div class="user-link" @click="$router.push('/history')">
            <el-icon><Clock /></el-icon><span>检测历史</span>
          </div>
          <div class="user-link" @click="$router.push('/targets')">
            <el-icon><Aim /></el-icon><span>目标库</span>
          </div>
          <div class="user-link" @click="$router.push('/qa')">
            <el-icon><ChatDotRound /></el-icon><span>AI 问答</span>
          </div>
        </div>
      </div>

      <!-- 右侧：统计 -->
      <div class="stats-area">
        <!-- 统计卡片 -->
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-icon st1"><el-icon><Picture /></el-icon></div>
            <div class="stat-body">
              <span class="stat-val">{{ profile.stats.total_detections }}</span>
              <span class="stat-lbl">总检测次数</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon st2"><el-icon><Aim /></el-icon></div>
            <div class="stat-body">
              <span class="stat-val">{{ profile.stats.total_objects }}</span>
              <span class="stat-lbl">累计检出目标</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon st3"><el-icon><Calendar /></el-icon></div>
            <div class="stat-body">
              <span class="stat-val">{{ profile.stats.active_days }}</span>
              <span class="stat-lbl">活跃天数</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon st4"><el-icon><Cpu /></el-icon></div>
            <div class="stat-body">
              <span class="stat-val small">{{ profile.stats.top_model }}</span>
              <span class="stat-lbl">常用模型</span>
            </div>
          </div>
        </div>

        <!-- 底部两栏 -->
        <div class="bottom-row">
          <!-- 类别分布 -->
          <div class="panel class-panel" v-if="profile.class_dist && profile.class_dist.length">
            <div class="panel-header">类别检出分布</div>
            <div class="class-list">
              <div v-for="item in profile.class_dist" :key="item.name" class="class-row">
                <span class="class-cn">{{ item.cn_name }}</span>
                <div class="class-bar-wrap">
                  <div
                    class="class-bar"
                    :style="{ width: barWidth(item.count, profile.class_dist) + '%' }"
                  ></div>
                </div>
                <span class="class-count">{{ item.count }}</span>
              </div>
            </div>
          </div>

          <!-- 模型使用 -->
          <div class="panel model-panel" v-if="profile.model_usage && profile.model_usage.length">
            <div class="panel-header">模型使用</div>
            <div class="model-list">
              <div v-for="m in profile.model_usage" :key="m.key" class="model-row">
                <span class="model-badge" :class="badgeClass(m.key)">{{ m.name }}</span>
                <div class="model-count-bar">
                  <div
                    class="model-bar-fill"
                    :class="barClass(m.key)"
                    :style="{ width: barWidth(m.count, profile.model_usage) + '%' }"
                  ></div>
                </div>
                <span class="model-count">{{ m.count }} 次</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!profile.stats.total_detections" class="empty-hint">
          <el-icon :size="40"><FolderOpened /></el-icon>
          <p>还没有检测记录，去<a href="/detection">智能检测</a>试试吧</p>
        </div>
      </div>
    </div>

    <!-- 编辑资料弹窗 -->
    <el-dialog v-model="showEditDialog" title="编辑资料" width="420px">
      <el-form :model="editForm" label-width="70px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" placeholder="请输入用户名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="showPwdDialog" title="修改密码" width="420px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="80px">
        <el-form-item label="当前密码" prop="oldPassword">
          <el-input v-model="pwdForm.oldPassword" type="password" placeholder="请输入当前密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="pwdForm.newPassword" type="password" placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="pwdForm.confirmPassword" type="password" placeholder="请确认新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPwdDialog = false">取消</el-button>
        <el-button type="primary" @click="changePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { User, Clock, Aim, ChatDotRound, Picture, Calendar, Cpu, FolderOpened, Edit, Lock } from "@element-plus/icons-vue";
import { getSession } from "../utils/auth";
import { getUserProfile } from "../api/detection";

const session = getSession();

const profile = reactive({
  username: session?.username || "未登录",
  role: "普通用户",
  avatar: "",
  created_at: "-",
  stats: { total_detections: 0, total_objects: 0, active_days: 0, success_rate: 0, top_model: "-" },
  class_dist: [],
  model_usage: [],
});

const barWidth = (val, arr) => {
  const max = Math.max(...arr.map(i => i.count), 1);
  return (val / max) * 100;
};

const badgeClass = (key) => {
  if (key.includes("n-")) return "badge-n";
  if (key.includes("m-")) return "badge-m";
  return "badge-x";
};

const barClass = (key) => {
  if (key.includes("n-")) return "fill-n";
  if (key.includes("m-")) return "fill-m";
  return "fill-x";
};

// ── 编辑资料 ──
const showEditDialog = ref(false);
const editForm = reactive({ username: profile.username });

const saveProfile = () => {
  if (!editForm.username.trim()) {
    ElMessage.warning("用户名不能为空");
    return;
  }
  profile.username = editForm.username;
  localStorage.setItem("rsod-username", editForm.username);
  showEditDialog.value = false;
  ElMessage.success("资料已更新");
};

// ── 修改密码 ──
const showPwdDialog = ref(false);
const pwdFormRef = ref(null);
const pwdForm = reactive({ oldPassword: "", newPassword: "", confirmPassword: "" });
const pwdRules = {
  oldPassword: [{ required: true, message: "请输入当前密码", trigger: "blur" }],
  newPassword: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, message: "至少 6 个字符", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认新密码", trigger: "blur" },
    { validator: (_, v, cb) => v !== pwdForm.newPassword ? cb(new Error("两次密码不一致")) : cb(), trigger: "blur" },
  ],
};

const changePassword = () => {
  pwdFormRef.value?.validate((valid) => {
    if (valid) {
      // 本地模拟密码修改
      localStorage.setItem("rsod-password-changed", "true");
      pwdForm.oldPassword = "";
      pwdForm.newPassword = "";
      pwdForm.confirmPassword = "";
      showPwdDialog.value = false;
      ElMessage.success("密码修改成功");
    }
  });
};

onMounted(async () => {
  try {
    const res = await getUserProfile();
    if (res.data) Object.assign(profile, res.data);
    // 确保用户名以 session 为准
    if (session?.username) profile.username = session.username;
  } catch (e) { /* use defaults */ }
});
</script>

<style scoped>
.profile-page { width: 100%; }

.page-header { margin-bottom: 28px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 13px; color: var(--text-muted); }

.profile-grid { display: flex; gap: 24px; align-items: flex-start; }

/* ── 用户卡片 ── */
.user-card {
  width: 240px; flex-shrink: 0;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 32px 24px;
  text-align: center;
}
.user-avatar-wrap { position: relative; display: inline-block; margin-bottom: 16px; }
.user-avatar { background: linear-gradient(135deg, var(--accent), var(--accent-secondary)); }
.avatar-ring {
  position: absolute; inset: -4px; border-radius: 50%;
  border: 2px solid var(--accent); opacity: 0.3;
}
.user-name { font-size: 18px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.user-role { font-size: 13px; color: var(--accent); margin-bottom: 8px; }
.user-since { font-size: 12px; color: var(--text-muted); }
.user-divider { height: 1px; background: var(--border-color); margin: 16px 0; }
.user-actions { display: flex; flex-direction: column; gap: 6px; }
.action-btn {
  width: 100%; justify-content: flex-start;
  color: var(--text-secondary) !important;
  background: transparent !important;
  border-color: var(--border-color) !important;
}
.action-btn:hover { color: var(--accent) !important; border-color: var(--accent) !important; }
.user-links { display: flex; flex-direction: column; gap: 6px; }
.user-link {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border-radius: var(--radius-sm); cursor: pointer; transition: all 0.2s;
  font-size: 13px; color: var(--text-secondary);
}
.user-link:hover { background: var(--bg-card-hover); color: var(--accent); }

/* ── 统计卡片 ── */
.stats-area { flex: 1; display: flex; flex-direction: column; gap: 20px; min-width: 0; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }

.stat-card {
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); padding: 20px; display: flex; align-items: center; gap: 16px;
}
.stat-icon {
  width: 44px; height: 44px; border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center; font-size: 20px;
}
.stat-icon.st1 { background: var(--accent-dim); color: var(--accent); }
.stat-icon.st2 { background: rgba(0, 184, 212, 0.12); color: var(--accent-secondary); }
.stat-icon.st3 { background: rgba(255, 171, 0, 0.12); color: var(--warning); }
.stat-icon.st4 { background: rgba(139, 92, 246, 0.12); color: #8b5cf6; }
.stat-body { display: flex; flex-direction: column; }
.stat-val { font-size: 22px; font-weight: 700; color: var(--text-primary); font-family: var(--mono); }
.stat-val.small { font-size: 14px; }
.stat-lbl { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* ── 底部两栏 ── */
.bottom-row { display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; }

.panel {
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); padding: 20px;
}
.panel-header { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }

/* 类别分布 */
.class-list { display: flex; flex-direction: column; gap: 10px; }
.class-row { display: flex; align-items: center; gap: 10px; }
.class-cn { width: 72px; font-size: 12px; color: var(--text-secondary); flex-shrink: 0; text-align: right; }
.class-bar-wrap { flex: 1; height: 8px; border-radius: 4px; background: var(--bg-input); overflow: hidden; }
.class-bar { height: 100%; border-radius: 4px; background: var(--accent); transition: width 0.6s ease; }
.class-count { width: 32px; font-size: 12px; color: var(--accent); font-family: var(--mono); text-align: right; }

/* 模型使用 */
.model-list { display: flex; flex-direction: column; gap: 14px; }
.model-row { display: flex; align-items: center; gap: 10px; }
.model-badge {
  width: 110px; text-align: center; padding: 3px 8px; border-radius: 4px;
  font-size: 11px; font-weight: 600; flex-shrink: 0;
}
.badge-n { background: rgba(139, 92, 246, 0.12); color: #8b5cf6; }
.badge-m { background: var(--accent-dim); color: var(--accent); }
.badge-x { background: rgba(255, 171, 0, 0.12); color: var(--warning); }
.model-count-bar { flex: 1; height: 6px; border-radius: 3px; background: var(--bg-input); overflow: hidden; }
.model-bar-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
.fill-n { background: #8b5cf6; }
.fill-m { background: var(--accent); }
.fill-x { background: var(--warning); }
.model-count { font-size: 12px; color: var(--text-muted); font-family: var(--mono); flex-shrink: 0; }

.empty-hint {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 40px; color: var(--text-muted); font-size: 13px;
}
.empty-hint a { color: var(--accent); }
</style>
