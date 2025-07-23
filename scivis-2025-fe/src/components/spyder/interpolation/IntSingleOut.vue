<template>
    <div class="single-outview" @mouseenter="emit('hover');">
        <span class="out-name">{{ out_name }} <span>({{ min_value.toFixed(2) }}, {{
            max_value.toFixed(2) }})</span></span>
        <div class="out-value" ref="wrapper_ref" @compositionend="updateGraph">
            <svg ref="svg_ref" class="svg-outchart">

            </svg>
        </div>
    </div>
</template>
<script setup lang="ts">
import { computed, onMounted, useTemplateRef, watch } from 'vue';
import { DataRepository } from '../../../proc/types';
import * as d3 from 'd3';
import { InterpolationResult } from '../../../api/Api';

const emit = defineEmits<{
    (e: 'hover'): void;
}>();

const { int_results, idx, out_name, data_rep } = defineProps({
    int_results: {
        type: Object as () => InterpolationResult,
        required: true
    },
    idx: {
        type: Number,
        required: true
    },
    out_name: {
        type: String,
        required: true
    },
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    }
})
const out_values = computed(() => {
    if (int_results.outputs && int_results.outputs[idx]) {
        return int_results.outputs.map(out_array => out_array[idx]);
    }
    return [];
});
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

const svg_ref = useTemplateRef('svg_ref');
const wrapper_ref = useTemplateRef('wrapper_ref');
function updateGraph() {
    if (!svg_ref.value || !wrapper_ref.value) return;

    const width = wrapper_ref.value.clientWidth;
    const height = wrapper_ref.value.clientHeight;

    const svg = d3.select(svg_ref.value)
        .attr('width', width)
        .attr('height', height);

    svg.selectAll('*').remove(); // Clear previous content

    const xScale = d3.scaleLinear()
        .domain([0, out_values.value.length - 1])
        .range([0, width]);

    const yScale = d3.scaleLinear()
        .domain([min_value.value, max_value.value])
        .range([height, 0]);
    console.log("Updating graph with values:", out_values.value, "min:", min_value.value, "max:", max_value.value);
    svg.append('path')
        .datum(out_values.value)
        .attr('fill', 'none')
        .attr('stroke', 'steelblue')
        .attr('stroke-width', 1.5)
        .attr('d', d3.line<number>()
            .x((d, i) => xScale(i))
            .y(d => yScale(d))
        );
}

onMounted(() => {
    updateGraph();
});
watch(() => out_values.value, () => {
    updateGraph();
}, { immediate: true });
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

.svg-outchart {
    width: 100%;
    height: 100%;
}
</style>