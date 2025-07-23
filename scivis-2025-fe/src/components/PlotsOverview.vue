<template>
    <div ref="plot" class="plot-containers">
        <div v-for="emb_key in loaded_keys" :key="emb_key">
            <h3>{{ emb_key }}</h3>
            <ReducedDimPlot :embedded_data="data_rep.all_embeddings.all_embeddings[emb_key]"
                :full_data="data_rep.data_points" v-model="selection" :embedding_name="emb_key" :data_rep="data_rep"
                :results="results" />
        </div>
    </div>
</template>
<script lang="ts" setup>
import { defineProps, defineModel, reactive, watch, ref, onMounted, ModelRef } from 'vue';
import { DataRepository } from '../proc/types';
import { PlotSelection, PlotSelectionResults } from './types';
import ReducedDimPlot from './ReducedDimPlot.vue';

const selection: ModelRef<PlotSelection> = defineModel({
    type: PlotSelection,
    default: () => new PlotSelection()
});

const { data_rep, loaded_keys, results } = defineProps({
    data_rep: {
        type: DataRepository,
        required: true
    },
    loaded_keys: {
        type: Array as () => string[],
        default: () => []
    },
    results: {
        type: Object as () => PlotSelectionResults,
        default: () => new PlotSelectionResults()
    }

});

const ui_params = reactive({
    // all_embeddings: [] as string[],
});
watch(() => data_rep, (newData) => {
    if (newData) {
        // ui_params.all_embeddings = Object.keys(newData.all_embeddings.all_embeddings)
        // console.log("Updated embeddings list:", ui_params.all_embeddings);
    }
}, { immediate: true });
</script>

<style scoped>
.plot-containers {
    height: 100%;
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    align-items: center;
    flex-direction: row;
}
</style>