<template>
    <div class="search-container">
        <h2>Similar Points</h2>
        <SpyderChart :rep="data_rep" v-model="state.dim_data" :editable="true" />
        <div class="search-results">
            <div v-for="(result, idx) in state.search_results" :key="idx" class="search-result-item"
                @mouseenter="emit('preview', result.index || -1)" @click.capture="emit('select', result.index || -1)">
                <SpyderChart :rep="data_rep" v-model="result.inputs" :editable="false" />
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef } from 'vue';
import * as d3 from 'd3';
import { DataRepository } from '../../proc/types';
import SpyderChart from './SpyderChart.vue';
import { DataPoint } from '../../api/Api';

const start_idx = defineModel({
    type: Number,
    default: -1
});
const emit = defineEmits<{
    (e: 'preview', idx: number): void;
    (e: 'select', idx: number): void;
}>();
const { data_rep } = defineProps({
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    }
});

const state = reactive({
    dimensions: [] as string[],
    dim_data: [] as number[],
    search_results: [] as DataPoint[],
});

watch(() => data_rep.description, (desc) => {
    console.log("New types:", desc);
    if (!desc) return;

    state.dimensions = data_rep.description?.input_cols || [];

    if (data_rep && data_rep.description && data_rep.description.inputs_constrained) {
        let max_sum = Object.keys(data_rep.description?.max_values || {}).filter((k) => state.dimensions.includes(k)).reduce((sum, k) => sum + (data_rep.description?.max_values[k] || 0), 0);
        state.dim_data = state.dimensions.map(type => (data_rep.description?.max_values?.[type] || 0) / state.dimensions.length);
    } else {
        state.dim_data = state.dimensions.map((type) => data_rep.description?.mean_values?.[type] || 0);
    }
    console.log("Initialized dim_data:", state.dim_data);
}, { immediate: true });

watch(() => state.dim_data, (dim_data) => {
    if (dim_data.length > 0) {
        data_rep.client.dataPoint.getSimilarDataPointsDataPointSimilarPost({
            values: dim_data.map((v) => v),
            k: 4
        }).then((similarity) => {
            // console.log("Similarity results:", similarity);
            state.search_results = similarity.data;
        }).catch((error) => {
            console.error("Error fetching similar data points:", error);
        });
    }
}, { immediate: true });

</script>

<style scoped>
.search-container {
    width: 100%;
    min-height: 100vh;
    max-height: 100vh;
    /* overflow-y: auto; */
    display: flex;
    flex-direction: column;
    justify-items: center;
    align-items: center;
    padding: 7px;
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