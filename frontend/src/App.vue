<script setup>
import { ref } from "vue";
import DevicesView from "./views/DevicesView.vue";
import MonitorView from "./views/MonitorView.vue";

const tab = ref("monitor");
const selectedDeviceId = ref(null);

function openMonitor(deviceId) {
  selectedDeviceId.value = deviceId;
  tab.value = "monitor";
}
</script>

<template>
  <div style="max-width: 1100px; margin: 0 auto; padding: 20px">
    <header style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 18px">
      <h1 style="font-size: 24px">INSIGHT</h1>
      <nav style="display: flex; gap: 4px">
        <button
          class="btn"
          :class="{ primary: tab === 'monitor' }"
          @click="tab = 'monitor'"
        >
          Monitor
        </button>
        <button
          class="btn"
          :class="{ primary: tab === 'devices' }"
          @click="tab = 'devices'"
        >
          Devices
        </button>
      </nav>
    </header>

    <MonitorView v-if="tab === 'monitor'" v-model:deviceId="selectedDeviceId" />
    <DevicesView v-else @monitor="openMonitor" />
  </div>
</template>
