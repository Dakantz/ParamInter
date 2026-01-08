<template>
    <div class="single-outview">
        <span class="out-name">{{ out_name }}={{ selected_value.toFixed(2) }} <span>({{ min_value.toFixed(2) }}, {{
            max_value.toFixed(2) }})</span> <button @click="$emit('remove')">X</button></span>
        <div class="out-value" ref="wrapper_ref" @compositionend="updateGraph">
            <svg ref="svg_ref" class="svg-outchart" width="0px" height="0px">
                <g>
                    <path d="" />
                </g>

            </svg>
        </div>
    </div>
</template>
<script setup lang="ts">
import { computed, onMounted, useTemplateRef, watch, onUpdated, reactive } from 'vue';
import { DataRepository } from '../../../proc/types';
import * as d3 from 'd3';
import { InterpolationResult } from '../../../api/Api';
import { outValues } from '../../helpers/utils';
defineEmits<{
    (e: 'hover'): void;
    (e: 'remove'): void;
}>();
const selected_value = defineModel<number>({
    type: Number,
    required: true
});
const { out_name, data_rep } = defineProps({

    out_name: {
        type: String,
        required: true
    },
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    },

})
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




let yScale = d3.scaleLinear()
    .domain([0, 1])
    .range([0, 32]);
let xScale = d3.scaleLinear()
    .domain([0, 1])
    .range([0, 64]);
function updateGraph() {
    if (!svg_ref.value || !wrapper_ref.value) return;

    const width = wrapper_ref.value.clientWidth - 5;
    const height = wrapper_ref.value.clientHeight - 5;
    // console.log("Updating graph with width:", width, "height:", height);
    const svg = d3.select(svg_ref.value)
        .attr('width', width)
        .attr('height', height);

    svg.selectAll('path').remove(); // Clear previous content


    yScale = d3.scaleLinear()
        .domain([0, 1])
        .range([height, 0]);
    xScale = d3.scaleLinear()
        .domain([min_value.value, max_value.value])
        .range([0, width]);

    // draw one path end to end and one circle at the selected value
    const line = d3.line<number>()
        .x((d, i) => xScale(d))
        .y((d) => yScale(0.5));
    svg.append('path')
        .datum([min_value.value, selected_value.value])
        .attr('class', 'output-line')
        .attr('d', line);
    svg.append('path')
        .datum([min_value.value, max_value.value])
        .attr('class', 'full-line')
        .attr('d', line);
    svg.selectAll('.hover-point').remove(); // Remove previous hover point
    svg.append('circle')
        .attr('class', 'hover-point')
        .attr('cx', xScale(selected_value.value))
        .attr('cy', yScale(0.5))
        .attr('r', 5)
}
watch(() => selected_value, (idx) => {

});
onMounted(() => {
    const wrapper = d3.select(wrapper_ref.value)
    wrapper.on('mousemove', (evt) => {
        if (!wrapper_ref.value) return;
    }).on('click', (evt) => {
        if (!wrapper_ref.value) return;
        const val = xScale.invert(d3.pointer(evt)[0])
        selected_value.value = val;
    });

    updateGraph();
});
watch(() => selected_value.value, () => {
    updateGraph();
}, { immediate: true });
</script>
<style>
.single-outview {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 80%;
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
    width: 100%;
}

.out-value .value {
    margin: 0 10px;
    font-size: 1.2em;
}

.svg-outchart {
    min-width: 64px;
    min-height: 32px;
}

.output-line {
    fill: none;
    stroke: rgb(52, 166, 220);
    stroke-width: 1.5;
}

.full-line {
    fill: none;
    stroke: rgb(200, 200, 200);
    stroke-width: 1.0;
}

.hover-point {
    fill: rgb(132, 208, 82);
    stroke: rgb(58, 173, 100);
    stroke-width: 1.5;
}
</style>