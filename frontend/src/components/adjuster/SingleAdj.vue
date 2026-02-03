<template>
    <div class="adj-outview">
        <div class="adj-top"> <span class="adjuster-name"> {{ out_name }}={{ selected_value.toFixed(2) }}</span> <button
                @click="$emit('remove')">X</button></div>
        <div class="dp-value" ref="wrapper_ref" @compositionend="updateGraph">
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
import { DataRepository } from '../../proc/data-store';
import * as d3 from 'd3';
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

function initScales() {
    if (!svg_ref.value || !wrapper_ref.value) return;
    const width = wrapper_ref.value.clientWidth - 5;
    const height = wrapper_ref.value.clientHeight - 5;

    // console.log("Updating graph with width:", width, "height:", height);
    const svg = d3.select(svg_ref.value)
        .attr('width', width)
        .attr('height', height);

    svg.selectAll('*').remove();

    yScale = d3.scaleLinear()
        .domain([0, 1])
        .range([height, 0]);
    xScale = d3.scaleLinear()
        .domain([min_value.value, max_value.value])
        .range([0, width]);
    const fixed_group = svg.append('g').attr('class', 'fixed-elements');

    fixed_group.append('text')
        .attr('x', 7)
        .attr('y', yScale(0.2))
        .text(min_value.value.toFixed(2))
        .attr('font-size', '10px')
        .attr('fill', 'black');

    fixed_group.append('text')
        .attr('x', width - 7)
        .attr('y', yScale(0.2))
        .text(max_value.value.toFixed(2))
        .attr('font-size', '10px')
        .attr('text-anchor', 'end')
        .attr('fill', 'black');
}
function updateGraph() {
    if (!svg_ref.value || !wrapper_ref.value) return;

    const svg = d3.select(svg_ref.value)
    svg.selectAll('g.selection-elements').remove();
    const selection_group = svg.append('g').attr('class', 'selection-elements');
    const line = d3.line<number>()
        .x((d, i) => xScale(d))
        .y((d) => yScale(0.8));
    selection_group.append('path')
        .datum([min_value.value, selected_value.value])
        .attr('class', 'select-line')
        .attr('d', line);
    selection_group.append('path')
        .datum([min_value.value, max_value.value])
        .attr('class', 'full-line')
        .attr('d', line);
    selection_group.append('circle')
        .attr('class', 'hover-point')
        .attr('cx', xScale(selected_value.value))
        .attr('cy', yScale(0.8))
        .attr('r', 5)

}
watch(() => selected_value, (idx) => {

});
onMounted(() => {
    const wrapper = d3.select(wrapper_ref.value)
    let clicked_element: any = null;
    function updateSelectionPos(evt: MouseEvent) {
        if (!wrapper_ref.value) return;
        if (clicked_element === null) return;
        if (clicked_element == "hover_point") {
            const val = xScale.invert(d3.pointer(evt)[0])
            selected_value.value = val;
        }
    }
    wrapper.on('mousemove', (evt) => {
        updateSelectionPos(evt);
    }).on('mousedown', (evt) => {
        if (!wrapper_ref.value) return;
        const mouse_pos = d3.pointer(evt);
        const hover_x = xScale(selected_value.value);
        const hover_y = yScale(0.8);
        const dist_to_hover = Math.sqrt((mouse_pos[0] - hover_x) ** 2 + (mouse_pos[1] - hover_y) ** 2);

        // if (dist_to_hover < 7) {
        clicked_element = "hover_point";
        evt.preventDefault();
        // }
    }).on('mouseup', (evt) => {
        updateSelectionPos(evt);
        clicked_element = null;
        
    });
    initScales();
    updateGraph();
});
watch(() => selected_value.value, () => {
    updateGraph();
}, { immediate: true });
</script>
<style>
.adj-outview {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    padding: 5px;
}

.adj-outview:hover {
    background-color: #f0f0f0;
}

.adjuster-name {
    font-weight: bold;
    margin-bottom: 2px;
    max-width: 90%;
    width: 90%;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
    text-align: start;
}

.adj-top {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 5px 5px;
    box-sizing: border-box;
}

.dp-value {
    display: flex;
    flex-direction: row;
    align-items: center;
    width: 100%;
}

.dp-value .value {
    margin: 0 10px;
    font-size: 1.1em;
}

.svg-outchart {
    min-width: 64px;
    min-height: 32px;
}

.select-line {
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