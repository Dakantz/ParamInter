<template>
    <div ref="spider-container" class="spider-container">
        <svg ref="plot" width="10px" height="10px" class="plot-svg">>
        </svg>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef, computed } from 'vue';
import * as d3 from 'd3';
import { inverseSpider, reSpider } from '../helpers/utils';
import { DataDescription } from '../../api/Api';
import { DataRepository } from '../../proc/types';
const dim_data = defineModel<Array<number>>({
    default: () => []
});
const { editable, factor, sensitivities, rep } = defineProps({
    rep: {
        type: Object as () => DataRepository,
        default: () => (null)
    },
    editable: {
        type: Boolean,
        default: false
    },
    factor: {
        type: Number,
        default: 1
    },
    sensitivities: {
        type: Array as () => Array<number>,
        default: () => []
    }
});
const plot = useTemplateRef('plot');
const spiderContainer = useTemplateRef('spider-container');

const dimensions = ref<string[]>([]);
watch(() => rep, (newRep) => {
    if (newRep && newRep.description) {
        if (dimensions.value.length === 0) {
            // initialize dim_data
            dimensions.value = [...newRep.description.input_cols];
            updateChart();
        }

    }
}, { immediate: true, deep: true });

const state = reactive({
    dim_data: dim_data,
    editing_spider: false,
    edit_start_mouse: { x: 0, y: 0 },
});
function updateChart() {
    // d3.select(plot.value)
    //     .selectAll('*')
    //     .remove();
    const dim_mapped = dimensions.value.map((dim, i) => {

        let min = rep && rep.description ? rep.description.min_values[dim] : 0;
        let max = rep && rep.description ? rep.description.max_values[dim] : 1;
        return {
            name: dim,
            value: dim_data.value[i],
            rescale_val: reSpider(dim_data.value[i], min, max),
            idx: i,
            angle: -1,
            min,
            max,
        };
    });
    // console.log("Dimensions:", dimensions, "Data:", dim_data, "Mapped:", dim_mapped);
    if (spiderContainer.value && plot.value) {
        const width = spiderContainer.value.clientWidth;
        const height = spiderContainer.value.clientHeight;
        const svg = d3.select(plot.value)
            .attr('width', width)
            .attr('height', height);
        const radius = Math.min(width, height) / 2 - 20; // Padding
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
            .selectAll('g.spider-text-item')
            .data(dim_mapped)
            .join('g')
            .attr('transform', d => {
                let x = (radius + 5) * Math.cos(d.idx * (2 * Math.PI / dim_mapped.length))
                let y = (radius + 5) * Math.sin(d.idx * (2 * Math.PI / dim_mapped.length))
                let angle = d.idx * (360 / dim_mapped.length) + 90;
                if (angle > 180) {
                    angle -= 360; // Normalize angle to [-180, 180]
                }
                if (angle < -90) {
                    angle += 180; // Adjust for left side text
                }
                if (angle > 90) {
                    angle -= 180; // Adjust for right side text
                }
                d.angle = angle; // Store angle for reference
                return `translate(${x}, ${y}), rotate(${angle})`;
            })
            .append('text')
            .attr('x', 0)
            .attr('y', 0)
            .attr('text-anchor', d => {
                return 'middle'; // 'start' or 'end' based on position
                //rotate the text based on the angle
            })
            .text(d => d.name)
            .attr('font-size', '10px')
            .attr('fill', 'black')
            .attr('class', 'spider-text-item')
        const spider = g
            .selectAll('path.spider-path')
            .data([dim_mapped])
            .join('path')
            .attr('class', 'spider-path')
            .attr('d', d => {
                let pieces = d.map((v, i) => {
                    let angle = (i / d.length) * 2 * Math.PI;
                    let x = Math.cos(angle) * radius * (v.rescale_val / factor);
                    let y = Math.sin(angle) * radius * (v.rescale_val / factor);
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
        const filtered_sensitivities = sensitivities.map((s, i) => {
            return { sense: s, idx: i, val: dim_mapped[i].rescale_val, name: dim_mapped[i].name, effective_length: radius * (s / (factor)) };
        }).filter(d => Math.abs(d.sense) > 0.2)
        // console.log("Filtered sensitivities:", filtered_sensitivities);
        const sensitivity = g
            .selectAll('path.sensitivity')
            .data(filtered_sensitivities) // filter out very small sensitivities
            // .filter(d => d.effective_length > 0.01) // filter out very small sensitivities
            .join('path')
            .attr('d', d => {
                // draw an arrow depending on the sensitivity value
                let angle = (d.idx / dim_mapped.length) * 2 * Math.PI;
                let base_x = Math.cos(angle) * radius * (d.val / factor);
                let base_y = Math.sin(angle) * radius * (d.val / factor);

                let to_x = base_x + Math.cos(angle) * d.effective_length;
                let to_y = base_y + Math.sin(angle) * d.effective_length;

                let path = d3.path();
                path.moveTo(base_x, base_y);
                path.lineTo(to_x, to_y);
                return path.toString();
            })
            .attr('marker-end', d => {
                return d.sense > 0 ? 'url(#arrow-pos)' : 'url(#arrow-neg)';
            })
            .attr('class', d => {
                return d.sense > 0 ? 'sensitivity_pos sensitivity' : 'sensitivity_neg sensitivity';
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

                    // console.log("Mouse moved to:", relX, relY, "Angle:", angle,
                    // "Radius:", radius_mouse, "Closest dimension:", closest_dim.name);
                    // clamp the radius to [0, 1]

                    let newValue = Math.max(0, Math.min(1, radius_mouse));
                    newValue = inverseSpider(newValue, closest_dim.min, closest_dim.max);
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

    const markerBoxWidth = 5;
    const markerBoxHeight = 5;
    const refX = markerBoxWidth / 2;
    const refY = markerBoxHeight / 2;
    const arrowPoints = [
        [0, 0],
        [markerBoxWidth, markerBoxHeight / 2],
        [0, markerBoxHeight],
        [markerBoxWidth / 2, markerBoxHeight / 2]
    ];
    d3.select(plot.value)
        .append('defs')
        .append('marker')
        .attr('id', 'arrow-pos')
        .attr('viewBox', [0, 0, markerBoxWidth, markerBoxHeight])
        .attr('refX', refX)
        .attr('refY', refY)
        .attr('markerWidth', markerBoxWidth)
        .attr('markerHeight', markerBoxHeight)
        .attr('orient', 'auto-start-reverse')
        .append('path')
        .attr('d', d3.line()(arrowPoints as [number, number][]))
        .attr('class', 'sensitivity_pos');
    d3.select(plot.value)
        .append('defs')
        .append('marker')
        .attr('id', 'arrow-neg')
        .attr('viewBox', [0, 0, markerBoxWidth, markerBoxHeight])
        .attr('refX', refX)
        .attr('refY', refY)
        .attr('markerWidth', markerBoxWidth)
        .attr('markerHeight', markerBoxHeight)
        .attr('orient', 'auto-start-reverse')
        .append('path')
        .attr('d', d3.line()(arrowPoints as [number, number][]))
        .attr('class', 'sensitivity_neg');

    updateChart();
});
watch(() => dimensions, () => {
    updateChart();
}, { immediate: true });
watch(() => dim_data, () => {
    // console.log("Dimension data changed:", dim_data.value);
    updateChart();
}, { deep: true, immediate: true });
const cursor_style = ref('default');
watch(() => editable, (editing) => {
    if (editing) {
        cursor_style.value = 'move';
    } else {
        cursor_style.value = 'default';
    }
}, { immediate: true });


watch(() => sensitivities, (sense) => {
    if (sense.length > 0) {
        // console.log("Updating sensitivities:", sense);
        updateChart();
    }
}, { immediate: true });
</script>

<style>
.spider-container {
    width: 100%;
    height: 100%;
    min-width: 200px;
    min-height: 20vw;
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
    /* height: 100%; */
}

.fixed-spider {
    fill: rgba(128, 255, 0, 0.5);
    stroke: rgba(58, 128, 0, 0.72);
    stroke-width: 1px;
}

.sensitivity {
    stroke-width: 3px;
}

.sensitivity_pos {
    fill: rgba(7, 107, 32, 0.642);
    stroke: rgba(7, 107, 32, 0.642);
}

.sensitivity_neg {
    fill: rgba(40, 6, 151, 0.608);
    stroke: rgba(71, 6, 151, 0.608);
}
</style>