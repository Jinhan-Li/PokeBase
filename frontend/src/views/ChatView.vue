<template>
  <div class="page">
    <div class="header">
      <h1>宝可梦知识图谱问答系统</h1>
      <p>基于 Vue 3 + FastAPI + Neo4j + PokeAPI 的智能问答界面</p>
    </div>

    <div class="chat-panel">
      <div ref="messageListRef" class="message-list">
        <ChatBubble
          v-for="(message, index) in messages"
          :key="index"
          :message="message"
        />

        <div v-if="loading" class="status loading">
          宝可梦助手正在查询知识图谱，请稍候...
        </div>

        <div v-if="errorMessage" class="status error">
          {{ errorMessage }}
        </div>
      </div>

      <ChatInput :loading="loading" @send="handleSend" />
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import ChatBubble from '../components/ChatBubble.vue'
import ChatInput from '../components/ChatInput.vue'
import { chatWithPokemon } from '../api/index.js'

const loading = ref(false)
const errorMessage = ref('')
const messageListRef = ref(null)

const messages = ref([
  {
    role: 'assistant',
    content:
      '你好，我是宝可梦知识图谱助手。你可以问我：皮卡丘是什么属性？小火龙有什么特性？火属性克制哪些属性？'
  }
])

function scrollToBottom() {
  nextTick(() => {
    const el = messageListRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

async function handleSend(question) {
  errorMessage.value = ''

  messages.value.push({
    role: 'user',
    content: question
  })

  loading.value = true
  scrollToBottom()

  try {
    const result = await chatWithPokemon(question)

    messages.value.push({
      role: 'assistant',
      content: result.answer || '查询成功，但未返回自然语言答案。',
      cypher: result.cypher || '',
      data: Array.isArray(result.data) ? result.data : []
    })
  } catch (error) {
    errorMessage.value = error.message || '请求失败，请稍后重试'
    messages.value.push({
      role: 'assistant',
      content: '抱歉，当前无法完成查询，请检查后端服务或稍后再试。'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24px;
  background:
    linear-gradient(180deg, #eaf3ff 0%, #f4f6fb 100%);
}

.header {
  text-align: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
  font-size: 32px;
  color: #303133;
}

.header p {
  margin-top: 10px;
  color: #606266;
  font-size: 15px;
}

.chat-panel {
  width: min(1000px, 96%);
  height: 78vh;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: #ffffffcc;
  backdrop-filter: blur(6px);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
  border: 1px solid #ebeef5;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.status {
  text-align: center;
  margin: 12px 0;
  font-size: 14px;
}

.loading {
  color: #409eff;
}

.error {
  color: #f56c6c;
}
</style>