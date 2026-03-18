import { createPinia } from 'pinia'

// 创建 Pinia 全局状态管理实例
const pinia = createPinia()

// 导出实例供 main.ts 挂载
export default pinia

/**
 * 注意事项：
 * 这里只是 Pinia 的初始化入口。
 * 具体的业务 Store (例如：管理当前面试进度的 useInterviewStore，或管理用户信息的 useUserStore)
 * 我们将在后续开发中，于 src/store/ 目录下单独建立文件。
 */