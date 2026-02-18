<template>
    <div class="main_container">
        <div class="inter-panel">
            <DatapointSearch :data_rep="(data_rep as DataRepository)" v-model="selection" @preview="previewSelected"
                @select="updateSelection" />
        </div>
        <div class="divider"></div>
        <div class="inter-panel" v-if="!state.loading_manager">
            <DatapointGuide v-if="selection.selected_indices.length > 0" :data_rep="(data_rep as DataRepository)"
                v-model="selection" :selected_dp="selection.selected_indices[0]" @preview="previewSelected"
                @select="updateSelection" />
        </div>
        <div class="divider"></div>
        <div class="inter-panel" v-if="!state.loading_manager">
            <DatapointInterpolation v-if="interpolations" :data_rep="(data_rep as DataRepository)" v-model="selection"
                :interpolations="interpolations" @preview="previewSelected" @select="updateSelection">
            </DatapointInterpolation>
            <Loading v-if="state.loading_costs" />
        </div>

        <div class="divider"></div>
        <div class="inter-panel">
            <div v-if="state.loading_embeddings">
                <Loading />
            </div>
            <PlotsOverview :data_rep='(data_rep as DataRepository)' :loaded_keys="state.loaded_keys" v-model="selection"
                :results="current_costs" :all_embeddings="all_embeddings" :interpolations="interpolations">
            </PlotsOverview>
        </div>
    </div>
