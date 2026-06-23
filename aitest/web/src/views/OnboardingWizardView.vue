<script setup lang="ts">
import { computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useOnboardingStore } from '@/stores/onboarding'
import { useOnboardingWS } from '@/composables/useOnboardingWS'
import StepChooseSource from '@/components/onboarding/StepChooseSource.vue'
import StepUrlInput from '@/components/onboarding/StepUrlInput.vue'
import StepScanning from '@/components/onboarding/StepScanning.vue'
import StepConfirmMenu from '@/components/onboarding/StepConfirmMenu.vue'
import StepResults from '@/components/onboarding/StepResults.vue'
import { Globe, Wifi, ListTree, FileSearch, CheckCircle2, AlertTriangle, ArrowRight, FolderOpen } from 'lucide-vue-next'
import { ref } from 'vue'

const store = useOnboardingStore()
const router = useRouter()
const { disconnect, wsError } = useOnboardingWS()

const sourceChosen = ref(false)

const STEPS = [
  { key: 'source', label: 'Source', icon: FolderOpen },
  { key: 'discovery', label: 'Discovery', icon: Wifi },
  { key: 'confirm', label: 'Review', icon: ListTree },
  { key: 'results', label: 'Results', icon: CheckCircle2 },
]

const currentStepIndex = computed(() => {
  if (store.isComplete) return 3
  if (store.isMenuReady) return 2
  if (store.isRunning || sourceChosen.value) return 1
  return 0
})

function onSourceChoose(type: 'url' | 'local', value: string) {
  store.sourceType = type
  if (type === 'local') {
    store.projectPath = value
    store.baseUrl = value  // Show path in UI
    // Derive project ID from folder name
    const parts = value.replace(/\\/g, '/').replace(/\/$/, '').split('/')
    const folderName = parts[parts.length - 1] || 'local-project'
    store.projectId = folderName
    store.start(value, folderName, '', '')
  } else {
    store.baseUrl = value
  }
  sourceChosen.value = true
}

function openProject() {
  router.push({ path: '/kanban', query: { project: store.projectId } })
}

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <div class="onboarding-wizard">
    <!-- Header -->
    <header class="wizard-header">
      <h2>New Project Onboarding</h2>
      <p class="subtitle">Enter a URL — TLO auto-discovers the application structure</p>
    </header>

    <!-- Step indicators -->
    <nav class="step-indicators">
      <div
        v-for="(step, i) in STEPS"
        :key="step.key"
        class="step-dot"
        :class="{
          active: i === currentStepIndex,
          done: i < currentStepIndex,
          error: store.isFailed && i === currentStepIndex,
        }"
      >
        <component :is="step.icon" :size="18" />
        <span class="step-label">{{ step.label }}</span>
      </div>
    </nav>

    <!-- Progress bar -->
    <div v-if="store.isRunning || store.isComplete" class="progress-bar-wrapper">
      <div class="progress-bar">
        <div
          class="progress-fill"
          :class="{ complete: store.isComplete, error: store.isFailed }"
          :style="{ width: (store.progress * 100) + '%' }"
        />
      </div>
      <span class="progress-text">{{ Math.round(store.progress * 100) }}%</span>
    </div>

    <!-- Error banner -->
    <div v-if="wsError" class="error-banner">
      <AlertTriangle :size="16" />
      <span>{{ wsError }}</span>
    </div>

    <!-- Step content -->
    <main class="wizard-body">
      <!-- Step 0: Choose source -->
      <StepChooseSource
        v-if="currentStepIndex === 0 && !sourceChosen"
        @choose="onSourceChoose"
      />
      <!-- Step 0.5: URL input (only for URL source) -->
      <StepUrlInput
        v-else-if="currentStepIndex === 1 && !store.isRunning && store.sourceType === 'url'"
      />
      <!-- Step 1: Discovery scanning -->
      <StepScanning v-else-if="currentStepIndex === 1 && store.isRunning" />
      <!-- Step 2: Menu confirmation -->
      <StepConfirmMenu v-else-if="currentStepIndex === 2" />
      <!-- Step 3: Results -->
      <StepResults v-else-if="currentStepIndex === 3" />

      <!-- Failed state -->
      <div v-if="store.isFailed" class="failed-state">
        <AlertTriangle :size="48" class="error-icon" />
        <h3>Onboarding failed</h3>
        <ul v-if="store.errors.length" class="error-list">
          <li v-for="(err, i) in store.errors" :key="i">{{ err }}</li>
        </ul>
        <div class="btn-row">
          <button class="btn btn-secondary" @click="store.reset()">Try Again</button>
        </div>
      </div>
    </main>

    <!-- Footer actions -->
    <footer class="wizard-footer">
      <button
        v-if="store.isRunning || store.isMenuReady"
        class="btn btn-outline"
        @click="store.cancel()"
      >
        Cancel
      </button>
      <button
        v-if="store.isComplete"
        class="btn btn-primary"
        @click="openProject"
      >
        Open Project <ArrowRight :size="16" />
      </button>
    </footer>
  </div>
</template>

<style scoped>
.onboarding-wizard {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
  animation: fade-in 0.3s ease-out;
}

.wizard-header {
  margin-bottom: 32px;
  text-align: center;
}
.wizard-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--foreground);
  margin: 0 0 8px;
}
.subtitle {
  color: var(--muted-foreground);
  font-size: 0.9rem;
  margin: 0;
}

/* Step indicators */
.step-indicators {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 24px;
}
.step-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--muted-foreground);
  transition: color 0.2s;
}
.step-dot.active {
  color: var(--primary);
}
.step-dot.done {
  color: var(--success);
}
.step-dot.error {
  color: var(--destructive);
}
.step-label {
  font-size: 0.75rem;
  font-weight: 500;
}

/* Progress bar */
.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--secondary);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--primary);
  border-radius: var(--radius-full);
  transition: width 0.5s ease;
}
.progress-fill.complete {
  background: var(--success);
}
.progress-fill.error {
  background: var(--destructive);
}
.progress-text {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--muted-foreground);
  min-width: 3em;
  text-align: right;
}

/* Body */
.wizard-body {
  min-height: 300px;
}

/* Footer */
.wizard-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

/* Error */
.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--warning-light);
  color: var(--warning);
  padding: 8px 16px;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  font-size: 0.85rem;
}
.failed-state {
  text-align: center;
  padding: 48px 0;
}
.error-icon {
  color: var(--destructive);
  margin-bottom: 16px;
}
.failed-state h3 {
  margin: 0 0 16px;
  color: var(--destructive);
}
.error-list {
  list-style: none;
  padding: 0;
  color: var(--muted-foreground);
  font-size: 0.85rem;
}
.error-list li {
  padding: 4px 0;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: background 0.15s, color 0.15s;
}
.btn-primary {
  background: var(--primary);
  color: var(--primary-foreground);
}
.btn-primary:hover { filter: brightness(1.1); }
.btn-secondary {
  background: var(--secondary);
  color: var(--secondary-foreground);
}
.btn-outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted-foreground);
}
.btn-outline:hover {
  background: var(--secondary);
}
.btn-row {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
