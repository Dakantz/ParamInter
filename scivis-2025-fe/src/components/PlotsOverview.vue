<template>
    <div ref="plot" class="plot-containers">
        <div v-for="emb_key in ui_params.all_embeddings" :key="emb_key">
            <h3>{{ emb_key }}</h3>
            <ReducedDimPlot :embedded_data="data_rep.all_embeddings.all_embeddings[emb_key]"
                :full_data="data_rep.data_points" v-model="selection" />
        </div>
    </div>
</template>
<script lang="ts" setup>
import { defineProps, defineModel, reactive, watch, ref, onMounted, ModelRef } from 'vue';
import { DataRepository } from '../proc/types';
import { PlotSelection } from './types';
import ReducedDimPlot from './ReducedDimPlot.vue';

const selection: ModelRef<PlotSelection> = defineModel({
    type: PlotSelection,
    default: () => new PlotSelection()
});

const { data_rep } = defineProps({
    data_rep: {
        type: DataRepository,
        required: true
    }
});

const ui_params = reactive({
    all_embeddings: [] as string[],
});
watch(() => data_rep, (newData) => {
    if (newData) {
        ui_params.all_embeddings = Object.keys(newData.all_embeddings.all_embeddings)
    }
}, { immediate: true });
</script>

<style scoped>
.plot-containers {
    width: 80vw;
    height: 100%;
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    align-items: center;
    flex-direction: row;
}
</style>