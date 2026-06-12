import { createApp } from 'vue'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { reveal } from './directives/reveal'

const app = createApp(App)

// Register all Element Plus icons as global components.
for (const [name, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, component)
}

app.directive('reveal', reveal)
app.use(router)
app.mount('#app')
