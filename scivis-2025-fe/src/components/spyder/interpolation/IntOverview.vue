<template>
    <div class="outputs-overview">
        <h2>{{ cat_name }}</h2>
        <div class="output-item" v-for="(t) in type_indices" :key="t.idx">
            <IntSingleOut :out_name="t.name" :int_results="int_result" @hover="emit('hover', t.name)"
                :data_rep="data_rep" :idx="t.idx" />
        </div>
    </div>
</template>
<script lang="ts" setup>
import { watch } from 'vue';
import { DataPoint, InterpolationResult } from '../../../api/Api';
import { DataRepository } from '../../../proc/types';
import IntSingleOut from './IntSingleOut.vue';


const emit = defineEmits<{
    (e: 'hover', name: string): void;
}>();

const int_result = defineModel<InterpolationResult>({ required: true });

const { types, data_rep, cat_name } = defineProps({
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
    }

});
const type_indices = types.map((t) => { return { name: t, idx: data_rep.getTypeIndex(t) } });
watch(() => int_result, (int) => {
    console.log("New outputs in IntOverview:", int_result.value.outputs);
}, { immediate: true });
</script>
<style scoped>
.outputs-overview {
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

.output-item {
    margin: 2px 0;
}
</style>