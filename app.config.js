export default {
  expo: {
    name: 'Project Bolt',
    slug: 'project-bolt',
    version: '1.0.0',
    orientation: 'portrait',
    icon: './assets/images/icon.png',
    userInterfaceStyle: 'automatic',
    splash: {
      image: './assets/images/splash.png',
      resizeMode: 'contain',
      backgroundColor: '#ffffff'
    },
    assetBundlePatterns: [
      '**/*'
    ],
    ios: {
      supportsTablet: true
    },
    android: {
      adaptiveIcon: {
        foregroundImage: './assets/images/adaptive-icon.png',
        backgroundColor: '#ffffff'
      }
    },
    web: {
      favicon: './assets/images/favicon.png'
    },
    extra: {
      supabaseUrl: 'https://vsolruwkakcgvzxawnvy.supabase.co',
      supabaseAnonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZzb2xydXdrYWtjZ3Z6eGF3bnZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NDQ5NzMsImV4cCI6MjA2MTQyMDk3M30.vHT5yxjjrIUf_FLLp6CtwyB3dSyKlHbAhND7zqazIZ8'
    }
  }
}; 