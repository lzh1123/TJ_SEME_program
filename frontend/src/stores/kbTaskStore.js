/**
 * Knowledge Base Task Store - tracks async import tasks across page navigation.
 *
 * The store persists only active tasks. Completed, failed, stale, or server-missing
 * tasks are removed immediately so refreshes cannot resurrect old placeholders.
 */
import { reactive } from 'vue'
import { apiService } from '../services/api.js'

const SESSION_KEY = 'slideon_kb_active_tasks'
const MAX_TASK_AGE_MS = 30 * 60 * 1000
const TERMINAL_STATUSES = new Set(['completed', 'failed', 'not_found'])

const state = reactive({
  uploading: false,
  tasks: [],
  progressPercent: 0,
  progressText: '',
})

let pollTimer = null

function _now() {
  return Date.now()
}

function _isActiveTask(task) {
  if (!task || !task.taskId) return false
  if (TERMINAL_STATUSES.has(task._status)) return false
  if (task.createdAt && _now() - task.createdAt > MAX_TASK_AGE_MS) return false
  return Array.isArray(task.filenames) && task.filenames.length > 0
}

function _persist() {
  try {
    const activeTasks = state.tasks.filter(_isActiveTask)
    if (activeTasks.length === 0) {
      sessionStorage.removeItem(SESSION_KEY)
    } else {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(activeTasks))
    }
  } catch {}
}

function _loadPersisted() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    const saved = raw ? JSON.parse(raw) : []
    const activeTasks = Array.isArray(saved) ? saved.filter(_isActiveTask) : []
    if (activeTasks.length !== saved.length) {
      if (activeTasks.length > 0) {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(activeTasks))
      } else {
        sessionStorage.removeItem(SESSION_KEY)
      }
    }
    return activeTasks
  } catch {
    return []
  }
}

function _clearPersisted() {
  try {
    sessionStorage.removeItem(SESSION_KEY)
  } catch {}
}

function _startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(_pollTick, 2000)
}

function _stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function _resetProgress() {
  state.uploading = false
  state.progressPercent = 0
  state.progressText = ''
}

async function _pollTick() {
  const activeBeforePoll = state.tasks.filter(_isActiveTask)
  if (activeBeforePoll.length === 0) {
    state.tasks = []
    _resetProgress()
    _clearPersisted()
    _stopPolling()
    return
  }

  const nextTasks = []
  let totalProcessed = 0
  let totalFiles = 0

  for (const task of activeBeforePoll) {
    try {
      const t = await apiService.getImportTaskStatus(task.taskId)
      const total = t.total || task.total || task.fileCount || task.filenames.length
      const processed = t.processed || 0
      const status = t.status || 'processing'

      task.processed = processed
      task.total = total
      task._status = status
      task._errors = t.errors || []

      if (status === 'completed' || status === 'failed') {
        continue
      }

      totalProcessed += processed
      totalFiles += total
      nextTasks.push(task)
    } catch (error) {
      if (error?.status === 404) {
        task._status = 'not_found'
        continue
      }

      const total = task.total || task.fileCount || task.filenames.length
      totalProcessed += task.processed || 0
      totalFiles += total
      nextTasks.push(task)
    }
  }

  state.tasks = nextTasks.filter(_isActiveTask)

  if (state.tasks.length === 0) {
    _resetProgress()
    _clearPersisted()
    _stopPolling()
    return
  }

  state.uploading = true
  state.progressPercent = totalFiles > 0 ? Math.round((totalProcessed / totalFiles) * 100) : 0
  state.progressText = `处理中 ${totalProcessed}/${totalFiles}`
  _persist()
}

export function useKBTasks() {
  function addTask(taskId, fileCount, filenames) {
    const safeNames = Array.isArray(filenames) ? filenames.filter(Boolean) : []
    if (!taskId || safeNames.length === 0) return

    state.uploading = true
    state.tasks.push({
      taskId,
      fileCount,
      filenames: safeNames,
      processed: 0,
      total: fileCount,
      createdAt: _now(),
      _status: 'processing',
      _errors: [],
    })
    state.progressPercent = 0
    state.progressText = `处理中 0/${fileCount}`
    _persist()
    _startPolling()
  }

  function resumeFromStorage() {
    if (state.tasks.length === 0) {
      state.tasks = _loadPersisted()
    } else {
      state.tasks = state.tasks.filter(_isActiveTask)
    }

    if (state.tasks.length === 0) {
      _resetProgress()
      _clearPersisted()
      _stopPolling()
      return false
    }

    state.uploading = true
    _startPolling()
    return true
  }

  function removeFiles(filenames) {
    const names = new Set(Array.isArray(filenames) ? filenames : [filenames])
    state.tasks = state.tasks
      .map(task => {
        const keptNames = (task.filenames || []).filter(name => !names.has(name))
        return {
          ...task,
          filenames: keptNames,
          fileCount: keptNames.length,
          total: Math.min(task.total || keptNames.length, keptNames.length),
        }
      })
      .filter(_isActiveTask)

    if (state.tasks.length === 0) {
      clearCompleted()
    } else {
      _persist()
    }
  }

  function clearCompleted() {
    state.tasks = []
    _resetProgress()
    _clearPersisted()
    _stopPolling()
  }

  function isPolling() {
    return pollTimer !== null
  }

  return {
    state,
    addTask,
    resumeFromStorage,
    removeFiles,
    clearCompleted,
    isPolling,
    stopPolling: _stopPolling,
  }
}
