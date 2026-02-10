<template>
    <div class="datapoint-guide" :class="{ 'non_active': !state.dp }">
        <h2>Build Minimizer</h2>
        <h3>Start Point</h3>
        <SpyderChart v-if="state.dp" :rep="data_rep" v-model="state.dp.inputs" :editable="false"
            :sensitivities="state.sensitivities_for_hover" :uncertainties="state.dp.uncertainties" />
        <h3>Linear Objective</h3>
        <h4 class="info">Drag to adjust</h4>
        <div class="linear-objectives">
            <div v-for="(target, idx) in state.linear_combination" :key="idx" @mouseenter="showSensitivity(target.name)"
                class="linear-objective">
                <SingleAdj v-model="target.val" :out_name="target.name" :data_rep="data_rep"
                    @hover="showSensitivity(target.name)" @remove="removeTarget(target.name)" />
            </div>
            min
            <span v-for="(target, idx) in state.linear_combination" :key="idx">
                {{ target.weight.toFixed(2) }} ({{ target.name }} - {{ target.val.toFixed(2) }}) <span
                    v-if="idx < state.linear_combination.length - 1"> + <br /> </span>
            </span>
        </div>
        <h3>Choose Variables</h3>
        <h4 class="info">Click to add, hover variables to see sensitivity!</h4>
        <div class="editable-outs" v-if="state.dp">
            <!-- <div class="">

                <input type="text"  class/>
            </div> -->
            <div v-for="(types, idx) of state.visible_types" :key="idx">
                <Overview v-model="state.dp" :types="types" :data_rep="data_rep" :cat_name="idx"
                    @hover="showSensitivity($event)" @add="addLinearTarget($event)" />
            </div>
        </div>

        <!-- <h3>Possible Input Targets</h3>
        <div class="search-results" v-if="state.search_results.length > 0">
            <div v-for="(result, idx) in state.search_results" :key="idx" class="search-result-item"
                @mouseenter="emit('preview', result.index || -1)" @click.capture="emit('select', result.index || -1)">
                <SpyderChart :rep="data_rep" v-model="result.inputs" :editable="false" />
            </div>
        </div> -->
        <div v-if="state.loading">
            \ <span>Loading...</span>
        </div>

    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef } from 'vue';
import * as d3 from 'd3';
import { DataRepository, LoadedDataPoints } from '../../proc/data-store';
import SpyderChart from '../spyder/SpyderChart.vue';
import { DataPoint, LinearTarget } from '../../api/Api';
import Overview from '../adjuster/Overview.vue';
import { PlotSelection } from '../types';
import SingleAdj from '../adjuster/SingleAdj.vue';

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

    linear_combination: [] as LinearTarget[],

});

watch(() => data_rep.all_types, (newTypes) => {
    if (newTypes) {
        state.visible_types = data_rep.getVisisbleTypes();
    }
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
        data_rep.client.datasets.dataPointSuggestionsDatasetsSetNameDataPointSuggestionsPost(data_rep.set_name, {
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
        data_rep.client.datasets.explanationsForDpDatasetsSetNameDataPointExplanationsIdxPost(state.dp.index || -1, data_rep.set_name,
            {
                for_outputs: [out_col],
                resolution: 16
            }).then((result) => {
                // console.log("Sensitivity Analysis Result:", result);
                if (result.data[0]) {
                    state.sensitivities_for_hover = result.data[0].sensitivity_scores;
                }
            }).catch((error) => {
                console.error("Error fetching sensitivity analysis:", error);
            });
    }
}

function addLinearTarget(name: string) {
    console.log("Adding linear target:", name);
    if (state.dp) {
        let idx = data_rep.getTypeIndex(name);
        let value: number;
        if (idx >= state.dp.inputs.length) {
            value = state.dp.outputs[idx - state.dp.inputs.length];
        } else {
            value = state.dp.inputs[idx];
        }
        state.linear_combination.push({
            name: name,
            val: value,
            weight: 1.0
        });
    }
}
function removeTarget(name: string) {
    console.log("Removing linear target:", name);
    state.linear_combination = state.linear_combination.filter((t) => t.name !== name);
}
watch(() => state.linear_combination, (newComb) => {
    console.log("Updated linear combination:", newComb);
    if (selection.value == null) return;
    selection.value.setTarget({
        targets: newComb.map((t) => ({
            name: t.name,
            val: t.val,
            weight: t.weight
        }))
    });
}, { deep: true });
</script>

<style scoped>
.datapoint-guide {
    width: 95%;
    display: flex;
    flex-direction: column;
    justify-items: center;
    align-items: center;
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
    max-width: 24vw;
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
    padding: 5px 0;
    padding: 5px;
    border: 1px solid #ccc;
    background-color: #f9f9f9;
    cursor: grab;
}

.search-result-item:hover {
    background-color: #e0e0e0;
}

.linear-objectives {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 5px 10px;
    width: 80%;
}

.linear-objective {
    padding: 5px 0;
    width: 95%;
}
</style>