<script setup lang="ts">
import { ref } from 'vue'
import { useOnboardingStore } from '@/stores/onboarding'
import { Globe, Lock, Play, Loader2 } from 'lucide-vue-next'

const store = useOnboardingStore()

const url = ref('https://')
const projectId = ref('')
const username = ref('admin')
const password = ref('')
const validating = ref(false)
const urlError = ref('')

function isValidUrl(val: string): boolean {
  try {
    new URL(val)
    return true
  } catch {
    return false
  }
}

async function handleStart() {
  urlError.value = ''
  if (!url.value || !isValidUrl(url.value)) {
    urlError.value = 'Please enter a valid URL (e.g. https://example.com)'
    return
  }
  const pid = projectId.value.trim() || url.value.replace(/https?:\/\//, '').replace(/[.\/]/g, '-').replace(/-+$/, '').substring(0, 40)
  validating.value = true
  await store.start(url.value, pid, username.value, password.value)
  validating.value = false
}
</script>

<template>
  <div class="step-url">
    <div class="form-group">
      <label>
        <Globe :size="16" />
        <span>Application URL</span>
      </label>
      <input
        v-model="url"
        type="url"
        placeholder="https://your-app.example.com"
        :class="{ error: urlError }"
        @keyup.enter="handleStart"
      />
      <p v-if="urlError" class="field-error">{{ urlError }}</p>
      <p class="hint">Paste the base URL of your web application</p>
    </div>

    <div class="form-group">
      <label>
        <span>Project Name (optional)</span>
      </label>
      <input
        v-model="projectId"
        type="text"
        placeholder="auto-detected from URL"
      />
      <p class="hint">Short slug for this project. Auto-generated if empty.</p>
    </div>

    <div class="credentials-row">
      <div class="form-group">
        <label>
          <Lock :size="16" />
          <span>Username</span>
        </label>
        <input v-model="username" type="text" placeholder="admin" />
      </div>
      <div class="form-group">
        <label>
          <Lock :size="16" />
          <span>Password</span>
        </label>
        <input v-model="password" type="password" placeholder="(if login required)" />
      </div>
    </div>

    <button
      class="btn-start"
      :disabled="validating || !url"
      @click="handleStart"
    >
      <Loader2 v-if="validating" :size="18" class="spin" />
      <Play v-else :size="18" />
      <span>{{ validating ? 'Connecting...' : 'Start Discovery' }}</span>
    </button>
  </div>
</template>

<style scoped>
.step-url {
  padding: 16px 0;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--foreground);
  margin-bottom: 6px;
}
.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--card);
  color: var(--foreground);
  font-size: 0.9rem;
}
.form-group input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: var(--shadow-focus);
}
.form-group input.error {
  border-color: var(--destructive);
}
.field-error {
  color: var(--destructive);
  font-size: 0.8rem;
  margin: 4px 0 0;
}
.hint {
  color: var(--muted-foreground);
  font-size: 0.78rem;
  margin: 4px 0 0;
}
.credentials-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.btn-start {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 32px;
  background: var(--primary);
  color: var(--primary-foreground);
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.15s;
  margin-top: 8px;
}
.btn-start:hover:not(:disabled) {
  filter: brightness(1.1);
}
.btn-start:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
