<template>
  <div class="qa-page">
    <div class="page-header">
      <h1 class="page-title">AI 智能问答</h1>
      <p class="page-subtitle">基于 DeepSeek，实时回答遥感目标检测相关问题</p>
    </div>

    <div class="chat-container">
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-5"/>
            </svg>
          </div>
          <h3>遥感目标检测 AI 助手</h3>
          <p>YOLO11x-OBB · DOTA v1.0 · 15 类目标</p>
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
            <div class="msg-text" v-html="formatContent(msg.content)"></div>
          </div>
        </div>

        <div v-if="streaming" class="message msg-ai">
          <div class="msg-avatar"><el-icon><ChatDotRound /></el-icon></div>
          <div class="msg-bubble">
            <div class="msg-text" v-html="formatContent(streamContent)"></div>
            <span class="cursor">|</span>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <div class="input-row">
          <el-input v-model="question" placeholder="输入你的问题..." :rows="2" type="textarea" :disabled="streaming" @keydown.enter.exact.prevent="sendMessage" class="chat-input" />
          <el-button type="primary" class="send-btn" :loading="streaming" :disabled="!question.trim() || streaming" @click="sendMessage">
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
        <p class="input-hint">Enter 发送 · Shift+Enter 换行</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";
import { ElMessage } from "element-plus";
import { ChatDotRound, User, Promotion } from "@element-plus/icons-vue";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const question = ref("");
const streaming = ref(false);
const streamContent = ref("");
const messages = ref([]);
const messagesContainer = ref(null);

const quickQuestions = [
  "DOTA v1.0 数据集包含哪些类别？",
  "YOLO11-OBB 和标准 YOLO 有什么区别？",
  "遥感图像中小目标检测有哪些难点？",
  "mAP50 和 mAP50-95 分别代表什么？",
  "什么是 OBB（旋转边界框）？",
];

const scrollToBottom = async () => {
  await nextTick();
  const el = messagesContainer.value;
  if (el) el.scrollTop = el.scrollHeight;
};

const sendMessage = async () => {
  const text = question.value.trim();
  if (!text || streaming.value) return;
  messages.value.push({ role: "user", content: text });
  question.value = "";
  streamContent.value = "";
  streaming.value = true;
  await scrollToBottom();

  try {
    const resp = await fetch(`${API_BASE}/qa/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: text,
        history: messages.value.slice(0, -1).map(m => ({ role: m.role, content: m.content })),
      }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) { streamContent.value += data.content; await scrollToBottom(); }
            if (data.done) {
              messages.value.push({ role: "assistant", content: streamContent.value });
              streamContent.value = "";
              streaming.value = false;
            }
            if (data.error) throw new Error(data.error);
          } catch (e) { /* skip parse errors */ }
        }
      }
    }
  } catch (e) {
    if (streamContent.value) messages.value.push({ role: "assistant", content: streamContent.value });
    else messages.value.push({ role: "assistant", content: "请求失败，请稍后重试。" });
    streamContent.value = "";
    streaming.value = false;
    if (e.message !== "done") ElMessage.error("请求失败");
  }
};

const sendQuick = (q) => { question.value = q; sendMessage(); };
const formatContent = (t) => t ? t.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>") : "";
watch(messages, () => scrollToBottom(), { deep: true });
</script>

<style scoped>
.qa-page { width: 100%; height: calc(100vh - 140px); display: flex; flex-direction: column; }

.page-header { margin-bottom: 18px; flex-shrink: 0; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 13px; color: var(--text-muted); }

.chat-container {
  flex: 1; background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); display: flex; flex-direction: column; overflow: hidden;
}

.chat-messages { flex: 1; padding: 24px; overflow-y: auto; }

.welcome { text-align: center; padding: 60px 20px; }
.welcome-icon { width: 72px; height: 72px; border-radius: 50%; background: var(--accent-dim); color: var(--accent); display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; }
.welcome h3 { font-size: 18px; color: var(--text-primary); margin-bottom: 8px; }
.welcome p { font-size: 13px; color: var(--text-muted); margin-bottom: 28px; }
.quick-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.quick-chip { padding: 6px 14px; border-radius: 18px; background: var(--bg-card-hover); color: var(--text-secondary); font-size: 12px; cursor: pointer; border: 1px solid var(--border-color); transition: all 0.2s; }
.quick-chip:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-dim); }

.message { display: flex; margin-bottom: 18px; }
.msg-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0; color: #fff; font-size: 14px; }
.msg-bubble { max-width: 70%; padding: 10px 14px; border-radius: 12px; line-height: 1.7; font-size: 13px; }

.msg-ai .msg-avatar { background: var(--accent); color: var(--on-accent); }
.msg-ai .msg-bubble { background: var(--bg-card-hover); color: var(--text-primary); border-radius: 0 12px 12px 12px; }

.msg-user { flex-direction: row-reverse; }
.msg-user .msg-avatar { background: var(--accent-secondary); color: var(--on-accent); margin-right: 0; margin-left: 10px; }
.msg-user .msg-bubble { background: var(--accent-dim); color: var(--text-primary); border-radius: 12px 0 12px 12px; }

.cursor { animation: blink 1s step-end infinite; color: var(--accent); font-weight: 700; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

.chat-input-area { padding: 14px 24px; border-top: 1px solid var(--border-color); flex-shrink: 0; }
.input-row { display: flex; gap: 10px; align-items: flex-end; }
.send-btn { width: 48px; height: 44px; }
.input-hint { margin-top: 6px; font-size: 11px; color: var(--text-muted); }
</style>
