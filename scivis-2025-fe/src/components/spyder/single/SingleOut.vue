<template>
    <div class="single-outview" @mouseenter="emit('hover');">
        <span class="out-name">{{ out_name }} <span>({{ min_value.toFixed(2) }}, {{
            max_value.toFixed(2)}})</span></span>
        <div class="out-value">
            <button @click="increase">+</button>
            <span class="value">{{ val.toFixed(2) }}</span>
            <button @click="decrease">-</button>
        </div>
    </div>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue';
import { DataRepository } from '../../../proc/types';


const emit = defineEmits<{
    (e: 'hover'): void;
}>();

const val = defineModel<number>({
    type: Number,
    default: -1,
});
function increase() {
    if (val.value == 0) {
        val.value = 0.1; // set to a small positive value if it was 0
    }
    val.value = val.value * 1.1
}
function decrease() {
    val.value = val.value * 0.9
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
    margin: 0 10px;
    font-size: 1.2em;
}
</style>