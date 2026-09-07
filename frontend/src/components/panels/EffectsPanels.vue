<template>
    <div class="main_container">
        <div class="inter-panel">
            <h2>Output</h2>
            <select v-model="state.output_col" class="output_select">
                <option v-for="col in state.output_cols" :key="col" :value="col">{{ col }}</option>
            </select>

            <h2>Combination order</h2>
            <p class="info">Rank every order-n combination of input features by mean |Shapley
                interaction effect| (order 1 = plain SHAP, order 2 = exact pairwise interaction,
                order 3+ = Monte-Carlo Shapley interaction index; higher orders get expensive on
                datasets with many input columns).</p>
            <select v-model.number="state.order" class="order_select">
                <option v-for="n in orderOptions" :key="n" :value="n">order {{ n }}</option>
            </select>
            <button @click="fetchInteraction">
                Compute dependency
            </button>
        </div>
        <div class="divider"></div>
        <div class="stacked-panels">
            <div class="wide-panel">
                <h2>Beeswarm ({{ state.output_col || '...' }})</h2>
                <p class="info">First-order SHAP values across a sample of the dataset, one row per
                    input feature (top {{ MAX_DISPLAY }} by mean |SHAP|), colored by that feature's own
                    value.</p>
                <Loading v-if="state.loading_beeswarm" />
                <div class="chart-scroll" v-if="beeswarm_rows.length">
                    <BeeswarmChart :rows="beeswarm_rows" color_label="feature value" @hover-row="onHoverFeatures"
                        @hover-point="onHoverPoint" />
                </div>
            </div>
            <div class="panel-divider"></div>
            <div class="wide-panel">
                <h2>Dependency</h2>
                <p class="info" v-if="state.interaction">
                    Top {{ state.interaction.combinations.length }} order-{{ state.interaction.order }}
                    feature combinations by mean |Shapley interaction effect| on
                    <b>{{ state.output_col }}</b>.
                </p>
                <Loading v-if="state.loading_interaction" />
                <div class="chart-scroll" v-if="dependency_rows.length">
                    <BeeswarmChart :rows="dependency_rows" color_label="SHAP interaction value"
                        @hover-row="onHoverFeatures" @hover-point="onHoverPoint" />
                </div>
                <div v-else-if="!state.loading_interaction" class="info">
                    Pick a combination order and click "Compute dependency" to see the ranked
                    combinations here.
                </div>
            </div>
            <div class="panel-divider"></div>
            <div class="wide-panel">
                <h2>Scatterplot Matrix</h2>
                <p class="info">Pairwise relationships between input features across a sample of
                    the dataset. Hover a Beeswarm row to highlight its row here, or an order-2
                    Dependency row to highlight that pair's cell. Hovering a specific point also
                    highlights it in the magnified popover, if it's in the shown sample.</p>
                <ScatterplotMatrix :data_rep="(data_rep as DataRepository)" :highlight_row="state.hover_row"
                    :highlight_cell="state.hover_cell" :highlight_point_index="state.hover_point_index" />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { reactive, computed, watch, onMounted } from 'vue';
import { DataRepository } from '../../proc/data-store';
import { BeeswarmResult, InteractionResult } from '../../api/Api';
import BeeswarmChart from '../effects/BeeswarmChart.vue';
import ScatterplotMatrix from '../effects/ScatterplotMatrix.vue';
import { BeeswarmRow } from '../effects/types';
import Loading from '../ui/Loading.vue';

const { data_rep } = defineProps<{
    data_rep: DataRepository;
}>();

const MAX_ORDER = 6;
const MAX_DISPLAY = 15;

const state = reactive({
    loading_manager: false,
    output_col: '',
    input_cols: [] as string[],
    output_cols: [] as string[],
    order: 2,
    beeswarm: null as BeeswarmResult | null,
    loading_beeswarm: false,
    interaction: null as InteractionResult | null,
    loading_interaction: false,
    hover_row: null as string | null,
    hover_cell: null as [string, string] | null,
    hover_point_index: null as number | null,
});

function onHoverFeatures(features: string[] | null) {
    if (!features || features.length === 0) {
        state.hover_row = null;
        state.hover_cell = null;
    } else if (features.length === 1) {
        state.hover_row = features[0];
        state.hover_cell = null;
    } else if (features.length === 2) {
        state.hover_row = null;
        state.hover_cell = [features[0], features[1]];
    } else {
        // order 3+ combos don't map onto a 2D scatterplot matrix cell/row.
        state.hover_row = null;
        state.hover_cell = null;
    }
}

function onHoverPoint(index: number | null) {
    state.hover_point_index = index;
}

