<template>
  <div class="qa-page">
    <div class="page-header">
      <h1 class="page-title">{{ $t('qa.title') }}</h1>
      <p class="page-subtitle">{{ $t('qa.subtitle') }}</p>
    </div>

    <div class="qa-layout">
      <div class="qa-sidebar">
        <el-button size="small" class="new-chat-btn" @click="newSession">
          <el-icon :size="14"><Plus /></el-icon> {{ $t('qa.newChat') }}
        </el-button>
        <div class="session-list">
          <div v-for="s in sessions" :key="s.id" class="session-item"
               :class="{ active: s.id === currentId }" @click="switchSession(s.id)">
            <div class="session-title" v-if="editingId !== s.id" @dblclick.stop="startRename(s)">{{ s.title }}</div>
            <input v-else class="session-title-input" v-model="editTitle"
              @blur="saveRename(s.id)" @keyup.enter="saveRename(s.id)" @click.stop ref="renameInput" />
            <div class="session-meta">{{ s.messages?.length || 0 }} {{ $t('qa.messagesSuffix') }}</div>
            <el-button class="session-del" size="small" circle @click.stop="deleteSession(s.id)">
              <el-icon :size="12"><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <div class="chat-container">
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome">
            <div class="welcome-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-5"/>
              </svg>
            </div>
            <h3>{{ $t('qa.welcomeTitle') }}</h3>
            <p>{{ $t('qa.welcomeDesc') }}</p>
            <div class="quick-chips">
              <span v-for="q in quickQuestions" :key="q" class="quick-chip" @click="sendQuick(q)">{{ q }}</span>
            </div>
          </div>

          <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="msg.role === 'user' ? 'msg-user' : 'msg-ai'">
            <div class="msg-avatar">
              <el-icon v-if="msg.role === 'assistant'"><ChatDotRound /></el-icon>
              <el-icon v-else><User /></el-icon>
            </div>
            <div class="msg-bubble">
              <div class="msg-text" v-html="renderMarkdown(msg.content)"></div>
              <!-- 知识引用 -->
              <div v-if="msg.references && msg.references.length" class="msg-refs">
                <div class="refs-label">参考来源</div>
                <div v-for="ref in msg.references" :key="ref.title" class="ref-item">
                  <span class="ref-bullet">·</span>
                  <span class="ref-title">{{ ref.title }}</span>
                  <span class="ref-source">{{ ref.source }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="streaming" class="message msg-ai">
            <div class="msg-avatar"><el-icon><ChatDotRound /></el-icon></div>
            <div class="msg-bubble">
              <div class="msg-text" v-html="renderMarkdown(streamContent)"></div>
              <span class="cursor">|</span>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="chat-toolbar">
            <el-button size="small" @click="doExport" :disabled="messages.length === 0">{{ $t('qa.exportMd') }}</el-button>
            <el-button size="small" type="danger" plain @click="clearChat" :disabled="messages.length === 0">{{ $t('qa.clearChat') }}</el-button>
          </div>
          <div class="input-row">
            <el-input v-model="question" :placeholder="$t('qa.placeholder')" :rows="2" type="textarea"
              :disabled="streaming" @keydown.enter.exact.prevent="sendMessage" class="chat-input" />
            <el-button type="primary" class="send-btn" :loading="streaming"
              :disabled="!question.trim() || streaming" @click="sendMessage">
              <el-icon><Promotion /></el-icon>
            </el-button>
          </div>
          <p class="input-hint">{{ $t('qa.enterHint') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { ChatDotRound, User, Promotion, Plus, Close } from "@element-plus/icons-vue";
import { requireLogin, streamRequest } from "../utils/request";
import { useI18n } from "vue-i18n";
import { useChatHistory } from "../composables/useChatHistory";
import { useChatExport } from "../composables/useChatExport";

const { sessions, currentId, messages, newSession, addMessage, switchSession, deleteSession, renameSession } = useChatHistory();
const { exportMarkdown } = useChatExport();

const question = ref("");
const streaming = ref(false);
const streamContent = ref("");
const streamRefs = ref([]);
const editingId = ref(null);
const editTitle = ref("");
const messagesContainer = ref(null);
const { t, locale } = useI18n();

if (!currentId.value) newSession();

const quickQuestions = computed(() => {
  if (locale.value.startsWith('zh')) {
    return ['DOTA v1.0 数据集包含哪些类别？', 'YOLO11-OBB 和标准 YOLO 有什么区别？', '遥感图像中小目标检测有哪些难点？', 'mAP50 和 mAP50-95 分别代表什么？', '什么是 OBB（旋转边界框）？']
  }
  return ['What categories does the DOTA v1.0 dataset include?', 'What is the difference between YOLO11-OBB and standard YOLO?', 'What are the challenges of small object detection in remote sensing?', 'What do mAP50 and mAP50-95 represent?', 'What is OBB (Oriented Bounding Box)?']
})

// ── 安全 markdown 渲染 ──
const HTML_ESCAPE = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, c => HTML_ESCAPE[c]);
}

function renderMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // 代码块 ```...```
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
    `<pre class="md-code-block"><code class="${lang ? 'lang-' + escapeHtml(lang) : ''}">${code}</code></pre>`);

  // 行内代码 `...`
  html = html.replace(/`([^`\n]+)`/g, '<code class="md-inline-code">$1</code>');

  // 分割为段落（双换行）
  const blocks = html.split(/\n\n+/);
  html = blocks.map(block => {
    // 表格 |---|---|
    if (block.includes('|') && block.includes('---')) {
      return renderTable(block);
    }
    // 无序列表
    const ulMatch = block.match(/^(?:[\-\*]\s.*(?:\n|$))+/m);
    if (ulMatch && ulMatch[0] === block.trim()) {
      const items = block.trim().split(/\n/).filter(l => /^[\-\*]\s/.test(l))
        .map(l => `<li>${l.replace(/^[\-\*]\s/, '')}</li>`).join('');
      return `<ul class="md-ul">${items}</ul>`;
    }
    // 有序列表
    const olMatch = block.match(/^(?:\d+\.\s.*(?:\n|$))+/m);
    if (olMatch && olMatch[0] === block.trim()) {
      const items = block.trim().split(/\n/).filter(l => /^\d+\.\s/.test(l))
        .map(l => `<li>${l.replace(/^\d+\.\s/, '')}</li>`).join('');
      return `<ol class="md-ol">${items}</ol>`;
    }
    return `<p class="md-p">${block.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  // 标题 ### / ## / #
  html = html.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
  html = html.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^# (.+)$/gm, '<h2 class="md-h2">$1</h2>');

  // 粗体 **...** 斜体 *...*
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // 横线 ---
  html = html.replace(/^---+$/gm, '<hr class="md-hr">');

  return html;
}

