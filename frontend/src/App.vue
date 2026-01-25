<template>
  <v-app>
    <v-main>
      <div class="main_container">
        <div class="inter-panel">
          <DatapointSearch :data_rep="(state.data_rep as DataRepository)" v-model="state.selection"
            @preview="previewSelected" @select="updateSelection" />
          <div v-if="state.loading">
            <v-progress-linear :value="state.loading_progress" color="primary" indeterminate></v-progress-linear>
            <span>Loading...</span>
          </div>
        </div>
        <div class="inter-panel">
          <DatapointGuide :data_rep="(state.data_rep as DataRepository)" v-model="state.selection"
            :selected_dp="state.selection.selected_indices[0]" @preview="previewSelected" @select="updateSelection" />
        </div>
        <div class="inter-panel">
          <DatapointInterpolation :data_rep="(state.data_rep as DataRepository)" v-model="state.selection"
            :interpolations="interpolations" @preview="previewSelected" @select="updateSelection">
          </DatapointInterpolation>
        </div>

        <div class="divider"></div>
        <div class="plot_container">
          <PlotsOverview :data_rep='(state.data_rep as DataRepository)' :loaded_keys="state.loaded_keys"
            v-model="state.selection" :results="state.current_results" :all_embeddings="all_embeddings"
            :interpolations="interpolations">
          </PlotsOverview>
        </div>
      </div>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { AllEmbeddings, DataRepository } from './proc/types';
import { PlotSelection, PlotSelectionResults } from './components/types';
import PlotsOverview from './components/PlotsOverview.vue';
import DatapointSearch from './components/panels/DatapointSearch.vue';
import DatapointGuide from './components/panels/DatapointGuide.vue';
import DatapointInterpolation from './components/panels/DatapointInterpolation.vue';
import { InterpolationResult } from './api/Api';

const state = reactive({
  data_rep: new DataRepository(),
  selection: new PlotSelection(),
  current_results: new PlotSelectionResults(),
  loading: false,
  loading_progress: 0,
  loaded_keys: [] as string[],
});
const all_embeddings = new AllEmbeddings();
let interpolations = null as InterpolationResult[] | null;
onMounted(() => {
  state.data_rep = new DataRepository();
  state.loading = true;
  state.data_rep.loadAll((p, keys) => {
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
  state.data_rep.client.dataPoint.getObjectiveCostsDataPointMinimizeCostPost(target).then((similarity) => {
    state.current_results.similarities = similarity.data;
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
    state.data_rep.client.dataPoint.getMinimizationInterpolationDataPointMinimizeInterpolationPost({
      start_idx: sel,
      min: target,
      samples: 512
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
  height: 100%;
  display: flex;
  justify-content: start;
  align-items: center;
  font-family: 'Roboto Mono', monospace;
}

.plot_container {
  /* width: 2vw; */
  height: 100vh;
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  align-items: center;
  flex-direction: row;
  overflow-y: scroll;
}

.divider {
  height: 100%;
  width: 1px;
  background-color: #ccc;
}

.inter-panel-container {
  width: 25vw;
  min-width: 25vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-items: start;
  align-items: start;
}

.inter-panel {
  width: 30vw;
  min-width: 25vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-items: center;
  align-items: center;
  overflow-y: scroll;
}

.reset-button {
  margin: 10px 20px;
}

button {
  background-color: #ffd79f;
  border: none;
  padding: 5px 10px;
  cursor: pointer;
  font-size: 1.2em;
}

button:hover {
  background-color: #fbc170;
}

button:active {
  background-color: #fca72f;
}
</style>