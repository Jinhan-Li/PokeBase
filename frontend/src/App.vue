<template>
  <div class="chat-container">
    <h1>🔍 宝可梦知识图谱问答</h1>
    <div class="messages">
      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <strong>{{ msg.role === 'user' ? '🧑 你' : '🤖 AI' }}:</strong>
        <p>{{ msg.content }}</p>
      </div>
      <div v-if="loading" class="message ai loading">
        🤖 AI 思考中...
      </div>
    </div>
    <div class="input-area">
      <input
        v-model="input"
        @keyup.enter="send"
        placeholder="输入问题，例如：皮卡丘是什么属性？"
        :disabled="loading"
      />
      <button @click="send" :disabled="loading || !input.trim()">
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { chat } from './api'

const input = ref('')
const messages = ref([])
const loading = ref(false)

async function send() {
  if (!input.value.trim() || loading.value) return
  const q = input.value.trim()
  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true

  try {
    const res = await chat(q)
    messages.value.push({ role: 'ai', content: res.data.answer })
  } catch (e) {
    messages.value.push({ role: 'ai', content: '请求失败：' + e.message })
  }
  loading.value = false
}
</script>

<style>
* {
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  margin: 0;
  padding: 20px;
  background: #f5f5f5;
}

.chat-container {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
}

.messages {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  min-height: 400px;
  background: white;
  max-height: 60vh;
  overflow-y: auto;
}

.message {
  margin: 10px 0;
  padding: 10px 15px;
  border-radius: 8px;
}

.message.user {
  background: #e3f2fd;
  text-align: right;
}

.message.ai {
  background: #f0f0f0;
}

.message.loading {
  color: #666;
  font-style: italic;
}

.input-area {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.input-area input {
  flex: 1;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.input-area input:focus {
  outline: none;
  border-color: #2196f3;
}

.input-area button {
  padding: 12px 25px;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.input-area button:hover:not(:disabled) {
  background: #1976d2;
}

.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
