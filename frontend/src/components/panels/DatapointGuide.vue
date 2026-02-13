<template>
    <div class="datapoint-guide" :class="{ 'non_active': !state.dp }">
        <h2>Build Minimizer</h2>
        <h3>Start Point</h3>
        <SpyderChart v-if="state.dp" :rep="data_rep" v-model="state.dp.inputs" :editable="false"
            :sensitivities="state.sensitivities_for_hover" :uncertainties="state.dp.uncertainties" />
        <h3>Linear Objective</h3>
        <h4 class="info">Drag to adjust</h4>
        <div class="linear-objectives">
            <div v-for="(target, idx) in Object.keys(state.filter_targets).map(key => ({ k: key, v: state.filter_targets[key] }))"
                :key="idx" @mouseenter="showSensitivity(target.v.objective.name)" class="linear-objective">
                <SingleAdj v-model="state.filter_targets[target.v.objective.name]" :out_name="target.v.objective.name"
                    :data_rep="data_rep" @hover="showSensitivity(target.v.objective.name)"
                    @remove="removeTarget(target.v.objective.name)" />
            </div>
            min
            <span v-for="(target, idx) in Object.values(state.filter_targets)" :key="idx">
                {{ target.objective.weight.toFixed(2) }} ({{ target.objective.name }} - {{
                    target.objective.val.toFixed(2) }}) <span v-if="idx < Object.values(state.filter_targets).length - 1"> +
                    <br /> </span>
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
                    @hover="showSensitivity($event)" @add="addFilterTarget($event)" />
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
import { DataPoint, FilterCondition, LinearTarget } from '../../api/Api';
import Overview from '../adjuster/Overview.vue';
import { PlotSelection } from '../types';
import SingleAdj from '../adjuster/SingleAdj.vue';
import { debounce } from '../helpers/utils';

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
    filter_targets: {} as Record<string, {
        objective: LinearTarget,
        filter: FilterCondition
    }>,

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
            // console.log("Selected Data Point:", dp);
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

function addFilterTarget(name: string) {
    console.log("Adding linear target:", name);
    if (state.dp) {
        let idx = data_rep.getTypeIndex(name);
        let value: number;
        if (idx >= state.dp.inputs.length) {
            value = state.dp.outputs[idx - state.dp.inputs.length];
        } else {
            value = state.dp.inputs[idx];
        }
        state.filter_targets[name] = {
            objective: {
                name: name,
                val: value,
                weight: 1.0
            },
            filter: {
                name: name,

            }
        };
    }
}
function removeTarget(name: string) {
    console.log("Removing linear target:", name);
    delete state.filter_targets[name];
}
function updateSelection() {
    if (selection.value) {
        selection.value.setTarget({
            targets: Object.values(state.filter_targets).map(t => t.objective),
            filters: Object.values(state.filter_targets).map(t => t.filter)
        });
    }
}
let debouncedUpdateSelection = debounce(updateSelection, 300);
watch(() => state.filter_targets, (newComb) => {
    // console.log("Updated linear combination:", newComb);
    if (selection.value == null) return;
    debouncedUpdateSelection();
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