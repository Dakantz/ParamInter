<template>
    <div class="dataset_view">
        <div class="header">
            <h2>Available Datasets</h2>
        </div>
        <div v-for="k in Object.keys(state.datasets)" :key="k">
            <Overview :dataset="state.datasets[k]" :dataset_id="k" />
        </div>
        <div v-if="state.loading">
            <Loading />
            Loading datasets...
        </div>
    </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { Api, ManagerSettings } from '../api/Api';
import { API_BASE_URL } from '../config';
import Overview from '../components/dataset/Overview.vue';
import Loading from '../components/ui/Loading.vue';
const router = useRouter();

const api = new Api({ baseURL: API_BASE_URL });
const state = reactive({
    datasets: {} as Record<string, ManagerSettings>,
    loading: true,
});
onMounted(async () => {
    try {
        const response = await api.datasets.getDatasetsDatasetsGet();
        state.datasets = reactive(response.data);
        console.log('Datasets fetched:', state.datasets);
    } catch (error) {
        console.error('Error fetching datasets:', error);
    } finally {
        state.loading = false;
    }
});
</script>
<style>
.dataset_view {
    min-width: 650px;

}
</style>