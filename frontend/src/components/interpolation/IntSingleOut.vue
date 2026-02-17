<template>
    <div class="single-outview" @mouseenter="emit('hover', out_idx)">
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
import { colorForIndex, DataRepository } from '../../proc/data-store';
import * as d3 from 'd3';
import { InterpolationResult } from '../../api/Api';
import { inverseNormalCdf, outValues } from '../helpers/utils';
import { HoveredInterpolation } from '../types';

const emit = defineEmits<{
    (e: 'hover', index: number): void;
    (e: 'select', idx: HoveredInterpolation): void;
}>();
const hovered_index = defineModel<HoveredInterpolation>({
    type: Object as () => HoveredInterpolation,
    default: { interpolation_idx: -1, index_in_interpolation: -1 }
});
const { int_results, out_idx, out_name, data_rep, uncertainty_steps } = defineProps({
    int_results: {
        type: Object as () => InterpolationResult[],
        required: true
    },
    out_idx: {
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
    uncertainty_steps: {
        type: Number,
        required: false,
        default: 4
    }

})
const out_values = computed(() => {
    return int_results.map(int => outValues(
        int,
        out_idx
    ));
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
    if (hovered_index.value.interpolation_idx >= 0
        && hovered_index.value.interpolation_idx < out_values.value.length
        && hovered_index.value.index_in_interpolation >= 0
        && hovered_index.value.index_in_interpolation < out_values.value[hovered_index.value.interpolation_idx].length) {
        return `- ${out_values.value[hovered_index.value.interpolation_idx][hovered_index.value.index_in_interpolation].toFixed(2)}`;
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

    const width = wrapper_ref.value.clientWidth - 5;
    const height = wrapper_ref.value.clientHeight - 5;
    // console.log("Updating graph with width:", width, "height:", height);
    const svg = d3.select(svg_ref.value)
        .attr('width', width)
        .attr('height', height);


    xScale = d3.scaleLinear()
        .domain([0, out_values.value[0].length - 1])
        .range([0, width]);

    yScale = d3.scaleLinear()
        .domain([min_value.value, max_value.value])
        .range([height, 0]);
    svg.selectAll('.output-line')
        .data(out_values.value)
        .join('path')
        .attr('class', 'output-line')
        .attr('stroke', (d, i) => colorForIndex(i, 0))
        .attr('d', d3.line<number>()
            .x((d, i) => xScale(i))
            .y(d => yScale(d))
        );
    if (display_ucq.value) {
        let ucq_steps = Array.from({ length: uncertainty_steps }).map((_, i) => {
            let q = 0.2 * i / uncertainty_steps
            let qs = [
                0.6 + q,
                0.4 - q,
            ]

            return {
                ucq_series: uncertainties.value.map((ucq, i) => {
                    let qs_results = qs.map(q => {
                        let values = out_values.value[i];
                        let uncertainties_value = uncertainties.value[i];
                        let ivs = uncertainties_value?.map((u, i) =>
                            inverseNormalCdf(q, values[i], u)) || values.map(_ => 0);

                        return {
                            inverse_quantiles: ivs,
                            uncertainties: uncertainties_value,
                            values: values,
                            q,
                            level: i / uncertainty_steps
                        }
                    })
                    return {
                        upper_qant: qs_results[0].inverse_quantiles,
                        lower_qant: qs_results[1].inverse_quantiles,
                        ucq: qs_results[0].uncertainties,
                        values: qs_results[0].values,
                    }
                }),
                q: q + 0.6,
                level: i / uncertainty_steps
            }
        })
        console.log("UCQ steps:", ucq_steps, uncertainties.value);
        ucq_steps.forEach((step, step_idx) => {
            svg.selectAll(`.ucq-line#step_${step_idx}`)
                .data(step.ucq_series)
                .join('path')
                .attr('class', 'ucq-line')
                .attr('id', `step_${step_idx}`)
                .attr('stroke', (d, i) => colorForIndex(i, 0))
                .attr('fill', (d, i) => colorForIndex(i, 0))
                .attr('opacity', (d, i) => 0.3 * (1 - step.level))
                .attr('d', (d) => {
                    let path = d3.path();
                    d.upper_qant.forEach((v, idx) => {
                        let x = xScale(idx);
                        let y = yScale(d.upper_qant[idx]);
                        if (idx === 0) {
                            path.moveTo(x, y);
                        } else {
                            path.lineTo(x, y);
                        }
                    });
                    d.lower_qant.slice().reverse().forEach((v, idx) => {
                        let idx_reversed = d.lower_qant.length - 1 - idx;
                        let x = xScale(idx_reversed);
                        let y = yScale(d.lower_qant[idx_reversed]);
                        path.lineTo(x, y);
                    });
                    path.closePath();
                    return path.toString();
                });
        });
    }
}
watch(() => hovered_index.value, (idx) => {
    const svg = d3.select(svg_ref.value);
    if (out_values.value.length > 0 && idx.interpolation_idx >= 0 && idx.interpolation_idx < out_values.value[0].length) {
        // Highlight the hovered point
        svg.selectAll('.hover-point').remove(); // Remove previous hover point
        svg.append('circle')
            .attr('class', 'hover-point')
            .attr('fill', colorForIndex(idx.interpolation_idx, 1))
            .attr('stroke', colorForIndex(idx.interpolation_idx, -4))
            .attr('cx', xScale(idx.index_in_interpolation))
            .attr('cy', yScale(out_values.value[idx.interpolation_idx][idx.index_in_interpolation]))
            .attr('r', 5)
    }else {
        // Remove hover point if no valid index
        svg.selectAll('.hover-point').remove();
    }
}, { immediate: true, deep: true });
function idxFromHover(evt: MouseEvent): HoveredInterpolation {
    if (!wrapper_ref.value) return { interpolation_idx: -1, index_in_interpolation: -1 };
    const width = wrapper_ref.value.clientWidth;
    const hoveredIndex = Math.floor(xScale.invert(d3.pointer(evt)[0]));

    const value_hovered = yScale.invert(d3.pointer(evt)[1]);
    const values_at_idx = out_values.value.map(int => int[hoveredIndex]);
    const distances = values_at_idx.map(v => Math.abs(v - value_hovered));
    let closest_int_idx = 0;
    for (let i = 1; i < distances.length; i++) {
        if (distances[i] < distances[closest_int_idx]) {
            closest_int_idx = i;
        }
    }
    return {
        interpolation_idx: closest_int_idx,
        index_in_interpolation: hoveredIndex
    };
}
onMounted(() => {
    const wrapper = d3.select(wrapper_ref.value)
    wrapper.on('mousemove', (evt) => {
        let hoveredIndexData = idxFromHover(evt);
        hovered_index.value.index_in_interpolation = hoveredIndexData.index_in_interpolation;
        hovered_index.value.interpolation_idx = hoveredIndexData.interpolation_idx;
        // emit('hover', hoveredIndexData);
    }).on('click', (evt) => {
        let hoveredIndexData = idxFromHover(evt);
        hovered_index.value.index_in_interpolation = hoveredIndexData.index_in_interpolation;
        hovered_index.value.interpolation_idx = hoveredIndexData.interpolation_idx;

        emit('select', hoveredIndexData);
    });

    updateGraph();
});
watch(() => out_values.value, () => {
    updateGraph();
}, { immediate: true });
const uncertainties = computed(() => {
    return int_results.map(int => int.uncertainties ? int.uncertainties.map((uq) => uq[out_idx]) : []);
});
const display_ucq = computed(() => {
    return int_results.reduce((has_ucq, int) => {
        return has_ucq || int.uncertainties != undefined;
    }, true);
})
</script>
<style>
.single-outview {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 8vw;
    max-width: 128px;
    padding: 5px;
}

.single-outview:hover {
    background-color: #f0f0f0;
}

.out-name {
    font-weight: bold;
    margin-bottom: 2px;
    max-width: 100%;
    width: 100%;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
    text-align: start;
}

.out-value {
    display: flex;
    flex-direction: row;
    align-items: center;

    max-width: 100%;
    width: 100%;
}


.svg-outchart {
    min-width: 64px;
    min-height: 64px;
}

.output-line {
    fill: none;
    stroke-width: 1.5;
}

.hover-point {
    fill: rgb(132, 208, 82);
    stroke: rgb(58, 173, 100);
    stroke-width: 1.5;
}
</style>