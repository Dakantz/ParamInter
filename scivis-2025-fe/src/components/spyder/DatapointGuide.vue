<template>
    <div class="datapoint-guide">
        <h2>Adapt Mixture</h2>
        <h3>Selection</h3>
        <SpyderChart v-if="state.dp" :dimensions="state.input_types" v-model="state.dp.inputs" :editable="false"
            :sensitivities="state.sensitivities_for_hover" />
        <h3>Target Output Values</h3>
        <div class="editable-outs" v-if="state.dp">
            <div v-for="(types, idx) of state.visible_types" :key="idx">
                <Overview v-model="state.dp" :types="types" :data_rep="data_rep" :cat_name="idx"
                    @hover="showSensitivity($event)" />
            </div>
        </div>
        <div class="search-results" v-if="state.search_results.length > 0">
            <h3>Possible Input Targets</h3>
            <div v-for="(result, idx) in state.search_results" :key="idx" class="search-result-item"
                @mouseenter="emit('preview', result.index || -1)" @click.capture="emit('select', result.index || -1)">
                <SpyderChart :dimensions="state.input_types" v-model="result.inputs" :editable="false" />
            </div>
        </div>
        <div v-if="state.loading">
            <v-progress-linear color="primary" indeterminate></v-progress-linear>
            <span>Loading...</span>
        </div>

    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, defineProps, defineModel, watch, onMounted, useTemplateRef } from 'vue';
import * as d3 from 'd3';
import { DataRepository, LoadedDataPoints } from '../../proc/types';
import SpyderChart from './SpyderChart.vue';
import { DataPoint } from '../../api/Api';
import Overview from './single/Overview.vue';
import { PlotSelection } from '../types';

const selection = defineModel<PlotSelection>();
const emit = defineEmits<{
    (e: 'preview', idx: number): void;
    (e: 'select', idx: number): void;
}>();
const { data_rep, selected_dp } = defineProps({
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    },
    selected_dp: {
        type: Number,
        default: -1
    }
});

const state = reactive({
    dp: null as DataPoint | null,
    loading: false,
    sensitivities_for_hover: [] as number[],
    search_results: [] as DataPoint[],
    visible_types: {} as Record<string, string[]>,
    input_types: [] as string[],
});

watch(() => data_rep.all_types, (newTypes) => {
    console.log("New types:", newTypes);
    if (Object.keys(newTypes).length === 0) {
        console.warn("No types available in data repository.");
        return;
    }
    state.input_types = newTypes[Object.keys(newTypes)[0]];
    state.visible_types = Object.fromEntries(
        Object.entries(newTypes).filter((kv, i) => i !== 0 && i < Object.entries(newTypes).length - 1).map(([key, value]) => [key, value])
    );

}, { immediate: true });
watch(() => selected_dp, (newIdx) => {
    if (newIdx >= 0) {
        data_rep.dps.getDP(newIdx).then((dp) => {
            state.dp = dp;
            console.log("Selected Data Point:", dp);
        }).catch((error) => {
            console.error("Error fetching data point:", error);
        });
    }
}, { immediate: true });
watch(() => state.dp, (dp) => {
    if (dp) {
        state.search_results = [];
        state.loading = true;
        data_rep.client.dataPoint.dataPointSuggestionsDataPointSuggestionsPost({
            values: dp.outputs,
            base_index: dp.index || -1,
            k: 4
        }).then((suggestions) => {
            state.loading = false;
            // console.log("Suggestions results:", suggestions);
            state.search_results = suggestions.data;
        }).catch((error) => {
            state.loading = false;
            console.error("Error fetching suggested data points:", error);
        });
    }
}, { immediate: true, deep: true });

function showSensitivity(out_col: string) {
    if (state.dp) {
        data_rep.client.dataPoint.explanationsForDpDataPointExplanationsIdxPost(
            state.dp.index || -1, {
            for_outputs: [out_col],
            resolution: 16
        }).then((result) => {
            // console.log("Sensitivity Analysis Result:", result);
            state.sensitivities_for_hover = result.data[0].sensitivity_scores;
        }).catch((error) => {
            console.error("Error fetching sensitivity analysis:", error);
        });
    }
}
</script>

<style scoped>
.datapoint-guide {
    min-height: 100vh;
    max-height: 100vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    justify-items: center;
    align-items: center;
    padding: 5px;
}



.search-result-item:hover {
    background-color: #e0e0e0;
}

.editable-outs {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    width: 100%;
    align-items: start;
    justify-content: start;
    margin: 4px;
}


.search-results {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 80%;
}

.search-result-item {
    width: 100%;
    display: flex;
    justify-content: center;
    margin: 5px 0;
    padding: 5px;
    border: 1px solid #ccc;
    background-color: #f9f9f9;
    cursor: grab;
}

.search-result-item:hover {
    background-color: #e0e0e0;
}
</style>