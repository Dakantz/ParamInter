<template>
    <div ref="plot" class="plot-containers">
        <div v-for="emb_key in loaded_keys" :key="emb_key">
            <h3>{{ emb_key }}</h3>
            <ReducedDimPlot :embedded_data='all_embeddings.all_embeddings[emb_key]' :full_data="data_rep.data_points"
                v-model="selection" :embedding_name="emb_key" :data_rep="data_rep" :results="results"
                :interpolations="interpolations" />
        </div>
    </div>
</template>
<script lang="ts" setup>
import { reactive, watch, ref, onMounted, ModelRef } from 'vue';
import { AllEmbeddings, DataRepository, Embeddings } from '../proc/data-store';
import { CostOverviewData, PlotSelection, PlotSelectionResults } from './types';
import ReducedDimPlot from './ReducedDimPlot.vue';
import { InterpolationResult } from '../api/Api';

const selection: ModelRef<PlotSelection> = defineModel({
    type: PlotSelection,
    default: () => new PlotSelection()
});

const { data_rep, loaded_keys, results } = defineProps({
    data_rep: {
        type: DataRepository,
        required: true
    },
    all_embeddings: {
        type: Object as () => AllEmbeddings,
        required: true
    },
    interpolations: {
        type: Object as () => InterpolationResult[] | null,
        default: () => []
    },
    loaded_keys: {
        type: Array as () => string[],
        default: () => []
    },
    results: {
        type: Object as () => CostOverviewData | null,
        default: () => null
    }

});

const ui_params = reactive({
    // all_embeddings: [] as string[],
});
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