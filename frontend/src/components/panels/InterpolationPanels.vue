<template>
    <div class="main_container">
        <div class="inter-panel">
            <DatapointSearch :data_rep="(data_rep as DataRepository)" v-model="state.selection"
                @preview="previewSelected" @select="updateSelection" />
            <div v-if="state.loading">
                <span>Loading...</span>
            </div>
        </div>
        <div class="divider"></div>
        <div class="inter-panel">
            <DatapointGuide :data_rep="(data_rep as DataRepository)" v-model="state.selection"
                :selected_dp="state.selection.selected_indices[0]" @preview="previewSelected"
                @select="updateSelection" />
        </div>
        <div class="divider"></div>
        <div class="inter-panel">
            <DatapointInterpolation :data_rep="(data_rep as DataRepository)" v-model="state.selection"
                :interpolations="interpolations" @preview="previewSelected" @select="updateSelection">
            </DatapointInterpolation>
        </div>

        <div class="divider"></div>
        <div class="inter-panel">
            <div v-if="state.loading">
                <Loading />
            </div>
            <PlotsOverview :data_rep='(data_rep as DataRepository)' :loaded_keys="state.loaded_keys"
                v-model="state.selection" :results="state.current_results" :all_embeddings="all_embeddings"
                :interpolations="interpolations">
            </PlotsOverview>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { AllEmbeddings, DataRepository } from '../../proc/data-store';
import { CostOverviewData, PlotSelection, PlotSelectionResults } from '../types';
import PlotsOverview from '../PlotsOverview.vue';
import DatapointSearch from './DatapointSearch.vue';
import DatapointGuide from './DatapointGuide.vue';
import DatapointInterpolation from './DatapointInterpolation.vue';
import { InterpolationResult } from '../../api/Api';
import Loading from '../ui/Loading.vue';
const { data_rep } = defineProps<{
    data_rep: DataRepository;
}>();
const state = reactive({
    selection: new PlotSelection(),
    current_results: new CostOverviewData(),
    loading: false,
    loading_progress: 0,
    loaded_keys: [] as string[],
});
const all_embeddings = new AllEmbeddings();
let interpolations = null as InterpolationResult[] | null;
onMounted(() => {
    state.loading = true;
    data_rep.loadAll((p, keys) => {
        state.loading_progress = p;
        state.loaded_keys = keys;

        console.log("Loading progress:", p, keys);
    }, all_embeddings).then(() => {
        state.loading = false;
    }).catch((error) => {
        console.error('Error loading data:', error);
        state.loading = false;
    });
});
function refetchSelectionState() {
    console.log("Refetching selection state");
    let target = state.selection.target;
    if (!target) return;
    state.loading = true
    data_rep.client.datasets.getObjectiveCostsDatasetsSetNameDataPointMinimizeCostPost(data_rep.set_name, target).then((similarity) => {
        state.current_results = similarity.data;
        state.loading = false
        // console.log("Current similarity scores:", state.current_results.similarities);
    }).catch((error) => {
        state.loading = false
        console.error('Error fetching objective costs:', error);
    });
    if (state.selection.selected_indices.length == 1) {
        state.selection.previewed_index = null;
        const sel = state.selection.selected_indices[0];
        state.loading = true
        data_rep.client.datasets.getMinimizationInterpolationDatasetsSetNameDataPointMinimizeInterpolationPost(data_rep.set_name, {
            start_idx: sel,
            min: target,
            samples: 512,
            k_options: 1
        }).then((int) => {
            interpolations = int.data;
            state.loading = false
            // console.log("Current similarity scores:", state.current_results.similarities);
        }).catch((error) => {
            state.loading = false
            console.error('Error fetching interpolation data:', error);
        });
    }
}
watch(() => state.selection.target, (target) => {
    refetchSelectionState();
}, { immediate: true, deep: true });
watch(() => state.selection.selected_indices, (sel) => {
    refetchSelectionState();
}, { immediate: true, deep: true });
function previewSelected(idx: number) {
    // console.log("Previewing selected index:", idx);
    // Set the hovered index in the selection
    state.selection.previewed_index = idx
}
function updateSelection(newSelection: number) {
    console.log("Updating selection:", newSelection);
    // if (state.selection.selected_indices.length == 2) {
    //   // If two indices are already selected, replace the first one
    //   state.selection.selected_indices = [newSelection];
    //   state.current_results.interpolation = null; // Reset interpolation when selection changes
    // } else {
    //   state.selection.selected_indices = [...state.selection.selected_indices, newSelection];
    // }
    state.selection.selected_indices = [newSelection];
    state.selection.previewed_index = null;
    // Emit the updated selection to parent components if needed
    // emit('update:selection', newSelection);
}
function reset() {
    console.log("Resetting selection");
    if (!state.selection) {
        state.selection = new PlotSelection();
    }
    state.selection.selected_indices = [];
    state.selection.previewed_index = null;
    interpolations = null;
}
</script>
<style>
.main_container {
    width: 100%;
    display: flex;
    justify-content: start;
    align-items: center;
    font-family: 'Roboto Mono', monospace;
}

.plot_container {
    /* width: 2vw; */
    height: 100%;
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    align-items: center;
    flex-direction: row;
    overflow-y: auto;
}

.divider {
    height: 93vh;
    width: 1px;
    background-color: #ccc;
}


.inter-panel {
    width: 24.5vw;
    min-width: 24vw;
    height: 93vh;
    display: flex;
    flex-direction: column;
    justify-items: start;
    align-items: center;
    overflow-y: auto;

    margin: 0px;
}
</style>