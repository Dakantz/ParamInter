<template>
  <v-app>
    <v-main>
      <div class="main_container">
        <div class="plot_container">
          <div v-if="state.loading">
            <v-progress-linear
              :value="state.loading_progress"
              color="primary"
            ></v-progress-linear>
            <span>Loading...</span>
          </div>
          <PlotsOverview :data_rep='(state.data_rep as DataRepository)'
             v-model="state.selection">
          </PlotsOverview>
        </div>
        <div class="divider"></div>
        <div class="search_container">

        </div>
      </div>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineModel, watch, onMounted } from 'vue';
import { DataRepository } from './proc/types';
import { PlotSelection } from './components/types';
import PlotsOverview from './components/PlotsOverview.vue';

const state = reactive({
  data_rep: new DataRepository(),
  selection: new PlotSelection(),
  loading: false,
  loading_progress: 0,
});

onMounted(() => {
  // Initialize data_rep here or fetch it from an API
  state.data_rep = new DataRepository(); // Example initialization
  state.loading = true;
  state.data_rep.loadAll((p) => {
    state.loading_progress = p;
    console.log("Loading progress:", p);
  }).then(() => {
    state.loading = false;
  }).catch((error) => {
    console.error('Error loading data:', error);
    state.loading = false;
  });
});

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