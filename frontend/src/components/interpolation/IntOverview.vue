<template>
    <div class="int-outputs-overview">
        <h2>{{ cat_name }}</h2>
        <div class="int-output-item" v-for="(t) in type_indices" :key="t.idx">
            <IntSingleOut :out_name="t.name" :int_results="int_results" v-model="hovered_index" :data_rep="data_rep"
                :out_idx="t.idx" @hover="emit('hover', t.name)" @select="emit('select', $event)" />
        </div>
    </div>
</template>
<script lang="ts" setup>
import { watch } from 'vue';
import { DataPoint, InterpolationResult } from '../../api/Api';
import { DataRepository } from '../../proc/types';
import IntSingleOut from './IntSingleOut.vue';
import { HoveredInterpolation } from '../types';

const emit = defineEmits<{
    (e: 'hover', name: string): void;
    (e: 'select', idx: HoveredInterpolation): void;
}>();

const hovered_index = defineModel<HoveredInterpolation>({
    type: Object as () => HoveredInterpolation,
    default: { interpolation_idx: -1, index_in_interpolation: -1 }
});

const { types, data_rep, cat_name, int_result: int_results } = defineProps({
    types: {
        type: Array as () => string[],
        default: () => []
    },
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    },
    cat_name: {
        type: String,
        required: true
    },
    int_result: {
        type: Object as () => InterpolationResult[],
        required: true
    }

});
const type_indices = types.map((t) => { return { name: t, idx: data_rep.getTypeIndex(t) } });
watch(() => int_results, (int) => {
    // console.log("New outputs in IntOverview:", int_result.outputs);
}, { immediate: true });
</script>
<style scoped>
.int-outputs-overview {
    display: flex;
    flex-direction: column;
    font-size: 8px;
    margin: 4px;
    align-items: center;
}

h2 {
    font-size: 1.2em;
    margin-left: 10px;
}

.int-output-item {
    margin: 2px 0;
}
</style>