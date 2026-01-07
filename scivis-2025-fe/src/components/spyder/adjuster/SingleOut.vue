<template>
    <div class="single-outview" @mouseenter="emit('hover');">
        <span class="out-name">{{ out_name }} <span>({{ min_value.toFixed(2) }}, {{
            max_value.toFixed(2) }})</span></span>
        <div class="out-value">
            <button @click="decrease">-</button>
            <span class="value">{{ val.toFixed(2) }}</span>
            <button @click="increase">+</button>
        </div>
    </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue';
import { DataRepository } from '../../../proc/types';
import { DataPoint } from '../../../api/Api';


const emit = defineEmits<{
    (e: 'hover'): void;
}>();

const dp = defineModel<DataPoint>({ required: true });
const idx = computed(() => {
    return data_rep.getTypeIndex(out_name);
});
const val = computed({
    get() {
        if (idx.value >= dp.value.inputs.length) {
            return dp.value.outputs[idx.value - dp.value.inputs.length];
        } else {
            return dp.value.inputs[idx.value];
        }
    },
    set(newVal: number) {
        if (idx.value >= dp.value.inputs.length) {
            dp.value.outputs[idx.value - dp.value.inputs.length] = newVal;
        } else {
            dp.value.inputs[idx.value] = newVal;
        }
    }
});
function increase() {
    val.value = val.value * 1.1;
    if (val.value >= max_value.value) {
        val.value = max_value.value;
    }

}
function decrease() {
    val.value = val.value * 0.9;
    if (val.value <= min_value.value) {
        val.value = min_value.value;
    }
}
const min_value = computed(() => {
    if (data_rep.description) {
        return data_rep.description.min_values[out_name];
    }
    return 0;
});
const max_value = computed(() => {
    if (data_rep.description) {
        return data_rep.description.max_values[out_name];
    }
    return 1;
});
const { out_name, data_rep } = defineProps({
    out_name: {
        type: String,
        required: true
    },
    initial_value: {
        type: Number,
        default: -1
    },
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    }
});

const state = reactive({
    initial_value: -1,
});
onMounted(() => {
    state.initial_value = val.value;
});
</script>
<style scoped>
.single-outview {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.single-outview:hover {
    background-color: #f0f0f0;
}

.out-name {
    font-weight: bold;
    margin-bottom: 2px;
}

.out-value {
    display: flex;
    flex-direction: row;
    align-items: center;
}

.out-value .value {
    margin: 0 5px;
    font-size: 1.2em;
}
</style>