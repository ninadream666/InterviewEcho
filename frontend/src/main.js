/**
 * 模块名称：应用入口（main.js）
 * 功能描述：Vue 3 应用启动入口，初始化 Pinia、Vue Router、Element Plus 和全局样式。
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
