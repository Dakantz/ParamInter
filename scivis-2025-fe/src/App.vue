<template>
  <v-app>
    <v-main>
      <div class="main_container">
        <div class="plot_container">
          <PlotsOverview :data_rep='(state.data_rep as DataRepository)' :loaded_keys="state.loaded_keys"
            v-model="state.selection" :results="state.current_results">
          </PlotsOverview>
        </div>
        <div class="divider"></div>
        <div class="search_container">
          <div v-if="state.loading">
            <v-progress-linear :value="state.loading_progress" color="primary" indeterminate></v-progress-linear>
            <span>Loading...</span>
          </div>

        </div>
      </div>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineModel, watch, onMounted } from 'vue';
import { DataRepository } from './proc/types';
import { PlotSelection, PlotSelectionResults } from './components/types';
import PlotsOverview from './components/PlotsOverview.vue';

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
      console.log("Current similarity scores:", state.current_results.similarities);
    }).catch((error) => {
      state.loading = false
      console.error('Error fetching similarity scores:', error);
    });
  }
  if (sel.length == 2) {

    state.loading = true
    state.data_rep.client.interpolation.getInterpolationInterpolationGet({
      from_index: sel[0],
      to_index: sel[1]
    }).then(resp => {
      state.loading = false
      console.log("Interpolation data:", resp.data);
      state.current_results.interpolation = resp.data
    }).catch((error) => {
      state.loading = false
      console.error('Error fetching interpolation data:', error);
    });

  }
}, { immediate: true, deep: true });

</script>
<style scoped>
.main_container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.plot_container {
  width: 80vw;
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

.search_container {
  width: 19vw;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>