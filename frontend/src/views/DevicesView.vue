<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../api";

const emit = defineEmits(["monitor"]);

const devices = ref([]);
const loading = ref(false);
const error = ref("");
const testResults = reactive({}); // device_id -> { ok, detail, at }

const form = reactive({
  id: null,
  name: "",
  host: "",
  port: 10001,
  address: "FF",
  poll_interval_s: 5,
  enabled: true,
});
const formOpen = ref(false);

async function refresh() {
  loading.value = true;
  error.value = "";
  try {
    devices.value = await api.listDevices();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function openCreateForm() {
  Object.assign(form, { id: null, name: "", host: "", port: 10001, address: "FF", poll_interval_s: 5, enabled: true });
  formOpen.value = true;
}

function openEditForm(device) {
  Object.assign(form, device);
  formOpen.value = true;
}

async function saveForm() {
  const payload = {
    name: form.name,
    host: form.host,
    port: Number(form.port),
    address: form.address.toUpperCase(),
    poll_interval_s: Number(form.poll_interval_s),
    enabled: form.enabled,
  };
  try {
    if (form.id) {
      await api.updateDevice(form.id, payload);
    } else {
      await api.createDevice(payload);
    }
    formOpen.value = false;
    await refresh();
  } catch (e) {
    error.value = e.message;
  }
}

async function removeDevice(device) {
  if (!confirm(`Eliminare "${device.name}"?`)) return;
  await api.deleteDevice(device.id);
  await refresh();
}

async function testDevice(device) {
  testResults[device.id] = { pending: true };
  try {
    const result = await api.testConnection(device.id);
    testResults[device.id] = { ...result, at: new Date().toLocaleTimeString() };
  } catch (e) {
    testResults[device.id] = { ok: false, error: e.message, at: new Date().toLocaleTimeString() };
  }
}

onMounted(refresh);
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
      <h2>Devices</h2>
      <button class="btn primary" @click="openCreateForm">+ Add device</button>
    </div>

    <p v-if="error" style="color: var(--danger)">{{ error }}</p>

    <div v-if="formOpen" class="card" style="padding: 16px; margin-bottom: 16px">
      <h3 style="margin-bottom: 12px">{{ form.id ? "Edit device" : "New device" }}</h3>
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px">
        <div class="field">
          <label>Name</label>
          <input v-model="form.name" placeholder="MD01" />
        </div>
        <div class="field">
          <label>Host / IP</label>
          <input v-model="form.host" placeholder="192.168.1.125" />
        </div>
        <div class="field">
          <label>Port</label>
          <input v-model="form.port" type="number" />
        </div>
        <div class="field">
          <label>Address (hex, "FF"=default)</label>
          <input v-model="form.address" maxlength="2" />
        </div>
        <div class="field">
          <label>Poll interval (s)</label>
          <input v-model="form.poll_interval_s" type="number" min="1" />
        </div>
        <div class="field">
          <label>Enabled</label>
          <input v-model="form.enabled" type="checkbox" style="width: 18px; height: 18px; align-self: flex-start" />
        </div>
      </div>
      <div style="margin-top: 14px; display: flex; gap: 8px">
        <button class="btn primary" @click="saveForm">Save</button>
        <button class="btn" @click="formOpen = false">Cancel</button>
      </div>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Host</th>
            <th>Addr</th>
            <th>Poll</th>
            <th>Status</th>
            <th>Connection test</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in devices" :key="d.id">
            <td>{{ d.name }}</td>
            <td class="mono">{{ d.host }}:{{ d.port }}</td>
            <td class="mono">{{ d.address }}</td>
            <td>{{ d.poll_interval_s }}s</td>
            <td>
              <span class="badge" :class="d.enabled ? 'ok' : 'muted'">{{ d.enabled ? "enabled" : "disabled" }}</span>
            </td>
            <td>
              <button class="btn" @click="testDevice(d)">Test</button>
              <span v-if="testResults[d.id]?.pending"> testing…</span>
              <span v-else-if="testResults[d.id]" style="margin-left: 8px">
                <span class="badge" :class="testResults[d.id].ok ? 'ok' : 'danger'">
                  {{ testResults[d.id].ok ? "OK" : "ERROR" }}
                </span>
                <span v-if="testResults[d.id].ok" class="mono" style="margin-left: 6px; font-size: 12px; color: var(--muted)">
                  {{ testResults[d.id].device_info.device_type_name }}
                </span>
                <span v-else style="margin-left: 6px; font-size: 12px; color: var(--danger)">
                  {{ testResults[d.id].error }}
                </span>
              </span>
            </td>
            <td style="white-space: nowrap">
              <button class="btn" @click="emit('monitor', d.id)">Monitor →</button>
              <button class="btn" @click="openEditForm(d)">Edit</button>
              <button class="btn danger" @click="removeDevice(d)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && devices.length === 0">
            <td colspan="7" style="text-align: center; color: var(--muted); padding: 24px">
              Nessun dispositivo configurato — usa "+ Add device".
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
