<template>
    <div ref="loading-container" class="loading-container">
        <svg ref="plot" :width="size + 'px'" :height="size + 'px'">
        </svg>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef, computed } from 'vue';
import * as d3 from 'd3';
import { inverseSpider, randomNormal, reSpider } from '../helpers/utils';
import { DataDescription } from '../../api/Api';
import { DataRepository } from '../../proc/data-store';
const dim_data = defineModel<Array<number>>({
    default: () => []
});
const { steps, color, indefinite, size } = defineProps({
    steps: {
        type: Number,
        default: 6
    },
    color: {
        type: String,
        default: '#fbc170'
    },
    indefinite: {
        type: Boolean,
        default: true
    },
    size: {
        type: Number,
        default: 128
    }
});
const plot = useTemplateRef('plot');
const loadingContainer = useTemplateRef('loading-container');

const dimensions = ref<string[]>([]);

const state = reactive({
    progress: 0,
});



function updateChart() {
    // d3.select(plot.value)
    //     .selectAll('*')
    //     .remove();
    if (loadingContainer.value && plot.value) {
        const width = loadingContainer.value.clientWidth;
        const height = loadingContainer.value.clientHeight;
        const svg = d3.select(plot.value)
            .attr('width', width)
            .attr('height', height);
        const padding = 4;
        const radius = Math.min(width, height) / 2 - padding; // Padding
        const center = { x: width / 2, y: height / 2 };

        let values = Array.from({ length: steps }, (_, i) => 0);
        values = values.map((_, i) => {
            return 0.3 + randomNormal() * 0.5;
        });
        let min = d3.min(values) || 0;
        let max = d3.max(values) || 1;
        const dims = values.map((dim, i) => {

            let rescale_val = Math.max(0.2, Math.min(1, dim)) / max;
            let angle = (i / values.length) * 2 * Math.PI;
            let x = Math.cos(angle) * radius * (rescale_val);
            let y = Math.sin(angle) * radius * (rescale_val);
            return {
                idx: i,
                val: dim,
                x,
                y,
                rescale_val,
            }
        });

        const angleScale = d3.scaleLinear()
            .domain([0, dims.length])
            .range([0, 2 * Math.PI]);
        svg.select('g')
            .remove();

        const g = svg.append('g')
            .attr('transform', `translate(${center.x}, ${center.y})`)
            .attr('class', 'spider-group')
        const time = 4
        g.append('g')
            .attr('class', 'spider-lines')
            .selectAll('line')
            .data(dims)
            .join('line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', d => radius * Math.cos(d.idx * (2 * Math.PI / dims.length)))
            .attr('y2', d => radius * Math.sin(d.idx * (2 * Math.PI / dims.length)))
            .attr('stroke', 'darkgray')
            .attr('stroke-width', 1);
        const spider = g
            .selectAll('path.spider-path')
            .data(dims)
            .join('path')
            .attr('id', (d) => `spider-path-${d.idx}`)
            .attr('class', 'spider-path')
            .style('animation', d => {
                return indefinite ? `${time}s cubic-bezier(0.7, 0, 0.3, 1) infinite spider_animation` : 'none'
            })
            .style('animation-delay', (d, i) => {
                let offset = i * (time / dims.length) - time
                return `${offset}s`;
            })
            .attr('d', (d, i) => {
                let path = d3.path();
                path.moveTo(0, 0);
                path.lineTo(d.x, d.y);
                let next_idx = (i + 1) % dims.length;
                let next_point = dims[next_idx];
                path.lineTo(next_point.x, next_point.y);
                path.lineTo(0, 0);
                path.closePath();
                return path.toString();
            })

    }

}
onMounted(() => {
    updateChart();
    if (indefinite) {

    }
});
watch(() => steps, () => {
    updateChart();
}, { immediate: true });
const light_color = computed(() => {
    return d3.color(color)?.brighter(0.5).toString() || color;
});
const dark_color = computed(() => {
    return d3.color(color)?.darker(1).toString() || color;
});

</script>

<style>
.loading-container {
    width: v-bind(size) + 'px';
    height: v-bind(size) + 'px';
    display: flex;
    justify-content: center;
    align-items: center;
}

@keyframes spider_animation {
    0% {
        opacity: 0;
        fill: v-bind(light_color);
        stroke: v-bind(dark_color);
    }

    50% {
        opacity: 0.9;
        fill: v-bind(light_color);
        stroke: v-bind(dark_color);
    }

    100% {
        opacity: 0;
        fill: v-bind(light_color);
        stroke: v-bind(dark_color);
    }
}
</style>