function renderTable(block) {
  const lines = block.trim().split('\n');
  if (lines.length < 2) return `<p>${escapeHtml(block)}</p>`;
  const headerCells = lines[0].split('|').filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join('');
  const bodyRows = lines.slice(2).map(line => {
    const cells = line.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
    return `<tr>${cells}</tr>`;
  }).join('');
  return `<table class="md-table"><thead><tr>${headerCells}</tr></thead><tbody>${bodyRows}</tbody></table>`;
}

// ── 发送 ──
const scrollToBottom = async () => {
  await nextTick();
  const el = messagesContainer.value;
  if (el) el.scrollTop = el.scrollHeight;
};

const startRename = (s) => {
  editingId.value = s.id; editTitle.value = s.title;
  nextTick(() => { const el = document.querySelector('.session-title-input'); if (el) { el.focus(); el.select(); } });
};
const saveRename = (id) => {
  if (editTitle.value.trim()) renameSession(id, editTitle.value.trim());
  editingId.value = null;
};

const sendMessage = async () => {
  const text = question.value.trim();
  if (!text || streaming.value) return;
  if (!(await requireLogin())) return;
  if (!currentId.value) newSession();

  addMessage({ role: "user", content: text });
  question.value = "";
  streamContent.value = "";
  streamRefs.value = [];
  streaming.value = true;
  await scrollToBottom();

  streamRequest(
    "/qa/ask/stream",
    { question: text, history: messages.value.slice(0, -1).map(m => ({ role: m.role, content: m.content })) },
    (data) => {
      if (data.content) { streamContent.value += data.content; scrollToBottom(); }
      if (data.references) { streamRefs.value = data.references; }
      if (data.done) {
        addMessage({ role: "assistant", content: streamContent.value, references: streamRefs.value });
        streamContent.value = "";
        streaming.value = false;
      }
      if (data.error) {
        addMessage({ role: "assistant", content: t('qa.serviceUnavailable') });
        streamContent.value = "";
        streaming.value = false;
      }
    },
    () => {},
    () => {
      if (streamContent.value) addMessage({ role: "assistant", content: streamContent.value });
      else addMessage({ role: "assistant", content: t('qa.requestFailed') });
      streamContent.value = "";
      streaming.value = false;
    }
  );
};

const sendQuick = (q) => { question.value = q; sendMessage(); };

const doExport = () => {
  const s = sessions.value.find(s => s.id === currentId.value);
  if (s) exportMarkdown(s);
};

const clearChat = async () => {
  try {
    await ElMessageBox.confirm(t('qa.confirmClear'), t('qa.confirmTitle'), { type: "warning" });
    deleteSession(currentId.value);
    newSession();
    ElMessage.success(t('qa.clearSuccess'));
  } catch (e) { /* cancelled */ }
};

watch(messages, () => scrollToBottom(), { deep: true });
</script>

<style scoped>
.qa-page { width: 100%; height: calc(100vh - 140px); display: flex; flex-direction: column; }
.page-header { margin-bottom: 18px; flex-shrink: 0; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 13px; color: var(--text-muted); }
.qa-layout { flex: 1; display: flex; gap: 14px; overflow: hidden; }

