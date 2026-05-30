<template>
  <aside class="fixed left-0 top-0 h-full w-64 flex flex-col backdrop-blur-sm z-40 transition-colors duration-200"
    :style="{ background: 'var(--bg-sidebar)', borderRight: '1px solid var(--border)' }">

    <!-- Logo -->
    <div class="px-5 py-5" :style="{ borderBottom: '1px solid var(--border)' }">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-xl bg-primary/20 border border-primary/40 flex items-center justify-center glow-cyan">
          <span class="text-primary font-bold text-sm">IO</span>
        </div>
        <div>
          <p class="font-bold text-sm tracking-wide" :style="{ color: 'var(--text-primary)' }">IntelliOLT</p>
          <p class="text-[10px] font-mono" :style="{ color: 'var(--text-muted)' }">Network Intelligence</p>
        </div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-3 py-4 overflow-y-auto space-y-1">
      <p class="text-[10px] font-semibold uppercase tracking-widest px-3 mb-2" :style="{ color: 'var(--text-muted)' }">Overview</p>

      <NuxtLink v-for="item in mainNav" :key="item.to" :to="item.to" custom v-slot="{ isActive, navigate }">
        <div @click="navigate" :class="['nav-item', isActive ? 'nav-item-active' : '']">
          <component :is="item.icon" :size="16" :class="isActive ? 'text-primary' : ''" :style="!isActive ? { color: 'var(--text-muted)' } : {}" />
          <span>{{ item.label }}</span>
          <span v-if="item.badge" class="ml-auto text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-400">
            {{ item.badge }}
          </span>
        </div>
      </NuxtLink>

      <p class="text-[10px] font-semibold uppercase tracking-widest px-3 mt-5 mb-2" :style="{ color: 'var(--text-muted)' }">Network</p>

      <NuxtLink v-for="item in networkNav" :key="item.to" :to="item.to" custom v-slot="{ isActive, navigate }">
        <div @click="navigate" :class="['nav-item', isActive ? 'nav-item-active' : '']">
          <component :is="item.icon" :size="16" :class="isActive ? 'text-primary' : ''" :style="!isActive ? { color: 'var(--text-muted)' } : {}" />
          <span>{{ item.label }}</span>
        </div>
      </NuxtLink>

      <p class="text-[10px] font-semibold uppercase tracking-widest px-3 mt-5 mb-2" :style="{ color: 'var(--text-muted)' }">Intelligence</p>

      <NuxtLink v-for="item in aiNav" :key="item.to" :to="item.to" custom v-slot="{ isActive, navigate }">
        <div @click="navigate" :class="['nav-item', isActive ? 'nav-item-active' : '']">
          <component :is="item.icon" :size="16" :class="isActive ? 'text-primary' : ''" :style="!isActive ? { color: 'var(--text-muted)' } : {}" />
          <span>{{ item.label }}</span>
        </div>
      </NuxtLink>
    </nav>

    <!-- User footer -->
    <div class="px-3 py-4" :style="{ borderTop: '1px solid var(--border)' }">
      <div class="flex items-center gap-3 px-3 py-2">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary/40 to-indigo-500/40 flex items-center justify-center text-xs font-bold text-white shrink-0">
          AD
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-semibold truncate" :style="{ color: 'var(--text-primary)' }">Admin User</p>
          <p class="text-[10px] truncate" :style="{ color: 'var(--text-muted)' }">admin@intelliolt.tn</p>
        </div>
        <LogOut :size="14" class="hover:text-red-400 cursor-pointer transition-colors shrink-0" :style="{ color: 'var(--text-muted)' }" />
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import {
  LayoutDashboard, Router, Bell, BrainCircuit,
  BarChart3, FileText, Activity, ShieldAlert, LogOut, Radio, Network
} from 'lucide-vue-next'

interface NavItem { to: string; label: string; icon: any; badge?: string | null }

const mainNav: NavItem[] = [
  { to: '/',          label: 'Dashboard',  icon: LayoutDashboard },
  { to: '/alerts',    label: 'Alerts',     icon: Bell,           badge: null },
  { to: '/analytics', label: 'Analytics',  icon: BarChart3 },
  { to: '/reports',   label: 'Reports',    icon: FileText }
]

const networkNav: NavItem[] = [
  { to: '/topology', label: 'Topology',     icon: Network },
  { to: '/olts',     label: 'OLT Devices',  icon: Router },
  { to: '/bfd',      label: 'BFD Sessions', icon: Activity },
  { to: '/snmp',     label: 'SNMP Metrics', icon: Radio }
]

const aiNav: NavItem[] = [
  { to: '/anomalies', label: 'Anomalies', icon: ShieldAlert },
  { to: '/ai-models', label: 'ML Models', icon: BrainCircuit }
]
</script>
