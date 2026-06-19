import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcssPostcss from '@tailwindcss/postcss'
import autoprefixer from 'autoprefixer'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    // 🎯 正确引入新版 v4.0 专用的 @tailwindcss/postcss 插件
    postcss: {
      plugins: [tailwindcssPostcss(), autoprefixer()],
    },
  },
})