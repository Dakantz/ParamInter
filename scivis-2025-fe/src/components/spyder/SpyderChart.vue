<template>
    <div ref="spider-container" class="spider-container">
        <svg ref="plot" width="10px" height="10px" class="plot-svg">>
        </svg>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, defineProps, defineModel, watch, onMounted, useTemplateRef } from 'vue';
import * as d3 from 'd3';
const dim_data = defineModel<Array<number>>({
    default: () => []
});
const { dimensions, editable, factor } = defineProps({
    dimensions: {
        type: Array as () => Array<string>,
        required: true
    },
    editable: {
        type: Boolean,
        default: false
    },
    factor: {
        type: Number,
        default: 100.0
    }
});
const plot = useTemplateRef('plot');
const spiderContainer = useTemplateRef('spider-container');


const state = reactive({
    dim_data: dim_data,
    editing_spider: false,
    edit_start_mouse: { x: 0, y: 0 },
});
function updateChart() {
    // d3.select(plot.value)
    //     .selectAll('*')
    //     .remove();
    const dim_mapped = dimensions.map((dim, i) => {
        return { name: dim, value: dim_data.value[i], idx: i };
    });
    console.log("Dimensions:", dimensions, "Data:", dim_data, "Mapped:", dim_mapped);
    if (spiderContainer.value && plot.value) {
        const width = spiderContainer.value.clientWidth;
        const height = spiderContainer.value.clientHeight;
        const svg = d3.select(plot.value)
            .attr('width', width)
            .attr('height', height);
        const radius = Math.min(width, height) / 2 - 60; // Padding
        const center = { x: width / 2, y: height / 2 };

        const angleScale = d3.scaleLinear()
            .domain([0, dim_mapped.length])
            .range([0, 2 * Math.PI]);
        svg.select('g')
            .remove();
        const g = svg.append('g')
            .attr('transform', `translate(${center.x}, ${center.y})`)
            .attr('class', 'spider-group')
        g.append('g')
            .attr('class', 'spider-lines')
            .selectAll('line')
            .data(dim_mapped)
            .join('line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', d => radius * Math.cos(d.idx * (2 * Math.PI / dim_mapped.length)))
            .attr('y2', d => radius * Math.sin(d.idx * (2 * Math.PI / dim_mapped.length)))
            .attr('stroke', 'darkgray')
            .attr('stroke-width', 1);
        const text = g.append('g')
            .attr('class', 'spider-text')
            .selectAll('text')
            .data(dim_mapped)
            .join('text')
            .attr('x', d => (radius + 10) * Math.cos(d.idx * (2 * Math.PI / dim_mapped.length)))
            .attr('y', d => (radius + 10) * Math.sin(d.idx * (2 * Math.PI / dim_mapped.length)))
            .attr('text-anchor', d => {
                let angle = d.idx * (2 * Math.PI / dim_mapped.length);
                if (angle > Math.PI / 2 && angle < 3 * Math.PI / 2) {
                    return 'end';
                } else {
                    return 'start';
                }
            })
            .text(d => d.name)
            .attr('font-size', '6px')
            .attr('fill', 'black')
            .attr('class', 'spider-text-item')
        const spider = g
            .selectAll('path')
            .data([dim_mapped])
            .join('path')
            .attr('d', d => {
                let pieces = d.map((v, i) => {
                    let angle = (i / d.length) * 2 * Math.PI;
                    let x = Math.cos(angle) * radius * (v.value / factor);
                    let y = Math.sin(angle) * radius * (v.value / factor);
                    return { x, y };
                });
                let path = d3.path();
                pieces.forEach((piece, i) => {
                    if (i === 0) {
                        path.moveTo(piece.x, piece.y);
                    } else {
                        path.lineTo(piece.x, piece.y);
                    }
                });
                path.closePath();
                return path.toString();
            })
            // .attr('class', 'spider-path')
            .attr('class', () => {
                return editable ? 'spider-path' : 'fixed-spider';
            })
        svg
            .on('mousedown', (event: MouseEvent, d) => {
                if (!editable) return;
                state.editing_spider = true;
                state.edit_start_mouse = { x: event.clientX, y: event.clientY };
                console.log("Editing spider started at:", state.edit_start_mouse);
            })
            .on('mousemove', (event: MouseEvent) => {
                if (state.editing_spider) {
                    // coordinate relative to the center of the spider
                    const rect = plot.value?.getBoundingClientRect();
                    if (!rect) return;
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    const relX = event.clientX - centerX;
                    const relY = event.clientY - centerY;


                    let angle = Math.atan2(relY, relX);
                    if (angle < 0) {
                        angle += 2 * Math.PI; // Normalize angle to [0, 2π]
                    }
                    const radius_mouse = Math.sqrt(relX * relX + relY * relY) / radius;

                    let closest_dim = dim_mapped.find((d) => {
                        const dim_angle = (d.idx / dim_mapped.length) * 2 * Math.PI;
                        const angle_diff = Math.abs(angle - dim_angle);
                        return angle_diff < Math.PI / dim_mapped.length;
                    });
                    if (!closest_dim) {
                        console.warn("No closest dimension found for angle:", angle);
                        return;
                    }
                    const idx = closest_dim.idx;

                    console.log("Mouse moved to:", relX, relY, "Angle:", angle,
                        "Radius:", radius_mouse, "Closest dimension:", closest_dim.name);

                    const newValue = Math.max(0, Math.min(1, radius_mouse));
                    dim_data.value[idx] = newValue;
                    //normalize the other values
                    const sum = dim_data.value.reduce((a, b) => a + b, 0);
                    dim_data.value = dim_data.value.map(v => v / sum);
                    updateChart();
                }
            })
            .on('mouseup', () => {
                state.editing_spider = false;
            });
        ;
        // console.log("Dims:", dim_mapped);
        // svg.data(dim_mapped)
        //     .join('g')
        //     .attr('transform', `translate(${center.x}, ${center.y})`)
        //     .append('line')
        //     .attr('x1', 0)
        //     .attr('y1', 0)
        //     .attr('x2', d => radius * Math.cos(angleScale(d.idx)))
        //     .attr('y2', d => radius * Math.sin(angleScale(d.idx)))
        //     .attr('stroke', 'black');
    }

}
onMounted(() => {
    updateChart();
});
watch(() => dimensions, () => {
    updateChart();
}, { immediate: true });
watch(() => dim_data, () => {
    // console.log("Dimension data changed:", dim_data.value);
    updateChart();
}, {deep: true, immediate: true });
const cursor_style = ref('default');
watch(() => editable, (editing) => {
    if (editing) {
        cursor_style.value = 'move';
    } else {
        cursor_style.value = 'default';
    }
}, { immediate: true });
</script>

<style>
.spider-container {
    width: 100%;
    height: 100%;
    min-height: 200px;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: v-bind(cursor_style);
}

.spider-path {
    fill: rgba(173, 216, 230, 0.541);
    stroke: darkblue;
    stroke-width: 1px;
}

.spider-text-item {
    pointer-events: none;
}

.plot-svg {
    width: 100%;
    height: 100%;
}

.fixed-spider {
    fill: rgba(128, 255, 0, 0.5);
    stroke: rgba(58, 128, 0, 0.72);
    stroke-width: 1px;
}

</style>