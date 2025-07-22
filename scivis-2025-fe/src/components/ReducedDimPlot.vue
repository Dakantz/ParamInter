<template>
    <div class="reduced-dim-plot">
        <svg width="420" height="420" xmlns="http://www.w3.org/2000/svg">
            <g transform="scale(420,420)">
                <g ref="plot"></g>
                <g ref="spyders"></g>
            </g>

        </svg>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineModel, watch } from 'vue';
import { Embeddings, LoadedDataPoints } from '../proc/types';
import * as d3 from 'd3';
import { ModelRef } from 'vue';
import { PlotSelection } from './types';
const { embedded_data, full_data } = defineProps({
    embedded_data: {
        type: Embeddings,
        required: true
    },
    full_data: {
        type: LoadedDataPoints,
        required: true
    }
});

const selection: ModelRef<PlotSelection> = defineModel({
    type: PlotSelection,
    default: () => new PlotSelection()
});

const ui_params = reactive({
    point_size: 2,
    spyder_size: 25
});

const plot = ref(null);
const spyders = ref(null);

watch(() => embedded_data, (newData) => {
    if (plot.value) {
        d3.
            select(plot.value)
            .selectAll('circle')
            .data(newData.embeddings)
            .enter()
            .append('circle')
            .attr('cx', d => d[0])
            .attr('cy', d => d[1])
            .attr('r', ui_params.point_size)
            .style('fill', 'black').
            on('click', (event, d) => {
                const index = newData.embeddings.indexOf(d);
                if (index !== -1) {
                    if (selection.value.selected_indices.includes(index)) {
                        selection.value.removeIndex(index);
                    } else {
                        selection.value.addIndex(index);
                    }
                }
            }).on('mouseover', (event, d) => {
                const index = newData.embeddings.indexOf(d);
                if (index !== -1) {
                    selection.value.hovered_index = index;
                }
            }).on('mouseout', () => {
                selection.value.hovered_index = null;
            });
    }
}, { immediate: true });

watch(() => selection.value.hovered_index, (newHoverIndex) => {
    if (plot.value) {
        d3.select(plot.value)
            .selectAll('circle')
            .style('fill', (d, i) => i === newHoverIndex ? 'red' : 'black');
    }
}, { immediate: true });

watch(() => selection.value.selected_indices, (newSelection) => {

    if (spyders.value) {
        d3.select(spyders.value)
            .selectAll('g')
            .data(newSelection)
            .join('g')
            .attr('transform', (index) => `translate(${embedded_data.embeddings[index][0]}, ${embedded_data.embeddings[index][1]})`)
            .append('path')
            .attr('d', (d) => {
                let input_data = full_data.inputs[d];
                let pieces = input_data.map((value, i) => {
                    let angle = (i / input_data.length) * 2 * Math.PI;
                    let x = Math.cos(angle) * ui_params.spyder_size * value;
                    let y = Math.sin(angle) * ui_params.spyder_size * value;
                    return { x, y };
                });
                let path = d3.path();
                path.moveTo(0, 0);
                pieces.forEach((piece) => path.lineTo(piece.x, piece.y));
                return path.toString();
            })

    }
}, { immediate: true, deep: true });
</script>

<style scoped>
.reduced-dim-plot {
    min-width: 420px;
    max-width: 420px;

    min-height: 420px;
    max-height: 420px;
    display: flex;
}
</style>
