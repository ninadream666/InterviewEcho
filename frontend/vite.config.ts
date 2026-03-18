import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // 配置 @ 别名指向 src 目录，方便后续深层级目录引入文件
      '@': path.resolve(__dirname, 'src') 
    }
  },
  server: {
    port: 5173, // 前端默认开发端口
    proxy: {
      // 配置反向代理，解决开发环境请求后端 API 的跨域问题 (CORS)
      // 匹配所有以 /api 开头的请求，转发到后端成员B的 FastAPI 服务
      '/api': {
        target: 'http://localhost:8000', // 假设后端运行在本地 8000 端口，可随时修改
        changeOrigin: true, // 是否改变请求头中的 Origin
        // rewrite: (path) => path.replace(/^\/api/, '') // 如果后端接口不带 /api 前缀，可以开启此行抹去前缀
      }
    }
  }
})