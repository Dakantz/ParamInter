<template>
    <g ref="spider-container">
    </g>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef, computed } from 'vue';
import * as d3 from 'd3';
import { inverseSpider, reSpider } from '../helpers/utils';
import { DataDescription } from '../../api/Api';
import { DataRepository } from '../../proc/data-store';
const dim_data = defineModel<Array<number>>({
    default: () => []
});
const { editable, factor, sensitivities, rep, width, height, color, show_labels, sensitivity_scale } = defineProps({
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
    },
    width: {
        type: Number,
        default: 20
    },
    height: {
        type: Number,
        default: 20
    },
    color: {
        type: String,
        default: 'rgba(58, 128, 0, 0.72)'
    },
    show_labels: {
        type: Boolean,
        default: true
    },
    sensitivity_scale: {
        type: Number,
        default: 1
    }
});
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
    d3.select(spiderContainer.value)
        .selectAll('*')
        .remove();
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
    const radius = Math.min(width, height) / 2;
    if (spiderContainer.value) {

        const g = d3.select(spiderContainer.value).append('g')
            .attr('transform', `translate(${width / 2}, ${height / 2})`)
            .attr('class', 'spider-group')
        // for interactivity - catch events!
        g.append('circle')
            .attr('cx', 0)
            .attr('cy', 0)
            .attr('r', radius)
            .attr('fill', 'white')
            .attr('fill-opacity', 0.0)
            .attr('stroke', 'none')
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
        if (show_labels) {
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
        }
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
                return 'spider-path';
            })
        const filtered_sensitivities = sensitivities.map((s, i) => {
            return {
                sense: s, idx: i, val: dim_mapped[i].rescale_val, name: dim_mapped[i].name, effective_length: radius * s * sensitivity_scale
            };
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

        g
            .on('mousedown', (event: MouseEvent, d) => {
                if (!editable) return;
                state.editing_spider = true;
                state.edit_start_mouse = { x: event.clientX, y: event.clientY };
                console.log("Editing spider started at:", state.edit_start_mouse);
            })
            .on('mousemove', (event: MouseEvent) => {
                if (state.editing_spider) {
                    // coordinate relative to the center of the spider
                    const rect = spiderContainer.value?.getBoundingClientRect();
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
                    if (rep && rep.description && rep.description.inputs_constrained) {
                        let min_values = rep.description.min_values;
                        let max_values = rep.description.max_values;
                        let normed_values = dim_data.value.map((v, i) => {
                            let dim_name = dimensions.value[i];
                            return (v - min_values[dim_name]) / (max_values[dim_name] - min_values[dim_name]);
                        });
                        const current_sum = normed_values.reduce((a, b) => a + b, 0);
                        const rescaled_values = normed_values.map((v, i) => {
                            return v / current_sum;
                        });
                        dim_data.value = rescaled_values.map((v, i) => {
                            let dim_name = dimensions.value[i];
                            return v * (max_values[dim_name] - min_values[dim_name]) + min_values[dim_name];
                        });
                    } else {
                        dim_data.value = [...dim_data.value];
                    }
                    updateChart();
                }
            })
            .on('mouseup', () => {
                state.editing_spider = false;
                console.log("Editing spider ended.");
            }).on('mouseleave', () => {
                state.editing_spider = false;
                console.log("Editing spider ended (mouseleave).");
            })
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
}, { deep: true, immediate: true });
watch(() => height, () => {
    updateChart();
}, { immediate: true });
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

const light_color = computed(() => {
    if (editable) {
        return "rgba(173, 216, 230, 0.541)"
    }
    if (!editable) {
        let col = d3.color(color);
        if (!col) return color;
        col.opacity = 0.6;
        return col.brighter(2).toString();
    }
});
const dark_color = computed(() => {
    if (editable) {
        return "darkblue"
    }
    if (!editable) {
        let col = d3.color(color);
        if (!col) return color;
        col.opacity = 0.6;
        return col.toString();
    }
});
const sensitivities_marker_size = computed(() => {
    return `${Math.min(width, height) / 60}px`;
});
</script>

<style>
.spider-path {
    fill: v-bind(light_color);
    stroke: v-bind(dark_color);
    stroke-width: 1px;
}

.spider-text-item {
    pointer-events: none;
}

.sensitivity {
    stroke-width: v-bind(sensitivities_marker_size);
}

.sensitivity_pos {
    fill: rgba(7, 107, 32, 0.911);
    stroke: rgba(7, 107, 32, 0.911);
}

.sensitivity_neg {
    fill: rgba(40, 6, 151, 0.911);
    stroke: rgba(71, 6, 151, 0.911);
}
</style>