<template>
    <div>
        <div class="header top_bar">
            <RouterLink :to="SITE_BASE_URL + '/'" class="link_btn link_btn_header">
                < </RouterLink>
                    <h2 class="small_h2"> {{ state.manager_settings?.data_name }} - Effects</h2>
        </div>

        <EffectsPanels v-if="state.data_rep && state.manager_settings" :data_rep="(state.data_rep as DataRepository)" />
        <div v-else>
            <Loading />
            Loading dataset...
        </div>
    </div>
</template>
<script setup lang="ts">
import { useRoute } from 'vue-router';
import EffectsPanels from '../components/panels/EffectsPanels.vue';
import { DataRepository } from '../proc/data-store';
import { reactive, watch } from 'vue';
import { ManagerSettings } from '../api/Api';
import { SITE_BASE_URL } from '../config';
import Loading from '../components/ui/Loading.vue';
const route = useRoute()
const state = reactive({
    data_rep: null as DataRepository | null,
    manager_settings: null as ManagerSettings | null,
});

watch(
    () => route.params.setname,
    async (newDatasetId) => {
        if (newDatasetId) {
            state.data_rep = new DataRepository(newDatasetId as string);
            try {
                await state.data_rep.loadDescription();
                state.manager_settings = state.data_rep.manager_settings;
            } catch (error) {
                console.error("Error loading dataset settings:", error);
            }
        }
    },
    { immediate: true }
);
</script>
<style scoped>
.link_btn_header {
    margin: 5px;
}
</style>
