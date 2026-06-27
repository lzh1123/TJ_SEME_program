import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import EditorView from '../views/EditorView.vue'
import { authService } from '../services/auth.js'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false, guestOnly: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { requiresAuth: false, guestOnly: true }
  },
  {
    path: '/editor',
    name: 'editor',
    component: EditorView,
    meta: { requiresAuth: true }
  },
  {
    path: '/editor/:id',
    name: 'editor-with-id',
    component: EditorView,
    meta: { requiresAuth: true }
  },
  {
    path: '/outline-editor',
    name: 'outline-editor',
    component: () => import('../views/OutlineEditorView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/knowledge-base',
    name: 'knowledge-base',
    component: () => import('../views/KnowledgeBaseView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/batch-eval',
    name: 'batch-eval',
    component: () => import('../views/BatchEvalView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫：需要登录的页面跳转到登录页
router.beforeEach((to, from, next) => {
  const isAuthenticated = authService.isAuthenticated

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.meta.guestOnly && isAuthenticated) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
