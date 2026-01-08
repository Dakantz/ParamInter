<template>
  <v-app>
    <v-main>
      <div class="main_container">
        <div class="search-bar-container">
          <div class="search-bar">
            <DatapointSearch :data_rep="(state.data_rep as DataRepository)" v-model="state.selection"
              @preview="previewSelected" @select="updateSelection"
              v-if="state.selection.selected_indices.length == 0" />
            <DatapointGuide :data_rep="(state.data_rep as DataRepository)" v-model="state.selection"
              :selected_dp="state.selection.selected_indices[0]" v-if="state.selection.selected_indices.length == 1"
              @preview="previewSelected" @select="updateSelection" />
            <DatapointInterpolation :data_rep="(state.data_rep as DataRepository)" v-model="state.selection"
              :interpolation="state.current_results.interpolation" v-if="state.selection.selected_indices.length == 2"
              @preview="previewSelected" @select="updateSelection">
            </DatapointInterpolation>
          </div>
          <div v-if="state.loading">
            <v-progress-linear :value="state.loading_progress" color="primary" indeterminate></v-progress-linear>
            <span>Loading...</span>
          </div>
          <button @click="reset" class="reset-button">Reset Selection</button>

        </div>
        <div class="divider"></div>
        <div class="plot_container">
          <PlotsOverview :data_rep='(state.data_rep as DataRepository)' :loaded_keys="state.loaded_keys"
            v-model="state.selection" :results="state.current_results">
          </PlotsOverview>
        </div>
      </div>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { DataRepository } from './proc/types';
import { PlotSelection, PlotSelectionResults } from './components/types';
import PlotsOverview from './components/PlotsOverview.vue';
import DatapointSearch from './components/spyder/DatapointSearch.vue';
import DatapointGuide from './components/spyder/DatapointGuide.vue';
import DatapointInterpolation from './components/spyder/DatapointInterpolation.vue';

const state = reactive({
  data_rep: new DataRepository(),
  selection: new PlotSelection(),
  current_results: new PlotSelectionResults(),
  loading: false,
  loading_progress: 0,
  loaded_keys: [] as string[],
});

onMounted(() => {
  // Initialize data_rep here or fetch it from an API
  state.data_rep = new DataRepository(); // Example initialization
  state.loading = true;
  state.data_rep.loadAll((p, keys) => {
    state.loading_progress = p;
    state.loaded_keys = keys;

    console.log("Loading progress:", p, keys);
  }).then(() => {
    state.loading = false;
  }).catch((error) => {
    console.error('Error loading data:', error);
    state.loading = false;
  });
});
watch(() => state.selection.selected_indices, (sel) => {
  console.log("Selected indices changed:", sel);
  if (sel.length > 0) {
    state.loading = true
    state.data_rep.client.dataPoint.getSimilarDataPointDataPointSimilarityScoresIndexGet(sel[0]).then((similarity) => {
      state.current_results.similarities = similarity.data;
      state.loading = false
      // console.log("Current similarity scores:", state.current_results.similarities);
    }).catch((error) => {
      state.loading = false
      console.error('Error fetching similarity scores:', error);
    });
  }
  if (sel.length == 2) {

    state.loading = true
    state.data_rep.client.dataPoint.getInterpolationDataPointInterpolationGet({
      from_index: sel[0],
      to_index: sel[1],
      // include_explainations: true
    }).then(resp => {
      state.loading = false
      // console.log("Interpolation data:", resp.data);
      state.current_results.interpolation = resp.data
    }).catch((error) => {
      state.loading = false
      console.error('Error fetching interpolation data:', error);
    });

  }
}, { immediate: true, deep: true });
function previewSelected(idx: number) {
  // console.log("Previewing selected index:", idx);
  // Set the hovered index in the selection
  state.selection.hovered_index = idx
}
function updateSelection(newSelection: number) {
  // console.log("Updating selection:", newSelection);
  if (state.selection.selected_indices.length == 2) {
    // If two indices are already selected, replace the first one
    state.selection.selected_indices = [newSelection];
    state.current_results.interpolation = null; // Reset interpolation when selection changes
  } else {
    state.selection.selected_indices = [...state.selection.selected_indices, newSelection];
  }
  state.selection.hovered_index = null;
  // Emit the updated selection to parent components if needed
  // emit('update:selection', newSelection);
}
function reset() {
  console.log("Resetting selection");
  if (!state.selection) {
    state.selection = new PlotSelection();
  }
  state.selection.selected_indices = [];
  state.selection.hovered_index = null;
  state.current_results.interpolation = null;
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
  /* width: 75vw; */
  height: 100%;
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  align-items: center;
  flex-direction: row;
}

.divider {
  height: 100%;
  width: 1px;
  background-color: #ccc;
}

.search-bar-container {
  width: 24vw;
  min-width: 450px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-items: center;
  align-items: center;
}

.search-bar {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
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