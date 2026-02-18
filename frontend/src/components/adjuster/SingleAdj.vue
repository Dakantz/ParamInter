<template>
    <div class="adj-outview">
        <div class="adj-top"> <span class="adjuster-name"> {{ out_name }}={{ objective_filter.objective.val.toFixed(2)
        }}</span> <button @click="$emit('remove')">X</button></div>
        <div class="dp-value" ref="wrapper_ref" @compositionend="updateGraph">
            <svg ref="svg_ref" class="svg-selchart" width="0px" height="0px">
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
import { HistogramData } from '../../api/Api';
defineEmits<{
    (e: 'hover'): void;
    (e: 'remove'): void;
}>();
const objective_filter = defineModel<ColumnObjective>({
    type: Object as () => ColumnObjective,
    required: true
});
const state = reactive({
    loading: false,
    hist: null as HistogramData | null,
    active_bins: [] as number[]
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
const text_padding = 40;
const brush_padding = 20;

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
        .range([height - brush_padding, brush_padding]);
    xScale = d3.scaleLinear()
        .domain([min_value.value, max_value.value])
        .range([text_padding, width - text_padding]);
    const fixed_group = svg.append('g').attr('class', 'fixed-elements');

    fixed_group.append('text')
        .attr('x', xScale(min_value.value) - 5)
        .attr('y', yScale(0) + 5)
        .text(min_value.value.toFixed(2))
        .attr('font-size', '10px')
        .attr('text-anchor', 'end')
        .attr('fill', 'black');

    fixed_group.append('text')
        .attr('x', xScale(max_value.value) + 5)
        .attr('y', yScale(0) + 5)
        .text(max_value.value.toFixed(2))
        .attr('font-size', '10px')
        .attr('text-anchor', 'start')
        .attr('fill', 'black');

    const hist_group = svg.append('g').attr('class', 'hist-elements');
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
        .y((d) => yScale(0));
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
        .attr('cy', yScale(0))
        .attr('r', 5)
    selection_group.append('circle')
        .attr('class', 'selector-point-brush')
        .attr('id', 'hover-brush')
        .attr('cx', xScale(objective_filter.value.objective.val))
        .attr('cy', yScale(0))
        .attr('r', 20)
    // add brushing sides
    let brush_size = 10
    selection_group.append('path')
        .attr('class', "brush")
        .attr('d', d3.line()([
            [xScale(min_val), yScale(0)],
            [xScale(min_val), yScale(0) + brush_padding]]));
    selection_group.append('rect')
        .attr('class', "brush-handle")
        .attr('id', "min-brush")
        .attr('x', xScale(min_val) - brush_size / 2)
        .attr('y', yScale(0))
        .attr('width', brush_size)
        .attr('height', brush_padding);


    selection_group.append('path')
        .attr('class', "brush ")
        .attr('d', d3.line()([
            [xScale(max_val), yScale(0)],
            [xScale(max_val), yScale(0) + brush_padding]]));
    selection_group.append('rect')
        .attr('class', "brush-handle")
        .attr('id', "max-brush")
        .attr('x', xScale(max_val) - brush_size / 2)
        .attr('y', yScale(0))
        .attr('width', brush_size)
        .attr('height', brush_padding);

    if (objective_filter.value.filter.min !== undefined) {

        selection_group.append('text')
            .attr('x', xScale(min_val) + 7)
            .attr('y', yScale(0) + brush_padding / 2 + 5)
            .text(min_val.toFixed(2))
            .attr('font-size', '10px')
            .attr('fill', 'black');
    }
    if (objective_filter.value.filter.max !== undefined) {

        selection_group.append('text')
            .attr('x', xScale(max_val) - 7)
            .attr('y', yScale(0) + brush_padding / 2 + 5)
            .text(max_val.toFixed(2))
            .attr('font-size', '10px')
            .attr('text-anchor', 'end')
            .attr('fill', 'black');
    }

}
enum DraggingElement {
    None,
    HoverPoint,
    MinBrush,
    MaxBrush
}
function setupEvents() {

    const wrapper = d3.select(wrapper_ref.value)
    let clicked_element: DraggingElement = DraggingElement.None;
    function updateSelectionPos(evt: MouseEvent) {
        if (!wrapper_ref.value) return;
        if (clicked_element === null) return;
        let val = xScale.invert(d3.pointer(evt)[0])
        val = Math.min(Math.max(val, min_value.value), max_value.value);
        if (clicked_element == DraggingElement.HoverPoint) {
            objective_filter.value.objective.val = val;
        } else if (clicked_element == DraggingElement.MinBrush) {
            objective_filter.value.filter.min = Math.min(val, objective_filter.value.filter.max || max_value.value);
        } else if (clicked_element == DraggingElement.MaxBrush) {
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
        recalculateActiveBins();
        updateHistogram();
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
}
onMounted(async () => {
    initScales();
    updateGraph();
    setupEvents();
    try {
        let hist = await data_rep.client.datasets.getHistogramDatasetsSetNameDataHistGet(data_rep.set_name, { bins: 32, col_name: out_name });
        state.hist = hist.data;
    } catch (error) {
        console.error("Error fetching histogram data:", error);

    }

});
function updateHistogram() {
    if (!state.hist || !svg_ref.value) return;
    // console.log("Redrawing histogram with data:", state.hist);
    const hist_group = d3.select(svg_ref.value).select('g.hist-elements');
    const bin_width = (xScale(state.hist.bins[1]) - xScale(state.hist.bins[0])) * 0.9;
    let max_rel = d3.max(state.hist.relative) || 1;
    let relative_values = state.hist.relative.map(d => d / max_rel);


    hist_group
        .selectAll('rect')
        .data(relative_values)
        .join('rect')
        .attr('class', (d, i) => state.active_bins.includes(i) ? 'hist-bar hist-active' : 'hist-bar')
        .attr('x', (d, i) => xScale(state.hist?.bins[i] || 0) - bin_width / 2)
        .attr('y', d => yScale(d))
        .attr('width', bin_width)
        .attr('height', d => yScale(0) - yScale(d))
}
function recalculateActiveBins() {
    if (!state.hist) return;
    state.active_bins = [];
    let min_val = objective_filter.value.filter.min || min_value.value;
    let max_val = objective_filter.value.filter.max || max_value.value;
    state.hist.bins.forEach((bin_edge, idx) => {
        if (bin_edge >= min_val && bin_edge <= max_val) {
            state.active_bins.push(idx);
        }
    });
}
watch(() => state.hist, () => {
    recalculateActiveBins();
    updateHistogram();
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

.svg-selchart {
    min-width: 64px;
    min-height: 96px;
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
    fill: rgb(244, 197, 66);
    stroke: rgb(197, 189, 85);
    stroke-width: 1.5;
}

.selector-point-brush {
    fill: rgba(244, 197, 66, 0);
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

.hist-bar {
    fill: rgb(200, 200, 200);
}

.hist-bar.hist-active {
    fill: rgb(52, 166, 220);
}
</style>