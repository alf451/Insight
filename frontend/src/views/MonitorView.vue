<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { api } from "../api";

const props = defineProps({ deviceId: { type: Number, default: null } });
const emit = defineEmits(["update:deviceId"]);

const devices = ref([]);
const connected = ref(false);
const lastUpdated = ref(null);
const lastError = ref(null);
const data = ref(null); // last read_device_data() payload
const readings = ref([]);
const logbook = ref([]);

const sensitivityForm = reactive({ product_number: null, sensitivity: null, confirm: false });
const writeBusy = ref(false);
const writeResult = ref(null);

let ws = null;
let reconnectTimer = null;

const STATE_BADGE = {
  IDLE: "muted",
  TEST: "warn",
  LEARNING: "warn",
  ERROR: "danger",
  WARNING: "warn",
  SETUP: "muted",
};

const stateBadgeClass = computed(() => {
  const name = data.value?.system_status?.main_state_name;
  return STATE_BADGE[name] || "muted";
});

async function loadDevices() {
  devices.value = await api.listDevices();
  if (!props.deviceId && devices.value.length > 0) {
    emit("update:deviceId", devices.value[0].id);
  }
}

async function loadSnapshot(id) {
  const latest = await api.getLatest(id);
  connected.value = latest.connected;
  lastUpdated.value = latest.last_updated;
  lastError.value = latest.last_error;
  if (latest.data) {
    data.value = latest.data;
    sensitivityForm.product_number = latest.data.current_product_number;
    sensitivityForm.sensitivity = latest.data.product_data.sensitivity;
  }
  readings.value = await api.getReadings(id, 30);
  logbook.value = await api.getLogbook(id, 20);
}

function connectWs(id) {
  disconnectWs();
  ws = new WebSocket(api.wsUrl(id));
  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    data.value = msg.data;
    connected.value = true;
    lastError.value = null;
    lastUpdated.value = new Date().toISOString();
  };
  ws.onclose = () => {
    reconnectTimer = setTimeout(() => {
      if (props.deviceId === id) connectWs(id);
    }, 3000);
  };
}

function disconnectWs() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  if (ws) {
    ws.onclose = null;
    ws.close();
    ws = null;
  }
}

watch(
  () => props.deviceId,
  async (id) => {
    data.value = null;
    readings.value = [];
    logbook.value = [];
    if (id == null) return;
    await loadSnapshot(id);
    connectWs(id);
  },
  { immediate: true }
);

onMounted(loadDevices);
onBeforeUnmount(disconnectWs);

async function refreshHistory() {
  if (props.deviceId == null) return;
  readings.value = await api.getReadings(props.deviceId, 30);
  logbook.value = await api.getLogbook(props.deviceId, 20);
}

async function syncSystemTime() {
  writeBusy.value = true;
  writeResult.value = null;
  try {
    const r = await api.writeSystemTime(props.deviceId);
    writeResult.value = { ok: r.ok, message: "Orologio del dispositivo sincronizzato." };
  } catch (e) {
    writeResult.value = { ok: false, message: e.message };
  } finally {
    writeBusy.value = false;
  }
}

async function submitSensitivity() {
  if (!sensitivityForm.confirm) return;
  writeBusy.value = true;
  writeResult.value = null;
  try {
    const r = await api.writeSensitivity(props.deviceId, {
      product_number: Number(sensitivityForm.product_number),
      sensitivity: Number(sensitivityForm.sensitivity),
      confirm: true,
    });
    writeResult.value = {
      ok: r.ok,
      message: `Sensibilità aggiornata a ${r.readback.sensitivity}% (prodotto ${sensitivityForm.product_number}).`,
    };
    sensitivityForm.confirm = false;
    await refreshHistory();
  } catch (e) {
    writeResult.value = { ok: false, message: e.message };
  } finally {
    writeBusy.value = false;
  }
}
</script>