.qa-sidebar {
  width: 220px; flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); padding: 14px; overflow-y: auto;
}
.new-chat-btn { width: 100%; }
.session-list { display: flex; flex-direction: column; gap: 6px; }
.session-item {
  position: relative; padding: 10px 12px; background: var(--bg-input);
  border: 1px solid var(--border-color); border-radius: var(--radius-sm);
  cursor: pointer; transition: all 0.15s;
}
.session-item:hover { border-color: var(--border-light); }
.session-item.active { border-color: var(--accent); background: var(--accent-dim); }
.session-title { font-size: 13px; font-weight: 500; color: var(--text-primary); margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-title-input { font-size: 13px; padding: 2px 4px; border: 1px solid var(--accent); border-radius: 3px; background: var(--bg-card); color: var(--text-primary); outline: none; width: calc(100% - 30px); }
.session-meta { font-size: 11px; color: var(--text-muted); }
.session-del { position: absolute; top: 4px; right: 4px; opacity: 0; transition: opacity 0.15s; }
.session-item:hover .session-del { opacity: 1; }

.chat-container { flex: 1; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-lg); display: flex; flex-direction: column; overflow: hidden; }
.chat-messages { flex: 1; padding: 24px; overflow-y: auto; }
.welcome { text-align: center; padding: 40px 20px; }
.welcome-icon { width: 72px; height: 72px; border-radius: 50%; background: var(--accent-dim); color: var(--accent); display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; }
.welcome h3 { font-size: 18px; color: var(--text-primary); margin-bottom: 8px; }
.welcome p { font-size: 13px; color: var(--text-muted); margin-bottom: 28px; }
.quick-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.quick-chip { padding: 6px 14px; border-radius: 18px; background: var(--bg-card-hover); color: var(--text-secondary); font-size: 12px; cursor: pointer; border: 1px solid var(--border-color); transition: all 0.2s; }
.quick-chip:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-dim); }

.message { display: flex; margin-bottom: 18px; }
.msg-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0; font-size: 14px; }
.msg-bubble { max-width: 80%; padding: 10px 14px; border-radius: 12px; line-height: 1.7; font-size: 13px; }
.msg-ai .msg-avatar { background: var(--accent); color: var(--on-accent); }
.msg-ai .msg-bubble { background: var(--bg-card-hover); color: var(--text-primary); border-radius: 0 12px 12px 12px; }
.msg-user { flex-direction: row-reverse; }
.msg-user .msg-avatar { background: var(--accent-secondary); color: var(--on-accent); margin-right: 0; margin-left: 10px; }
.msg-user .msg-bubble { background: var(--accent-dim); color: var(--text-primary); border-radius: 12px 0 12px 12px; }
.cursor { animation: blink 1s step-end infinite; color: var(--accent); font-weight: 700; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

/* 知识引用 */
.msg-refs { margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border-color); }
.refs-label { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; font-weight: 600; }
.ref-item { display: flex; align-items: baseline; gap: 4px; font-size: 11px; color: var(--text-muted); padding: 2px 0; }
.ref-bullet { color: var(--accent); }
.ref-title { color: var(--accent); font-weight: 500; }
.ref-source { color: var(--text-muted); font-size: 10px; }

/* markdown 样式 */
.msg-text :deep(.md-p) { margin: 0 0 8px; }
.msg-text :deep(.md-p:last-child) { margin-bottom: 0; }
.msg-text :deep(.md-h2) { font-size: 16px; font-weight: 700; margin: 12px 0 6px; }
.msg-text :deep(.md-h3) { font-size: 14px; font-weight: 700; margin: 10px 0 4px; }
.msg-text :deep(.md-h4) { font-size: 13px; font-weight: 600; margin: 8px 0 4px; }
.msg-text :deep(.md-ul), .msg-text :deep(.md-ol) { margin: 6px 0; padding-left: 20px; }
.msg-text :deep(.md-ul li), .msg-text :deep(.md-ol li) { margin: 2px 0; }
.msg-text :deep(.md-code-block) {
  background: var(--bg-deep); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); padding: 10px 14px; margin: 8px 0;
  font-family: var(--mono); font-size: 12px; overflow-x: auto; white-space: pre-wrap;
}
.msg-text :deep(.md-inline-code) {
  background: var(--bg-deep); padding: 1px 5px; border-radius: 3px;
  font-family: var(--mono); font-size: 12px;
}
.msg-text :deep(.md-table) { border-collapse: collapse; margin: 8px 0; width: 100%; }
.msg-text :deep(.md-table th) { background: var(--bg-deep); padding: 6px 10px; border: 1px solid var(--border-color); font-size: 12px; font-weight: 600; text-align: left; }
.msg-text :deep(.md-table td) { padding: 6px 10px; border: 1px solid var(--border-color); font-size: 12px; }
.msg-text :deep(.md-hr) { border: none; border-top: 1px solid var(--border-color); margin: 10px 0; }
.msg-text :deep(strong) { font-weight: 700; color: var(--text-primary); }

.chat-input-area { padding: 14px 24px; border-top: 1px solid var(--border-color); flex-shrink: 0; }
.chat-toolbar { display: flex; gap: 8px; margin-bottom: 10px; }
.input-row { display: flex; gap: 10px; align-items: flex-end; }
.send-btn { width: 48px; height: 44px; }
.input-hint { margin-top: 6px; font-size: 11px; color: var(--text-muted); }
</style>
