<template>
    <div class="outputs-overview">
        <h2>{{ cat_name }}</h2>
        <div class="output-item" v-for="(t) in type_indices" :key="t.idx">
            <!-- <SingleOut :out_name="t.name" v-model="dp" @hover="emit('hover', t.name)" :data_rep="data_rep" /> -->
            <button @click="addToSet(t.name, dp)" @mouseenter="emit('hover', t.name)">Add {{ t.name }} (@ {{
                valueOf(t.name).toFixed(2) }})</button>
        </div>

    </div>
</template>
<script lang="ts" setup>
import { DataPoint } from '../../api/Api';
import { DataRepository } from '../../proc/data-store';


const emit = defineEmits<{
    (e: 'hover', name: string): void;
    (e: 'add', name: string): void;
}>();

const dp = defineModel<DataPoint>({ required: true });

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
function valueOf(name: string) {
    const idx = data_rep.getTypeIndex(name);
    let value = 0;
    if (idx >= dp.value.inputs.length) {
        value = dp.value.outputs[idx - dp.value.inputs.length];
    } else {
        value = dp.value.inputs[idx];
    }
    if(!isFinite(value)) value = 0;
    return value;
};
const addToSet = (name: string, dp: DataPoint) => {
    console.log("Adding to set:", name);
    emit('add', name);
};

</script>
<style scoped>
.outputs-overview {
    display: flex;
    flex-direction: column;
    font-size: 8px;
    margin: 2px;
    align-items: center;
}

h2 {
    font-size: 1.2em;
    margin-left: 0px;
}

.output-item {
    margin: 1px 0;
    width: 128px;
}

.output-item button {
    width: 100%;
    padding: 4px;
    /* height: 2.1rem */
}
</style>