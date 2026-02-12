<template>
    <div class="adj-outview">
        <div class="adj-top"> <span class="adjuster-name"> {{ out_name }}={{ objective_filter.objective.val.toFixed(2)
                }}</span> <button @click="$emit('remove')">X</button></div>
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
import { ColumnObjective } from '../types';
import { debounce } from '../helpers/utils';
defineEmits<{
    (e: 'hover'): void;
    (e: 'remove'): void;
}>();
const objective_filter = defineModel<ColumnObjective>({
    type: Object as () => ColumnObjective,
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

    let min_val = objective_filter.value.filter.min || min_value.value;
    let max_val = objective_filter.value.filter.max || max_value.value;
    const svg = d3.select(svg_ref.value)
    svg.selectAll('g.selection-elements').remove();
    const selection_group = svg.append('g').attr('class', 'selection-elements');
    const line = d3.line<number>()
        .x((d, i) => xScale(d))
        .y((d) => yScale(0.8));
    selection_group.append('path')
        .datum([min_val, max_val])
        .attr('class', 'full-line')
        .attr('d', line);
    selection_group.append('path')
        .datum([min_val, objective_filter.value.objective.val])
        .attr('class', 'select-line')
        .attr('d', line);
    selection_group.append('circle')
        .attr('class', 'selector-point')
        .attr('cx', xScale(objective_filter.value.objective.val))
        .attr('cy', yScale(0.8))
        .attr('r', 5)
    selection_group.append('circle')
        .attr('class', 'selector-point-brush')
        .attr('id', 'hover-brush')
        .attr('cx', xScale(objective_filter.value.objective.val))
        .attr('cy', yScale(0.8))
        .attr('r', 20)
    // add brushing sides
    let brush_size = 10
    selection_group.append('path')
        .attr('class', "brush")
        .attr('d', d3.line()([
            [xScale(min_val), yScale(0.8)],
            [xScale(min_val), yScale(0.2)]]));
    selection_group.append('rect')
        .attr('class', "brush-handle")
        .attr('id', "min-brush")
        .attr('x', xScale(min_val) - brush_size / 2)
        .attr('y', yScale(0.8))
        .attr('width', brush_size)
        .attr('height', yScale(0.2) - yScale(0.8));


    selection_group.append('path')
        .attr('class', "brush ")

        .attr('d', d3.line()([
            [xScale(max_val), yScale(0.8)],
            [xScale(max_val), yScale(0.2)]]));
    selection_group.append('rect')
        .attr('class', "brush-handle")
        .attr('id', "max-brush")
        .attr('x', xScale(max_val) - brush_size / 2)
        .attr('y', yScale(0.8))
        .attr('width', brush_size)
        .attr('height', yScale(0.2) - yScale(0.8));




}
enum DraggingElement {
    None,
    HoverPoint,
    MinBrush,
    MaxBrush
}
onMounted(() => {
    const wrapper = d3.select(wrapper_ref.value)
    let clicked_element: DraggingElement = DraggingElement.None;
    function updateSelectionPos(evt: MouseEvent) {
        if (!wrapper_ref.value) return;
        if (clicked_element === null) return;
        if (clicked_element == DraggingElement.HoverPoint) {
            const val = xScale.invert(d3.pointer(evt)[0])
            objective_filter.value.objective.val = val;
        } else if (clicked_element == DraggingElement.MinBrush) {
            const val = xScale.invert(d3.pointer(evt)[0])
            objective_filter.value.filter.min = Math.min(val, objective_filter.value.filter.max || max_value.value);
        } else if (clicked_element == DraggingElement.MaxBrush) {
            const val = xScale.invert(d3.pointer(evt)[0])
            objective_filter.value.filter.max = Math.max(val, objective_filter.value.filter.min || min_value.value);
        }
        if (objective_filter.value.filter.min !== undefined && objective_filter.value.filter.max !== undefined) {
            objective_filter.value.filter.min = Math.min(objective_filter.value.filter.min, objective_filter.value.filter.max);
            objective_filter.value.filter.max = Math.max(objective_filter.value.filter.min, objective_filter.value.filter.max);

            objective_filter.value.objective.val = Math.min(Math.max(objective_filter.value.objective.val, objective_filter.value.filter.min), objective_filter.value.filter.max);
        } else if (objective_filter.value.filter.min !== undefined) {
            objective_filter.value.filter.min = Math.max(objective_filter.value.filter.min, min_value.value);

            objective_filter.value.objective.val = Math.max(objective_filter.value.objective.val, objective_filter.value.filter.min);
        } else if (objective_filter.value.filter.max !== undefined) {
            objective_filter.value.filter.max = Math.min(objective_filter.value.filter.max, max_value.value);

            objective_filter.value.objective.val = Math.min(objective_filter.value.objective.val, objective_filter.value.filter.max);
        }
    }
    wrapper
        .on('mousemove', (evt) => {
            updateSelectionPos(evt);
        })
        .on('mousedown', (evt: MouseEvent) => {
            if (!wrapper_ref.value) return;
            const mouse_pos = d3.pointer(evt);
            const hover_x = xScale(objective_filter.value.objective.val);
            const hover_y = yScale(0.8);
            const dist_to_hover = Math.sqrt((mouse_pos[0] - hover_x) ** 2 + (mouse_pos[1] - hover_y) ** 2);
            let target = evt.target as HTMLElement;
            let target_id = target.id;
            if (target_id === "min-brush") {
                clicked_element = DraggingElement.MinBrush;
            } else if (target_id === "max-brush") {
                clicked_element = DraggingElement.MaxBrush;
            } else {
                clicked_element = DraggingElement.HoverPoint;
            }
            evt.preventDefault();
            // }
        }).on('mouseup', (evt) => {
            updateSelectionPos(evt);
            clicked_element = DraggingElement.None;

        });
    initScales();
    updateGraph();
});
watch(() => objective_filter.value, () => {
    updateGraph();
}, { immediate: true, deep: true });
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
    stroke: rgb(213, 213, 213);
    stroke-width: 1.5;
}

.selector-point {
    fill: rgb(52, 166, 220);
    stroke: white;
    stroke-width: 1.5;
}

.selector-point-brush {
    fill: rgba(52, 167, 220, 0);
    cursor: move;
}

.brush {
    stroke: rgb(142, 142, 142);
    stroke-width: 2;
}

.brush-handle {
    fill: rgba(191, 190, 190, 0);
    cursor: ew-resize;

}
</style>