// order can't exceed the number of input columns; also mirror the backend's
// MAX_POOL_FOR_HIGH_ORDER=10 guard (order >= 3 requires a pool of at most 10 features) so the
// request doesn't just 400.
const orderOptions = computed(() => {
    const max_by_pool = state.input_cols.length || MAX_ORDER;
    const max_by_high_order = state.input_cols.length > 10 ? 2 : MAX_ORDER;
    const max_order = Math.max(1, Math.min(MAX_ORDER, max_by_pool, max_by_high_order));
    return Array.from({ length: max_order }, (_, i) => i + 1);
});

async function loadDescription() {
    state.loading_manager = true;
    try {
        if (!data_rep.manager_settings) {
            await data_rep.loadDescription();
        }
        const desc = data_rep.description || data_rep.manager_settings?.data_description;
        state.input_cols = desc?.input_cols || [];
        state.output_cols = desc?.output_cols || [];
        if (!state.output_col && state.output_cols.length) {
            state.output_col = state.output_cols[0];
        }
    } catch (error) {
        console.error('Error loading dataset description for effects panel:', error);
    } finally {
        state.loading_manager = false;
    }
}

async function fetchBeeswarm() {
    if (!state.output_col) return;
    state.loading_beeswarm = true;
    try {
        const res = await data_rep.client.datasets.getBeeswarmDatasetsSetNameEffectsBeeswarmPost(
            data_rep.set_name,
            { output_col: state.output_col, max_samples: 200 },
        );
        state.beeswarm = res.data;
    } catch (error) {
        console.error('Error fetching beeswarm:', error);
        state.beeswarm = null;
    } finally {
        state.loading_beeswarm = false;
    }
}

async function fetchInteraction() {
    if (!state.output_col) return;
    state.loading_interaction = true;
    try {
        const res = await data_rep.client.datasets.getInteractionDatasetsSetNameEffectsInteractionPost(
            data_rep.set_name,
            {
                output_col: state.output_col,
                features: [],
                order: state.order,
                top_k: MAX_DISPLAY,
                max_samples: 200,
                n_permutations: 64,
            },
        );
        state.interaction = res.data;
    } catch (error) {
        console.error('Error fetching interaction:', error);
        state.interaction = null;
    } finally {
        state.loading_interaction = false;
    }
}

onMounted(async () => {
    await loadDescription();
    await fetchBeeswarm();
});

watch(() => state.output_col, () => {
    fetchBeeswarm();
    if (state.interaction) fetchInteraction();
});

watch(orderOptions, (options) => {
    if (!options.includes(state.order)) {
        state.order = options[options.length - 1] ?? 1;
    }
});

const beeswarm_rows = computed<BeeswarmRow[]>(() => {
    const bs = state.beeswarm;
    if (!bs) return [];
    const ranked = bs.features
        .map(f => ({
            key: f,
            label: f,
            values: bs.shap_values[f] || [],
            color_values: bs.feature_values[f] || [],
            indices: bs.indices,
            features: [f],
            mean_abs: (bs.shap_values[f] || []).reduce((s, v) => s + Math.abs(v), 0) / Math.max(1, (bs.shap_values[f] || []).length),
        }))
        .sort((a, b) => b.mean_abs - a.mean_abs)
        .slice(0, MAX_DISPLAY);
    return ranked.reverse();
});

const dependency_rows = computed<BeeswarmRow[]>(() => {
    const interaction = state.interaction;
    if (!interaction) return [];
    // Backend already ranks combinations descending by mean |effect|; reverse so the strongest
    // ends up at the top of the chart, matching beeswarm_rows' convention.
    return interaction.combinations
        .map(combo => ({
            key: combo.features.join('-'),
            label: combo.features.join(' & '),
            values: combo.values,
            indices: interaction.indices,
            features: combo.features,
            kind: 'swarm' as const,
        }))
        .reverse();
});
</script>

<style scoped>
.main_container {
    width: 100%;
    display: flex;
    justify-content: start;
    align-items: flex-start;
    font-family: 'Roboto Mono', monospace;
}

.divider {
    min-height: 93vh;
    width: 1px;
    background-color: #ccc;
}

.inter-panel {
    width: 24.5vw;
    min-width: 24vw;
    height: 93vh;
    display: flex;
    flex-direction: column;
    justify-items: start;
    align-items: center;
    overflow-y: auto;
    margin: 0px;
}

.stacked-panels {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    min-width: 0;
}

.wide-panel {
    width: 70vw;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.panel-divider {
    width: 90%;
    height: 1px;
    background-color: #ccc;
    margin: 16px 0;
}

.info {
    font-size: 11px;
    color: #666;
    text-align: center;
    padding: 0 8px;
}

.output_select,
.order_select {
    margin-bottom: 8px;
}

.chart-scroll {
    width: 100%;
    max-height: 42vh;
    overflow-y: auto;
}
</style>
