<template>
  <div class="input-wrapper">
    <textarea
      v-model="inputValue"
      class="chat-textarea"
      placeholder="请输入你的问题，例如：皮卡丘是什么属性？"
      rows="3"
      :disabled="loading"
      @keydown.enter.exact.prevent="handleSend"
    />

    <button
      class="send-btn"
      :disabled="loading || !inputValue.trim()"
      @click="handleSend"
    >
      {{ loading ? '发送中...' : '发送' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send'])

const inputValue = ref('')

function handleSend() {
  const question = inputValue.value.trim()
  if (!question || props.loading) return

  emit('send', question)
  inputValue.value = ''
}
</script>

<style scoped>
.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 16px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}

.chat-textarea {
  flex: 1;
  resize: none;
  border: 1px solid #dcdfe6;
  border-radius: 12px;
  padding: 12px 14px;
  outline: none;
  font-size: 14px;
  line-height: 1.6;
}

.chat-textarea:focus {
  border-color: #409eff;
}

.send-btn {
  min-width: 96px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: #409eff;
  color: white;
  font-size: 14px;
  cursor: pointer;
}

.send-btn:disabled {
  background: #b3d8ff;
  cursor: not-allowed;
}
</style>