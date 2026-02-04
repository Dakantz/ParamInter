<template>
    <div class="datapoint-guide" :class="{ 'non_active': !interpolations }">
        <h2>Explore Interpolation</h2>
        <h3>Input Interpolation</h3>
        <InterpolationSlider v-if="interpolations" :data_rep="data_rep" :interpolations="interpolations"
            v-model="selection" :spyder_size="60" :padding="20" :hovered_output="state.hovered_value" />
        <h3>Interpolated Output Values</h3>
        <div class="interpolation-outputs" v-if="interpolations">
            <div v-for="(types, cat_name) of state.visible_types" :key="cat_name" class="interpolation-category">
                <IntOverview :int_result="(state.interpolation_copy as InterpolationResult[])" :types="types"
                    :data_rep="data_rep" :cat_name="cat_name" @hover="hoveredValue($event)"
                    v-model="state.hovered_interpolation" @select="selectDp($event)" />
            </div>
        </div>
        <div v-if="state.loading">
            <span>Loading...</span>
        </div>

    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef, computed } from 'vue';
import * as d3 from 'd3';
import { colorForIndex, DataRepository, LoadedDataPoints } from '../../proc/data-store';
import SpyderChart from '../spyder/SpyderChart.vue';
import { DataPoint, InterpolationResult } from '../../api/Api';
import { HoveredInterpolation, PlotSelection } from '../types';
import IntOverview from '../interpolation/IntOverview.vue';
import InterpolationSlider from '../interpolation/InterpolationSlider.vue';
onMounted(() => {
    console.log("Interpolation component mounted");
});
const selection = defineModel<PlotSelection>(
    {
        required: true,
    }
);
const emit = defineEmits<{
    (e: 'preview', idx: number): void;
    (e: 'select', idx: number): void;
    (e: 'hover', out_name: string): void;
}>();
const { data_rep, interpolations } = defineProps({
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    },
    interpolations: {
        type: Object as () => InterpolationResult[] | null,
        default: () => (null)
    },
});
function highlightClass(selected_idx: number, current_idx: number) {
    return selected_idx === current_idx ? 'highlighted_spyder' : 'normal_spyder';
}

const state = reactive({
    loading: false,
    hovered_interpolation: { interpolation_idx: -1, index_in_interpolation: -1 } as HoveredInterpolation,
    hovered_dp: null as DataPoint | null,
    sensitivities_for_hover: [] as number[],
    visible_types: {} as Record<string, string[]>,
    input_types: [] as string[],
    interpolation_copy: null as InterpolationResult[] | null,
    hovered_value: "",
    hovered_index: -1,
});
function selectDp(idx: HoveredInterpolation) {
    console.log("Selecting Data Point:", idx);
    if (idx.interpolation_idx >= 0) {
        const true_idx = state.interpolation_copy?.[idx.interpolation_idx]?.indices[idx.index_in_interpolation];
        if (true_idx !== undefined) {
            emit('select', true_idx);
        }
    }
}
function hoveredValue(out_name: string) {
    state.hovered_value = out_name;
    emit('hover', out_name);
}
watch(() => state.hovered_interpolation, (hovered_interpolation) => {
    // console.log("Hovered index:", idx);
    if (hovered_interpolation.index_in_interpolation >= 0 && state.interpolation_copy) {
        state.hovered_index = state.interpolation_copy[hovered_interpolation.interpolation_idx].indices[hovered_interpolation.index_in_interpolation];
        if (state.hovered_value) {
            showSensitivity(state.hovered_value, state.hovered_index);
        }

        data_rep.dps.getDP(state.hovered_index).then((dp) => {
            state.hovered_dp = dp;
            showSensitivity(state.hovered_value, state.hovered_index);
        }).catch((error) => {
            console.error("Error fetching data point:", error);
        });
    } else {
        console.log("No valid hovered interpolation.");
    }
    selection.value.hovered_int = hovered_interpolation;
}, { immediate: true, deep: true });
watch(() => interpolations, (int) => {
    if (int) {
        state.interpolation_copy = JSON.parse(JSON.stringify(int));
        // console.log("New interpolation:", int);
    } else {
        state.interpolation_copy = null;
    }
}, { immediate: true });
const interpolation_ends = computed(() => {
    if (interpolations) {
        return interpolations.map(int => int.inputs[int.inputs.length - 1]);
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
    state.visible_types = data_rep.getVisisbleTypes();

}, { immediate: true, deep: true });
watch(() => state.hovered_value, (out_name) => {
    if (out_name && state.hovered_index >= 0) {
        showSensitivity(out_name, state.hovered_index);
    }
}, { immediate: true });
function showSensitivity(out_col: string, hovered_index: number) {
    if (state.hovered_dp) {
        data_rep.client.datasets.explanationsForDpDatasetsSetNameDataPointExplanationsIdxPost(
            hovered_index || -1, data_rep.set_name, {
            for_outputs: [out_col],
            resolution: 16
        }).then((result) => {
            // console.log("Sensitivity Analysis Result:", result);
            if (result.data.length > 0) {
                state.sensitivities_for_hover = result.data[0].sensitivity_scores;
            } else {
                state.sensitivities_for_hover = [];
            }
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
    padding: 0px;
    width: 100%;
}



.search-result-item:hover {
    background-color: #e0e0e0;
}

.interpolation-outputs {
    display: flex;
    flex-direction: row;
    align-items: start;
    justify-content: start;
    margin: 2px;
    max-width: 100%;
    flex-wrap: wrap;
}

.interpolation-category {
    flex: 1;
    padding: 0 5px;
    width: 132px;
}

.interpolation-ends {
    display: flex;
    flex-direction: row;
    margin: 10px 0;
    /* max-height: 10vh; */
}

.interpolation_end {
    flex: 1;
    margin: 0 10px;
    width: 132px;
    height: 10vh;
    display: flex;
    align-items: center;
}

.interpolation-end-label {
    font-weight: bold;
    text-align: center;
    margin-bottom: 5px;
}

.highlighted_spyder {
    border: 2px solid #d4d4d4;
    padding: 2px;
}

.normal_spyder {
    border: 2px solid #ff990000;
    ;
    padding: 2px;
}

.interpolation-hover {
    margin-top: 15px;
    width: 90%;
}
</style>