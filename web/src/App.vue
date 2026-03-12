<template>
  <div class="flex h-screen bg-slate-900 text-slate-100 font-sans overflow-hidden">
    <nav class="w-16 bg-slate-950 border-r border-slate-800 flex flex-col items-center py-6 gap-8">
      <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-xl shadow-[0_0_15px_rgba(37,99,235,0.5)]">
        DRX
      </div>
      <router-link to="/" class="p-3 rounded-xl hover:bg-slate-800 transition" exact-active-class="bg-blue-600/20 text-blue-400">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
      </router-link>
      <router-link to="/search" class="p-3 rounded-xl hover:bg-slate-800 transition" active-class="bg-blue-600/20 text-blue-400">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      </router-link>
    </nav>

    <main class="flex-1 overflow-hidden relative">
      <router-view></router-view>
    </main>
  </div>
</template>