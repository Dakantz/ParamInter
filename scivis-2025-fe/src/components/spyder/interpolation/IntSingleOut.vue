<template>
    <div class="single-outview" @mouseenter="emit('hover', hovered_index)">
        <span class="out-name">{{ out_name }} {{ hovered_value }} <span>({{ min_value.toFixed(2) }}, {{
            max_value.toFixed(2) }})</span></span>
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

const emit = defineEmits<{
    (e: 'hover', index: number): void;
    (e: 'select', idx: number): void;
}>();
const hovered_index = defineModel<number>({
    type: Number,
    default: -1
});
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
    },

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
const hovered_value = computed(() => {
    if (hovered_index.value >= 0 && hovered_index.value < out_values.value.length) {
        return out_values.value[hovered_index.value].toFixed(2);
    }
    return "--";
});

const svg_ref = useTemplateRef('svg_ref');
const wrapper_ref = useTemplateRef('wrapper_ref');



let xScale = d3.scaleLinear()
    .domain([0, out_values.value.length - 1])
    .range([0, 64]);

let yScale = d3.scaleLinear()
    .domain([min_value.value, max_value.value])
    .range([32, 0]);

function updateGraph() {
    if (!svg_ref.value || !wrapper_ref.value) return;

    const width = wrapper_ref.value.clientWidth;
    const height = wrapper_ref.value.clientHeight;
    // console.log("Updating graph with width:", width, "height:", height);
    const svg = d3.select(svg_ref.value)
        .attr('width', width)
        .attr('height', height);

    svg.selectAll('path').remove(); // Clear previous content

    xScale = d3.scaleLinear()
        .domain([0, out_values.value.length - 1])
        .range([0, width]);

    yScale = d3.scaleLinear()
        .domain([min_value.value, max_value.value])
        .range([height, 0]);


    console.log("Updating graph with values:", out_values.value, "min:", min_value.value, "max:", max_value.value);
    svg.append('path')
        .datum(out_values.value)
        .attr('class', 'output-line')
        .attr('d', d3.line<number>()
            .x((d, i) => xScale(i))
            .y(d => yScale(d))
        );
}
watch(() => hovered_index.value, (idx) => {
    const svg = d3.select(svg_ref.value);
    if (idx >= 0 && idx < out_values.value.length) {
        // Highlight the hovered point
        svg.selectAll('.hover-point').remove(); // Remove previous hover point
        svg.append('circle')
            .attr('class', 'hover-point')
            .attr('cx', xScale(idx))
            .attr('cy', yScale(out_values.value[idx]))
            .attr('r', 5)
    }
});
onMounted(() => {
    const wrapper = d3.select(wrapper_ref.value)
    wrapper.on('mousemove', (evt) => {
        if (!wrapper_ref.value) return;
        const width = wrapper_ref.value.clientWidth;
        const hoveredIndex = Math.floor(d3.pointer(evt)[0] / (width / out_values.value.length));
        hovered_index.value = hoveredIndex;
        emit('hover', hoveredIndex);
    }).on('click', (evt) => {
        if (!wrapper_ref.value) return;
        const width = wrapper_ref.value.clientWidth;
        const clickedIndex = Math.floor(d3.pointer(evt)[0] / (width / out_values.value.length));
        hovered_index.value = clickedIndex;
        emit('select', clickedIndex);
    });

    updateGraph();
});
watch(() => out_values.value, () => {
    updateGraph();
}, { immediate: true });
</script>
<style>
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
    min-width: 64px;
    min-height: 32px;
}

.output-line {
    fill: none;
    stroke: rgb(52, 166, 220);
    stroke-width: 1.5;
}

.hover-point {
    fill: rgb(132, 208, 82);
    stroke: rgb(58, 173, 100);
    stroke-width: 1.5;
}
</style>