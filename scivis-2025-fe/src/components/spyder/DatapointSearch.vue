<template>
    <div class="search-container">
        <div>
            <h2>Similar Points</h2>
            <SpyderChart :dimensions="state.dimensions" v-model="state.dim_data" :editable="true" :factor="1" />
            <div class="search-results">
                <div v-for="(result, idx) in state.search_results" :key="idx" class="search-result-item"
                    @mouseenter="emit('preview', result.index || -1)" @click.capture="emit('select', result.index || -1)">
                    <SpyderChart :dimensions="state.dimensions" v-model="result.inputs" :editable="false" />
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, defineProps, defineModel, watch, onMounted, useTemplateRef } from 'vue';
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

watch(() => data_rep.all_types, (newTypes) => {
    console.log("New types:", newTypes);
    if (Object.keys(newTypes).length === 0) {
        console.warn("No types available in data repository.");
        return;
    }
    state.dimensions = newTypes[Object.keys(newTypes)[0]];
    state.dim_data = state.dimensions.map(type => 1 / state.dimensions.length);
}, { immediate: true });

watch(() => state.dim_data, (dim_data) => {
    if (dim_data.length > 0) {
        data_rep.client.dataPoint.getSimilarDataPointsDataPointSimilarPost({
            values: dim_data.map((v) => v * 100),
            k: 4
        }).then((similarity) => {
            console.log("Similarity results:", similarity);
            state.search_results = similarity.data;
        }).catch((error) => {
            console.error("Error fetching similar data points:", error);
        });
    }
}, { immediate: true });

</script>

<style>
.search-container {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: start;
    padding: 7px;
}

.search-results {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
}

.search-result-item {
    width: 100%;
    display: flex;
    justify-content: center;
    margin: 5px 0;
    padding: 5px;
    border: 1px solid #ccc;
    background-color: #f9f9f9;
    cursor:  grab;
}

.search-result-item:hover {
    background-color: #e0e0e0;
}
</style>