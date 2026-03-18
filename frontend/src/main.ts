import { createApp } from 'vue'
import App from './App.vue' // 根组件 (阶段四将修改它以支持布局切换)

// 1. 引入刚才配置的路由和状态管理
import router from './router'
import pinia from './store'

// 2. 全局引入 Element Plus 及其默认样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 3. 全局引入 Element Plus 的所有图标 (由于是内部比赛项目，全局引入能大幅提高开发速度)
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// （预留）如果后续需要自定义全局样式，可以在此处引入
// import '@/assets/styles/index.scss
import '@/assets/styles/tailwind.css'

// 创建 Vue 应用实例
const app = createApp(App)

// 注册 Element Plus 所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 依次挂载插件
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 最终挂载到 index.html 中的 #app 节点
app.mount('#app')