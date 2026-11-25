<template>
    <div class="cond-view">
        <div class="header top_bar">
            <RouterLink :to="SITE_BASE_URL + '/'" class="link_btn link_btn_header">
                < </RouterLink>
                    <h2 class="small_h2"> {{ state.settings?.data_name }} - GP-VAE Conditioning</h2>
        </div>
        <div v-if="state.error" class="cond-error">{{ state.error }}</div>
        <div v-else-if="!state.ready" class="cond-loading">
            <Loading />
            Preparing the GP-VAE conditioner (trains the model on first use, this can take a few minutes)...
        </div>
        <div v-else class="cond-main">
            <div class="cond-side">
                <h3>Conditions</h3>
                <p class="info">Brush an axis to condition on a range, double click an axis to fix a
                    single value. All other parameters are predicted by the GP-VAE with uncertainty.
                    Opacity between two axes = certainty of the prediction there.</p>
                <div v-if="!Object.keys(state.conditions).length" class="info">No conditions - showing
                    the unconditioned model.</div>
                <div v-for="(c, col) in state.conditions" :key="col" class="cond-row">
                    <div class="cond-name" :class="{ out: output_cols.includes(col as string) }">{{ col }}</div>
                    <label>value <input type="number" :step="stepFor(col as string)" :value="round(c.value)"
                            @change="e => setValue(col as string, +(e.target as HTMLInputElement).value, c.width)" /></label>
                    <label>± range <input type="number" min="0" :step="stepFor(col as string)" :value="round(c.width / 2)"
                            @change="e => setValue(col as string, c.value, 2 * Math.max(0, +(e.target as HTMLInputElement).value))" /></label>
                    <button class="small" @click="removeCondition(col as string)" title="remove">✕</button>
                </div>
                <button v-if="Object.keys(state.conditions).length" class="small" @click="clearAll">Clear all</button>
                <div class="cond-meta" v-if="state.result">
                    <div>mixture ESS: {{ state.result.ess.toFixed(1) }} / {{ state.bank_size }}</div>
                    <div v-if="state.result.temperature < 1">likelihood tempered (β = {{ state.result.temperature.toFixed(3) }})</div>
                    <div>{{ matching_rows }} / {{ state.data_rows.length }} sampled rows match the conditions</div>
                    <div v-if="state.loading_pred">updating...</div>
                </div>
                <h3>Presets</h3>
                <button class="small preset" @click="presetLowNox">Low NOx + high load</button>
                <button class="small preset" @click="presetHotAmbient">Hot ambient, fixed TIT</button>
            </div>
            <div class="cond-plots">
                <ConditionalPCP :columns="state.columns" :output_cols="output_cols" :domains="state.domains"
                    :data_rows="state.data_rows" :result="state.result" :conditions="state.conditions"
                    :hover_column="detail_column" @update-condition="onUpdateCondition" @hover="onHover" />
                <UncertaintyDetail :result="state.result" :column="detail_column" :columns="state.columns"
                    :output_cols="output_cols" :data_rows="state.data_rows" :conditions="state.conditions"
                    @hover="onHover" />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useRoute } from 'vue-router';
import * as d3 from 'd3';
import { Api, ConditionResult, ManagerSettings } from '../api/Api';
import { API_BASE_URL, SITE_BASE_URL } from '../config';
import Loading from '../components/ui/Loading.vue';
import ConditionalPCP from '../components/conditioning/ConditionalPCP.vue';
import UncertaintyDetail from '../components/conditioning/UncertaintyDetail.vue';
import { CondValue, relUncertainty } from '../components/conditioning/types';

const route = useRoute();
const api = new Api({ baseURL: API_BASE_URL });

const state = reactive({
    set_name: '' as string,
    settings: null as ManagerSettings | null,
    ready: false,
    error: '' as string,
    columns: [] as string[],
    domains: {} as Record<string, [number, number]>,
    data_rows: [] as number[][],
    conditions: {} as Record<string, CondValue>,
    result: null as ConditionResult | null,
    loading_pred: false,
    hover: null as string | null,
    last_hover: null as string | null,
    bank_size: 0,
});

const output_cols = computed(() => state.settings?.data_description.output_cols ?? []);

const detail_column = computed(() => {
    if (state.hover) return state.hover;
    if (state.last_hover) return state.last_hover;
    const r = state.result;
    if (!r) return null;
    // default: the most uncertain non conditioned column
    let best: string | null = null, best_v = -1;
    r.columns.forEach((c, i) => {
        if (state.conditions[c]) return;
        const v = relUncertainty(r, i);
        if (v > best_v) { best_v = v; best = c; }
    });
    return best;
});

const matching_rows = computed(() => {
    const conds = Object.entries(state.conditions);
    if (!conds.length) return state.data_rows.length;
    return state.data_rows.filter(row => conds.every(([col, c]) => {
        const i = state.columns.indexOf(col);
        const [lo, hi] = state.domains[col];
        return Math.abs(row[i] - c.value) <= Math.max(c.width / 2, (hi - lo) * 0.03);
    })).length;
});

function round(v: number) {
    return +d3.format('.5~g')(v);
}
function stepFor(col: string) {
    const [lo, hi] = state.domains[col] ?? [0, 1];
    return +d3.format('.1~g')((hi - lo) / 100);
}

