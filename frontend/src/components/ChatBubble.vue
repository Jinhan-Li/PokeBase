<template>
  <div :class="['bubble-row', message.role]">
    <div class="avatar">
      {{ message.role === 'user' ? '我' : 'AI' }}
    </div>

    <div class="bubble-card">
      <div class="bubble-role">
        {{ message.role === 'user' ? '用户' : '宝可梦助手' }}
      </div>

      <div class="bubble-content">
        {{ message.content }}
      </div>

      <div
        v-if="message.role === 'assistant' && message.cypher"
        class="extra-block"
      >
        <div class="extra-title">Cypher 查询</div>
        <pre>{{ message.cypher }}</pre>
      </div>

      <div
        v-if="message.role === 'assistant' && message.data && message.data.length"
        class="extra-block"
      >
        <div class="extra-title">原始数据</div>
        <pre>{{ formatData(message.data) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

function formatData(data) {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}
</script>

<style scoped>
.bubble-row {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
  align-items: flex-start;
}

.bubble-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
}

.user .avatar {
  background: #67c23a;
}

.bubble-card {
  max-width: 76%;
  background: #fff;
  border-radius: 16px;
  padding: 14px 16px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
  border: 1px solid #ebeef5;
}

.user .bubble-card {
  background: #ecf9ec;
}

.bubble-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.bubble-content {
  font-size: 15px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.extra-block {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #dcdfe6;
}

.extra-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  font-weight: 600;
}

pre {
  margin: 0;
  background: #f7f8fa;
  border-radius: 10px;
  padding: 10px;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>