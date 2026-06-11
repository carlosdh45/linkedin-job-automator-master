export default defineNuxtConfig({
  devtools: { enabled: false },
  modules: ['@nuxtjs/tailwindcss'],
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    },
  },
  typescript: {
    strict: true,
    shim: false,
  },
  app: {
    head: {
      title: 'DobryBot — CorosDev',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'DobryBot internal dashboard — human-in-the-loop opportunity assistant. Never sends or applies automatically.' },
      ],
    },
  },
})