async function init(set_name: string) {
    state.set_name = set_name;
    state.ready = false;
    state.error = '';
    state.conditions = {};
    state.result = null;
    try {
        state.settings = (await api.datasets.getSetDatasetsSetNameGet(set_name, { load: false })).data;
        const desc = state.settings.data_description;
        const status = (await api.datasets.getConditionerStatusDatasetsSetNameConditioningStatusGet(set_name)).data;
        if (!status.available) {
            state.error = status.reason || 'Conditioning not available for this dataset.';
            return;
        }
        state.bank_size = status.bank_size;
        state.columns = status.columns;
        state.domains = Object.fromEntries(state.columns.map(c => [c, [desc.min_values[c], desc.max_values[c]]]));
        const sample = (await api.datasets.getDataSampleDatasetsSetNameDataSampleGet(set_name, {
            max_samples: 400, include_outputs: true,
        })).data;
        // rows in conditioner column order (inputs then outputs)
        const order = [...desc.input_cols, ...desc.output_cols];
        state.data_rows = sample.inputs.map((inp, k) => {
            const full = [...inp, ...(sample.outputs[k] ?? [])];
            return state.columns.map(c => full[order.indexOf(c)]);
        });
        state.ready = true;
        await predict();
    } catch (error) {
        console.error('Error initialising conditioner:', error);
        state.error = `Error initialising conditioner: ${error}`;
    }
}

let request_id = 0;
let pending: ReturnType<typeof setTimeout> | null = null;
function schedulePredict() {
    if (pending) clearTimeout(pending);
    pending = setTimeout(predict, 60);
}
async function predict() {
    const id = ++request_id;
    state.loading_pred = true;
    try {
        const res = await api.datasets.predictConditionedDatasetsSetNameConditioningPredictPost(state.set_name, {
            conditions: Object.entries(state.conditions).map(([column, c]) => ({ column, value: c.value, width: c.width })),
            n_samples: 48,
            grid_points: 120,
        });
        if (id === request_id) state.result = res.data;
    } catch (error) {
        console.error('Error predicting:', error);
    } finally {
        if (id === request_id) state.loading_pred = false;
    }
}

function onUpdateCondition(column: string, value: CondValue | null) {
    if (value === null) {
        delete state.conditions[column];
    } else {
        state.conditions[column] = value;
    }
    schedulePredict();
}
function setValue(column: string, value: number, width: number) {
    state.conditions[column] = { value, width };
    schedulePredict();
}
function removeCondition(column: string) {
    delete state.conditions[column];
    schedulePredict();
}
function clearAll() {
    state.conditions = {};
    schedulePredict();
}
function onHover(column: string | null) {
    state.hover = column;
    if (column) state.last_hover = column;
}
function quantile(col: string, q: number) {
    const i = state.columns.indexOf(col);
    return d3.quantile(state.data_rows.map(r => r[i]).sort(d3.ascending), q) ?? 0;
}
function presetLowNox() {
    const nox = state.columns.find(c => c.toUpperCase() === 'NOX') ?? output_cols.value[output_cols.value.length - 1];
    const tey = state.columns.find(c => c === 'TEY') ?? state.columns[0];
    state.conditions = {
        [nox]: { value: quantile(nox, 0.15), width: quantile(nox, 0.25) - quantile(nox, 0.05) },
        [tey]: { value: quantile(tey, 0.85), width: quantile(tey, 0.95) - quantile(tey, 0.75) },
    };
    schedulePredict();
}
function presetHotAmbient() {
    const at = state.columns.find(c => c === 'AT') ?? state.columns[0];
    const tit = state.columns.find(c => c === 'TIT') ?? state.columns[1];
    state.conditions = {
        [at]: { value: quantile(at, 0.9), width: 0 },
        [tit]: { value: quantile(tit, 0.5), width: 0 },
    };
    schedulePredict();
}

watch(() => route.params.setname, (name) => { if (name) init(name as string); }, { immediate: true });
</script>

<style scoped>
.cond-main {
    display: flex;
    align-items: flex-start;
    gap: 10px;
}

.cond-side {
    width: 250px;
    flex-shrink: 0;
    padding: 0 10px 0 20px;
    font-size: 12px;
}

.cond-side h3 {
    font-size: 13px;
    margin: 10px 0 4px 0;
}

.cond-plots {
    flex-grow: 1;
    min-width: 0;
}

.info {
    font-size: 11px;
    color: #666;
}

.cond-row {
    border-left: 3px solid #d1495b;
    padding: 3px 6px;
    margin: 6px 0;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px;
}

.cond-row input {
    width: 76px;
    font-family: inherit;
    font-size: 11px;
}

.cond-row label {
    font-size: 10px;
    color: #555;
}

.cond-name {
    font-weight: 700;
    width: 100%;
}

.cond-name.out {
    color: #c76b00;
}

button.small {
    font-size: 11px;
    padding: 2px 6px;
}

button.preset {
    display: block;
    margin: 4px 0;
}

.cond-meta {
    margin-top: 10px;
    font-size: 10px;
    color: #555;
}

.cond-loading,
.cond-error {
    margin: 20px;
}

.cond-error {
    color: #b00020;
}

.cond-view {
    width: 100vw;
}

.link_btn_header {
    margin: 5px;
}
</style>
