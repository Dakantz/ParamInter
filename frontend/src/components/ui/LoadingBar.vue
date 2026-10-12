<template>
    <div ref="container" class="loading-bar-container">
        <svg ref="plot" class="loading-bar-svg"></svg>
        <div v-if="label" class="loading-bar-label">{{ label }}</div>
    </div>
</template>

<script lang="ts" setup>
import { watch, onMounted, onBeforeUnmount, useTemplateRef } from 'vue';
import * as d3 from 'd3';

// Determinate progress bar (0..1) drawn with a single d3 rect that's scaled/animated to the
// current progress - used for iterative/batched loads (see ScatterplotMatrix.vue) where a
// spinner can't show how far along the load actually is.
const { progress, height, color, track_color, label } = defineProps({
    // 0..1. Values outside that range are clamped.
    progress: {
        type: Number,
        default: 0,
    },
    height: {
        type: Number,
        default: 6,
    },
    color: {
        type: String,
        default: '#fbc170',
    },
    track_color: {
        type: String,
        default: '#eee',
    },
    label: {
        type: String,
        default: '',
    },
});

const container = useTemplateRef('container');
const plot = useTemplateRef('plot');

function redraw() {
    if (!container.value || !plot.value) return;
    const width = container.value.clientWidth;
    const svg = d3.select(plot.value)
        .attr('width', width)
        .attr('height', height);

    const clamped = Math.max(0, Math.min(1, progress));
    const scale = d3.scaleLinear().domain([0, 1]).range([0, width]);

    svg.selectAll<SVGRectElement, unknown>('rect.loading-bar-track')
        .data([null])
        .join('rect')
        .attr('class', 'loading-bar-track')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', width)
        .attr('height', height)
        .attr('rx', height / 2)
        .attr('fill', track_color);

    svg.selectAll<SVGRectElement, unknown>('rect.loading-bar-fill')
        .data([null])
        .join('rect')
        .attr('class', 'loading-bar-fill')
        .attr('x', 0)
        .attr('y', 0)
        .attr('height', height)
        .attr('rx', height / 2)
        .attr('fill', color)
        .transition()
        .duration(200)
        .attr('width', scale(clamped));
}

let resize_observer: ResizeObserver | null = null;
onMounted(() => {
    redraw();
    if (container.value) {
        resize_observer = new ResizeObserver(() => redraw());
        resize_observer.observe(container.value);
    }
});
onBeforeUnmount(() => {
    resize_observer?.disconnect();
});

watch(() => progress, redraw);
</script>

<style scoped>
.loading-bar-container {
    width: 100%;
}

.loading-bar-svg {
    display: block;
    width: 100%;
}

.loading-bar-label {
    margin-top: 4px;
    font-size: 11px;
    color: #666;
    text-align: center;
}
</style>
