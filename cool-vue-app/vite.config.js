import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: '/cool-vue-app/',  // 깃허브 리포지토리 이름, 예: '/cool-vue-app/'
  plugins: [vue()]
})
