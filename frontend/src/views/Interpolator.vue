<template>
    <div>
        <div class="header top_bar">
            <RouterLink :to="SITE_BASE_URL + '/'" class="link_btn link_btn_header">
                < </RouterLink>
                    <h2 class="small_h2"> {{ state.manager_settings?.data_name }}</h2><button @click="resetSelection">Reset</button>
        </div>

        <InterpolationPanels v-if="state.data_rep && state.manager_settings"
            :data_rep="(state.data_rep as DataRepository)" v-model="state.selection" />
        <div v-else>
            <Loading />
            Loading dataset...
        </div>
    </div>
</template>
<script setup lang="ts">
import { useRoute } from 'vue-router';
import InterpolationPanels from '../components/panels/InterpolationPanels.vue';
import { DataRepository } from '../proc/data-store';
import { reactive, watch } from 'vue';
import { ManagerSettings } from '../api/Api';
import { SITE_BASE_URL } from '../config';
import { PlotSelection } from '../components/types';
const route = useRoute()
const state = reactive({
    data_rep: null as DataRepository | null,
    manager_settings: null as ManagerSettings | null,
    selection: new PlotSelection(),
});

watch(
    () => route.params.setname,
    async (newDatasetId) => {
        console.log("Dataset ID changed to:", newDatasetId);
        if (newDatasetId) {
            state.data_rep = new DataRepository(newDatasetId as string);
            try {
                await state.data_rep.loadDescription();
                state.manager_settings = state.data_rep.manager_settings;
                console.log("Loaded dataset settings:", state.manager_settings);
            } catch (error) {
                console.error("Error loading dataset settings:", error);
            }
        }
    },
    { immediate: true }
);
function resetSelection() {
    state.selection = reactive(new PlotSelection());
}
</script>
<style scoped>
.link_btn_header {
    margin: 5px;
}
</style>