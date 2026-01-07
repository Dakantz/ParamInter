<template>
    <div class="datapoint-guide">
        <h2>Explore Interpolation</h2>
        <h3>Selection</h3>

        <div class="interpolation-ends" v-if="interpolation">
            <div v-for="end, i in interpolation_ends" :key="i" class="interpolation-end">
                <SpyderChart :rep="data_rep" v-model="interpolation_ends[i]" :editable="false" />
            </div>
        </div>


        <h3>Interpolated Output Values</h3>
        <div class="editable-outs" v-if="interpolation">
            <div v-for="(types, cat_name) of state.visible_types" :key="cat_name">
                <IntOverview :int_result="(state.interpolation_copy as InterpolationResult)" :types="types"
                    :data_rep="data_rep" :cat_name="cat_name" @hover="state.hovered_value = $event"
                    v-model="state.hovered_offset" @select="selectDp($event)" />
            </div>
        </div>
        <h3>Interpolated Input Values</h3>
        <div class="interpolation-hover" v-if="interpolation && state.hovered_offset >= 0 && state.hovered_dp">
            <SpyderChart :rep="data_rep" v-model="state.hovered_dp.inputs" :editable="false"
                :sensitivities="state.sensitivities_for_hover" />
        </div>
        <div v-if="state.loading">
            <v-progress-linear color="primary" indeterminate></v-progress-linear>
            <span>Loading...</span>
        </div>

    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef, computed } from 'vue';
import * as d3 from 'd3';
import { DataRepository, LoadedDataPoints } from '../../proc/types';
import SpyderChart from './SpyderChart.vue';
import { DataPoint, InterpolationResult } from '../../api/Api';
import Overview from './interpolation/IntOverview.vue';
import { PlotSelection } from '../types';
import IntOverview from './interpolation/IntOverview.vue';
onMounted(() => {
    console.log("Interpolation component mounted");
});
const selection = defineModel<PlotSelection>();
const emit = defineEmits<{
    (e: 'preview', idx: number): void;
    (e: 'select', idx: number): void;
}>();
const { data_rep, interpolation } = defineProps({
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    },
    interpolation: {
        type: Object as () => InterpolationResult | null,
        default: () => (null)
    },
});


const state = reactive({
    loading: false,
    hovered_offset: -1,
    hovered_dp: null as DataPoint | null,
    sensitivities_for_hover: [] as number[],
    visible_types: {} as Record<string, string[]>,
    input_types: [] as string[],
    interpolation_copy: null as InterpolationResult | null,
    hovered_value: "",
    hovered_index: -1,
});
function selectDp(idx: number) {
    console.log("Selecting Data Point:", idx);
    if (idx >= 0) {
        const true_idx = state.interpolation_copy?.indices[idx];
        if (true_idx !== undefined) {
            emit('select', true_idx);
        }
    }
}
watch(() => state.hovered_offset, (idx) => {
    // console.log("Hovered index:", idx);
    if (idx >= 0 && state.interpolation_copy) {
        state.hovered_index = state.interpolation_copy.indices[idx];
    }
}, { immediate: true });
watch(() => interpolation, (int) => {
    if (int) {
        state.interpolation_copy = JSON.parse(JSON.stringify(int));
        // console.log("New interpolation:", int);
    } else {
        state.interpolation_copy = null;
    }
}, { immediate: true });
const interpolation_ends = computed(() => {
    if (interpolation) {
        return [interpolation.inputs[0], interpolation.inputs[interpolation.inputs.length - 1]];
    }
    return [];
});
watch(() => data_rep.description, (desc) => {
    console.log("New types:", desc);
    if (desc?.all_columns.length === 0) {
        console.warn("No types available in data repository.");
        return;
    }
    state.input_types = desc?.input_cols || [];
    state.visible_types = data_rep.all_types;

}, { immediate: true });
watch(() => state.hovered_index, (idx) => {
    console.log("Hovered index:", idx);
    if (idx && idx >= 0) {
        if (state.hovered_value) {
            showSensitivity(state.hovered_value, idx);
        }
        emit('preview', idx);
        data_rep.dps.getDP(idx).then((dp) => {
            state.hovered_dp = dp;
            // console.log("Selected Data Point:", dp);
        }).catch((error) => {
            console.error("Error fetching data point:", error);
        });
    }
}, { immediate: true });

function showSensitivity(out_col: string, hovered_index: number) {
    if (state.hovered_dp) {
        data_rep.client.dataPoint.explanationsForDpDataPointExplanationsIdxPost(
            hovered_index || -1, {
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
    align-items: start;
    justify-content: start;
    margin: 4px;
}


.interpolation-ends {
    display: flex;
    flex-direction: row;
    margin: 10px 0;
    width: 100%;
}

.interpolation_end {
    flex: 1;
    margin: 0 10px;
    width: 50%;
}
</style>