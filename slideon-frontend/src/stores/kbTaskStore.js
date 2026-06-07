/**
 * Knowledge Base Task Store — tracks async import tasks across page navigation.
 *
 * Design: module-level reactive state + module-level poll timer, identical to
 * the pattern used by useFloatingBall.js. This ensures that when the user
 * navigates away from the KB page and returns, the upload progress is still
 * visible and the timer keeps polling.
 *
 * sessionStorage is used as a secondary persistence layer so that timers
 * survive a page refresh within the same tab.
 */
import { reactive } from 'vue'
import { apiService } from '../services/api.js'

const SESSION_KEY = 'slideon_kb_active_tasks'

// ── Module-level reactive state (persists across SPA navigation) ──
const state = reactive({
  uploading: false,
  tasks: [],        // [{ taskId, fileCount, filenames, processed, total }]
  progressPercent: 0,
  progressText: '',
})

let pollTimer = null

// ── sessionStorage helpers ──
function _persist() {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(state.tasks))
  } catch {}
}

function _loadPersisted() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function _clearPersisted() {
  try {
    sessionStorage.removeItem(SESSION_KEY)
  } catch {}
}

// ── Polling ──
function _startPolling() {
  if (pollTimer) return // Already running
  pollTimer = setInterval(_pollTick, 2000)
}

function _stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function _pollTick() {
  if (state.tasks.length === 0) {
    _stopPolling()
    return
  }

  let allDone = true
  let totalProcessed = 0
  let totalFiles = 0
  const MAX_FAILURES = 5  // ~10 seconds of failures before giving up

  for (const task of [...state.tasks]) {
    try {
      const t = await apiService.getImportTaskStatus(task.taskId)
      task.processed = t.processed || 0
      task.total = t.total || task.fileCount
      task._status = t.status
      task._errors = t.errors || []
      task._failures = 0  // Reset on success

      totalProcessed += task.processed
      totalFiles += task.total

      if (t.status !== 'completed' && t.status !== 'failed') {
        allDone = false
      }
    } catch {
      task._failures = (task._failures || 0) + 1
      // Only remove after repeated failures (e.g. task was cleaned up on server)
      if (task._failures > MAX_FAILURES) {
        state.tasks = state.tasks.filter(x => x.taskId !== task.taskId)
      }
      // Still count toward totals using last-known values
      totalProcessed += task.processed || 0
      totalFiles += task.total || task.fileCount
      allDone = false
    }
  }

  if (totalFiles > 0) {
    state.progressPercent = Math.round((totalProcessed / totalFiles) * 100)
  }
  state.progressText = `处理中 ${totalProcessed}/${totalFiles}`

  if (allDone && state.tasks.length > 0) {
    _stopPolling()
    state.uploading = false
    _clearPersisted()
  }

  _persist()
}

// ── Public API ──
export function useKBTasks() {
  /**
   * Register a new import task and start background polling.
   * Safe to call multiple times — each call adds to the task list.
   */
  function addTask(taskId, fileCount, filenames) {
    state.uploading = true
    state.tasks.push({
      taskId,
      fileCount,
      filenames,
      processed: 0,
      total: fileCount,
      _status: 'processing',
      _errors: [],
    })
    _persist()
    _startPolling()
  }

  /**
   * Called by the KB page on mount. Returns the current set of active tasks.
   * Restarts polling if there are saved tasks from a previous session.
   */
  function resumeFromStorage() {
    if (state.tasks.length === 0) {
      const saved = _loadPersisted()
      if (saved.length > 0) {
        state.tasks = saved
        state.uploading = true
        _startPolling()
        return true
      }
      return false
    }
    // Tasks already in memory (same SPA session)
    _startPolling()
    return true
  }

  /**
   * Called when all tasks are done and the component has consumed the results.
   */
  function clearCompleted() {
    state.tasks = []
    state.uploading = false
    state.progressPercent = 0
    state.progressText = ''
    _clearPersisted()
    _stopPolling()
  }

  /** Whether polling is currently active. */
  function isPolling() {
    return pollTimer !== null
  }

  return {
    state,
    addTask,
    resumeFromStorage,
    clearCompleted,
    isPolling,
    stopPolling: _stopPolling,
  }
}