</template>
<script setup lang="ts">
import { ref, reactive, watch, onMounted, computed } from 'vue';
import { AllEmbeddings, DataRepository } from '../../proc/data-store';
import { CostOverviewData, PlotSelection } from '../types';
import PlotsOverview from '../PlotsOverview.vue';
import DatapointSearch from './DatapointSearch.vue';
import DatapointGuide from './DatapointGuide.vue';
import DatapointInterpolation from './DatapointInterpolation.vue';
import { InterpolationResult } from '../../api/Api';
import Loading from '../ui/Loading.vue';
const selection = defineModel<PlotSelection>({
    required: true,
});
const { data_rep } = defineProps<{
    data_rep: DataRepository;
}>();
const state = reactive({
    current_results: new CostOverviewData(),
    loading_embeddings: false,
    loading_manager: false,
    loading_costs: false,
    loading_progress: 0,
    initial_load_done: false,
    loaded_keys: [] as string[],
    interpolations: null as InterpolationResult[] | null,
});
const all_embeddings = new AllEmbeddings();
async function loadData() {
    state.loading_embeddings = true;
    state.loading_manager = true;
    try {

        await data_rep.loadDescription();
        state.loading_manager = false;

        await data_rep.loadAll((p, keys) => {
            state.loading_progress = p;
            state.loaded_keys = keys;
            console.log("Loading progress:", p, keys);
        }, all_embeddings);
    } catch (error) {
        console.error('Error loading data:', error);

    }
    state.initial_load_done = true;
    state.loading_manager = false;
    state.loading_embeddings = false;
}
onMounted(() => {
    let urlParams: URLSearchParams | null = null;
    try {
        let urlParams_temp = new URLSearchParams(window.location.search);
        console.log("URL Parameters on mount:", JSON.parse(atob(urlParams_temp.get('selection') || 'null')));
        urlParams = urlParams_temp;
    } catch (error) {
        console.error("Error parsing URL parameters on mount:", error);
    }
    if (urlParams) {
        selection.value.fromQueryParams(urlParams);
    }
    (async () => {
        await loadData();
    })();
});
//http://localhost:3000/param-inter/interpolator/blast_furnace-blast_furnace_slag_alk_BAS2_split_0_normalize_False?selection=eyJzZWxlY3RlZF9pbmRpY2VzIjpbODk4NV0sImhvdmVyZWRfaW50Ijp7ImludGVycG9sYXRpb25faWR4IjotMSwiaW5kZXhfaW5faW50ZXJwb2xhdGlvbiI6LTF9LCJwcmV2aWV3ZWRfaW5kZXgiOm51bGwsInRhcmdldCI6eyJ0YXJnZXRzIjpbeyJuYW1lIjoiUkVfR0VXIFt0XSIsInZhbCI6NjkyLjc2NDk2NTU0MzQ0NDYsIndlaWdodCI6MX1dLCJmaWx0ZXJzIjpbeyJuYW1lIjoiUkVfR0VXIFt0XSJ9XX19
function refetchSelectionState() {
    console.log("Refetching selection state");
    let target = selection.value.target;
    if (!target) return;
    state.loading_costs = true
    data_rep.client.datasets.getObjectiveCostsDatasetsSetNameDataPointMinimizeCostPost(data_rep.set_name, target).then((similarity) => {
        state.current_results = similarity.data;
        state.loading_costs = false
        // console.log("Current similarity scores:", state.current_results.similarities);
    }).catch((error) => {
        state.loading_costs = false
        console.error('Error fetching objective costs:', error);
    });
    if (selection.value.selected_indices.length == 1) {
        console.log("Fetching interpolation for selected index and target:", selection.value.selected_indices[0], target);
        selection.value.previewed_index = null;
        const sel = selection.value.selected_indices[0];
        state.loading_costs = true
        data_rep.client.datasets.getMinimizationInterpolationDatasetsSetNameDataPointMinimizeInterpolationPost(data_rep.set_name, {
            start_idx: sel,
            min: target,
            samples: 512,
            k_options: 1
        }).then((int) => {
            state.interpolations = int.data;
            state.loading_costs = false
            // console.log("Current similarity scores:", state.current_results.similarities);
        }).catch((error) => {
            state.loading_costs = false
            console.error('Error fetching interpolation data:', error);
        });
    }
}
watch(() => selection, (newSelection) => {
    if (state.initial_load_done) {
        try {
            let base64_selection = btoa(JSON.stringify(newSelection.value));
            // set to the query params
            const url = new URL(window.location.href);
            url.searchParams.set('selection', base64_selection);
            window.history.replaceState({}, '', url.toString());
            // console.log("Selection changed, updated URL parameters:", base64_selection, JSON.parse(JSON.stringify(newSelection.value)));
        } catch (error) {
            console.error("Error updating URL parameters:", error);
        }
    }
}, { immediate: true, deep: true });
watch(() => selection.value.target, (target) => {
    refetchSelectionState();
}, { immediate: true, deep: true });
watch(() => selection.value.selected_indices, (sel) => {
    refetchSelectionState();
}, { immediate: true, deep: true });
function previewSelected(idx: number) {
    // console.log("Previewing selected index:", idx);
    // Set the hovered index in the selection
    if (idx >= 0) {
        selection.value.previewed_index = idx
    }
    else {
        selection.value.previewed_index = null;
    }
}
function updateSelection(newSelection: number) {
    // console.log("Updating selection:", newSelection);
    // if (selection.selected_indices.length == 2) {
    //   // If two indices are already selected, replace the first one
    //   selection.selected_indices = [newSelection];
    //   state.current_results.interpolation = null; // Reset interpolation when selection changes
    // } else {
    //   selection.selected_indices = [...selection.selected_indices, newSelection];
    // }
    selection.value.selected_indices = [newSelection];
    selection.value.previewed_index = null;
    // Emit the updated selection to parent components if needed
    // emit('update:selection', newSelection);
}
function reset() {
    console.log("Resetting selection");
    if (!selection) {
        // selection = new PlotSelection();
        console.warn("Selection object not initialized!");
    }
    selection.value.selected_indices = [];
    selection.value.previewed_index = null;
    state.interpolations = null;
}
const interpolations = computed(() => {
    if (selection.value.selected_indices.length < 1) {
        return null;
    }
    return state.interpolations;
});
const current_costs = computed(() => {
    if (!state.current_results || selection.value.target == null) {
        return null;
    }
    return state.current_results;
});
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