<template>
  <div>
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px">
      <h2>Monitor</h2>
      <select
        :value="deviceId"
        @change="emit('update:deviceId', Number($event.target.value))"
        style="padding: 6px 8px; border: 1px solid var(--line); border-radius: 6px"
      >
        <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
      <span v-if="deviceId != null" class="badge" :class="connected ? 'ok' : 'danger'">
        {{ connected ? "ONLINE" : "OFFLINE" }}
      </span>
      <span v-if="lastUpdated" style="font-size: 12px; color: var(--muted)" class="mono">
        last update: {{ new Date(lastUpdated).toLocaleTimeString() }}
      </span>
    </div>

    <p v-if="devices.length === 0" style="color: var(--muted)">
      Nessun dispositivo configurato. Vai su "Devices" per aggiungerne uno.
    </p>
    <p v-else-if="lastError" style="color: var(--danger)">{{ lastError }}</p>

    <div v-if="data" style="display: grid; grid-template-columns: 1.3fr 1fr; gap: 16px">
      <div style="display: flex; flex-direction: column; gap: 16px">
        <div class="card" style="padding: 16px">
          <h3 style="margin-bottom: 10px">System status</h3>
          <div style="display: flex; gap: 20px; align-items: baseline; flex-wrap: wrap">
            <span class="badge" :class="stateBadgeClass" style="font-size: 13px; padding: 4px 12px">
              {{ data.system_status.main_state_name }}
            </span>
            <span class="mono">metal signal: <b>{{ data.system_status.metal_signal }}</b></span>
            <span class="mono">product: <b>{{ data.current_product_number }}</b></span>
          </div>
          <div v-if="data.system_status.active_flags.length" style="margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap">
            <span v-for="f in data.system_status.active_flags" :key="f" class="badge muted">{{ f }}</span>
          </div>
          <div v-if="data.system_status.active_errors.length" style="margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap">
            <span v-for="e in data.system_status.active_errors" :key="e" class="badge danger">{{ e }}</span>
          </div>
        </div>

        <div class="card" style="padding: 16px">
          <h3 style="margin-bottom: 10px">Product data</h3>
          <table>
            <tbody>
              <tr><td>Sensitivity</td><td class="mono"><b>{{ data.product_data.sensitivity }}%</b></td></tr>
              <tr><td>Angle</td><td class="mono">{{ (data.product_data.product_angle / 10).toFixed(1) }}°</td></tr>
              <tr><td>Gain</td><td class="mono">{{ data.product_data.gain }}</td></tr>
              <tr><td>Threshold</td><td class="mono">{{ data.product_data.threshold }}</td></tr>
              <tr><td>Conveyor speed</td><td class="mono">{{ data.product_data.conveyor_speed }} mm/s</td></tr>
            </tbody>
          </table>
        </div>

        <div class="card" style="padding: 16px">
          <h3 style="margin-bottom: 10px">Counters</h3>
          <table>
            <tbody>
              <tr><td>Metal detections (global)</td><td class="mono">{{ data.global_counters.metal_counter }}</td></tr>
              <tr><td>Errors (global)</td><td class="mono">{{ data.global_counters.error_counter }}</td></tr>
              <tr><td>Logbook</td><td class="mono">{{ data.logbook_count }} / {{ data.logbook_max }}</td></tr>
            </tbody>
          </table>
        </div>

        <div class="card" style="padding: 16px">
          <h3 style="margin-bottom: 10px">Logbook (archiviato)</h3>
          <table>
            <thead>
              <tr><th>Timestamp</th><th>Evento</th><th>Dettagli</th></tr>
            </thead>
            <tbody>
              <tr v-for="e in logbook" :key="e.absolute_number">
                <td class="mono">{{ e.timestamp }}</td>
                <td>{{ e.entry_code_description }}</td>
                <td class="mono" style="font-size: 12px; color: var(--muted)">
                  {{ Object.entries(e.decoded).map(([k, v]) => `${k}=${v}`).join(", ") }}
                </td>
              </tr>
              <tr v-if="logbook.length === 0"><td colspan="3" style="color: var(--muted)">Nessuna voce archiviata ancora.</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 16px">
        <div class="card" style="padding: 16px">
          <h3 style="margin-bottom: 4px">Scrittura verso il dispositivo</h3>
          <p style="font-size: 12px; color: var(--muted); margin-top: 4px">
            Esempi di comando WRITE (spec SSTProt "TT"/"PD") — vedi
            <code>docs/SSTPROT.md</code> prima di usarli su un dispositivo reale.
          </p>

          <div style="margin-top: 12px">
            <button class="btn" :disabled="writeBusy" @click="syncSystemTime">Sync system time</button>
          </div>

          <div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--line)">
            <div style="font-size: 12px; color: var(--muted); margin-bottom: 8px">Update sensitivity (product data write)</div>
            <div style="display: flex; gap: 8px; align-items: end; flex-wrap: wrap">
              <div class="field">
                <label>Product #</label>
                <input v-model="sensitivityForm.product_number" type="number" style="width: 80px" />
              </div>
              <div class="field">
                <label>Sensitivity (1-100)</label>
                <input v-model="sensitivityForm.sensitivity" type="number" min="1" max="100" style="width: 80px" />
              </div>
            </div>
            <label style="display: flex; align-items: center; gap: 6px; margin-top: 10px; font-size: 12.5px">
              <input v-model="sensitivityForm.confirm" type="checkbox" />
              Confermo: sto scrivendo sul dispositivo reale, non testato in produzione — vedi docs/SSTPROT.md
            </label>
            <button
              class="btn"
              :class="{ primary: sensitivityForm.confirm }"
              :disabled="!sensitivityForm.confirm || writeBusy"
              style="margin-top: 10px"
              @click="submitSensitivity"
            >
              Write sensitivity
            </button>
          </div>

          <p v-if="writeResult" style="margin-top: 12px; font-size: 13px" :style="{ color: writeResult.ok ? 'var(--ok)' : 'var(--danger)' }">
            {{ writeResult.message }}
          </p>
        </div>

        <div class="card" style="padding: 16px">
          <h3 style="margin-bottom: 10px">Storico letture (archiviate)</h3>
          <table>
            <thead><tr><th>Ora</th><th>Sens.</th><th>Stato</th></tr></thead>
            <tbody>
              <tr v-for="r in readings" :key="r.timestamp">
                <td class="mono" style="font-size: 12px">{{ new Date(r.timestamp).toLocaleTimeString() }}</td>
                <td class="mono">{{ r.sensitivity }}%</td>
                <td>{{ r.main_state_name }}</td>
              </tr>
              <tr v-if="readings.length === 0"><td colspan="3" style="color: var(--muted)">Nessuna lettura archiviata ancora.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
