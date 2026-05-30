<template>
  <div class="min-h-screen flex transition-colors duration-200" :style="{ background: 'var(--bg-base)' }">
    <!-- Background decoration (dark only) -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden dark:block hidden">
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      <div class="absolute bottom-1/4 right-1/4 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl" />
    </div>

    <AppSidebar />

    <div class="flex-1 flex flex-col min-w-0 ml-64">
      <AppHeader />
      <main class="flex-1 p-6 overflow-auto animate-fade-in">
        <slot />
      </main>
    </div>

    <AiChat />
    <AppToast />
  </div>
</template>

<script setup lang="ts">
</script>
