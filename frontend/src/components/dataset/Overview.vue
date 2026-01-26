<template>
    <div class="dataset-overview">
        <h3>{{ dataset.data_name }}</h3>
        <p>Short Name: {{ dataset.short_data_name }}</p>
        <p>Input Columns: <span class="col_desc" v-for="col in dataset.data_description.input_cols" :key="col">{{ col
        }}</span></p>
        <p>Output Columns: <span class="col_desc" v-for="col in dataset.data_description.output_cols" :key="col">{{ col
        }}</span></p>
        <p>Inputs Constrained: {{ dataset.inputs_constrained ? "Yes" : "No" }}</p>
        <p>Loaded: {{ dataset.loaded ? "Yes" : "No" }}</p>
        <p>
            <button v-bind:class="load_btn_class" @click="loadDataset">Load</button>
            <RouterLink :to="`./interpolator/${dataset_id}`" v-bind:class="explore_link_class">Explore</RouterLink>

        </p>
    </div>

</template>
<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue';
import { Api, ManagerSettings } from '../../api/Api';
import { API_BASE_URL } from '../../config';
const api = new Api({ baseURL: API_BASE_URL });
const { dataset, dataset_id } = defineProps<{
    dataset: ManagerSettings;
    dataset_id: string;
}>();
const state = reactive({
    loading: false,
});
async function loadDataset() {
    state.loading = true;
    try {
        await api.datasets.loadDatasetDatasetsLoadSetNamePost(dataset_id);
        dataset.loaded = true;
    } catch (error) {
        console.error('Error loading dataset:', error);
    } finally {
        state.loading = false;
    }
}

const load_btn_class = computed(() => {
    return {
        inactive: state.loading || dataset.loaded,
    };
});
const explore_link_class = computed(() => {
    return {
        link_btn: true,
        inactive: !dataset.loaded,
    };
});

</script>
<style scoped>
.dataset-overview {
    border-bottom: 1px solid #ccc;
    padding-bottom: 10px;
    margin: 10px 20px;
}

.col_desc {
    display: inline-block;
    margin-right: 8px;
    margin: 2px 6px;
    background-color: #f0f0f0;
}

.inactive {
    opacity: 0.5;
    pointer-events: none;
}
</style>