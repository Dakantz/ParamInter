<template>
    <div class="inputs_interpolation_sliders" ref="wrapper_ref">
        <svg ref="svg_ref" width="100px" height="100px">
            <g class="spyder_ends" v-for="(end, i) in end_points" :key="i"
                :transform="`translate(${endsPosition(i).x}, ${endsPosition(i).y})`">
                <SpyderChart_Base :rep="data_rep" v-model="end_points[i]" :editable="false" :height="spyder_size"
                    :show_labels="false" :width="spyder_size" :color="colorForIndex(display_intersection_index)" />
            </g>
            <g class="interpolation_slider">
                <!-- <text>Hello</text> -->
            </g>
            <g class="spyder_interpolation"
                :transform="`translate(${interpolationPosition.x}, ${interpolationPosition.y})`">
                <SpyderChart_Base v-if="hovered_input" :rep="data_rep" v-model="hovered_input"
                    :sensitivities="state.displayed_sensitivities" :editable="false" :show_labels="false"
                    :height="spyder_size * hover_scale" :width="spyder_size * hover_scale"
                    :color="colorForIndex(display_intersection_index)" :sensitivity_scale="0.5" />
            </g>

        </svg>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef, computed } from 'vue';
import * as d3 from 'd3';
import { colorForIndex, DataRepository, LoadedDataPoints } from '../../proc/data-store';
import SpyderChart from '../spyder/SpyderChart.vue';
import { DataPoint, InterpolationResult } from '../../api/Api';
import { HoveredInterpolation, PlotSelection } from '../types';
import IntOverview from '../interpolation/IntOverview.vue';
import { setupMarkers } from '../helpers/utils';
import SpyderChart_Base from '../spyder/SpyderChart_Base.vue';

const svg_ref = useTemplateRef('svg_ref');
const wrapper_ref = useTemplateRef('wrapper_ref');

onMounted(() => {
    console.log("Interpolation component mounted");
});
const selection = defineModel<PlotSelection>(
    {
        required: true,
    }
);
const { data_rep, interpolations, spyder_size, padding, hovered_output } = defineProps({
    data_rep: {
        type: Object as () => DataRepository,
        required: true
    },
    interpolations: {
        type: Object as () => InterpolationResult[] | null,
        default: () => (null)
    },
    spyder_size: {
        type: Number,
        default: 75
    },
    padding: {
        type: Number,
        default: 20
    },
    hovered_output: {
        type: String,
        default: ""
    }


});

const state = reactive({
    displayed_sensitivities: [] as number[],
})
const hover_scale = 0.8;

let yScale = d3.scaleLinear()
    .domain([0, 1])
    .range([0, 32]);
let xScale = d3.scaleLinear()
    .domain([0, 1])
    .range([0, 64]);

function setUpLayout() {
    if (!svg_ref.value || !wrapper_ref.value) return;
    const width = wrapper_ref.value.clientWidth - 5;
    const height = wrapper_ref.value.clientHeight;

    // console.log("Updating graph with width:", width, "height:", height);
    d3.select(svg_ref.value)
        .attr("width", width)
        .attr("height", height);

    const svg = d3.select(svg_ref.value);
    const slider_group = svg.select('.interpolation_slider');
    slider_group.on("mousemove", (event: MouseEvent) => {
        const [mx, my] = d3.pointer(event);
        const inv_x = Math.round(xScale.invert(mx));
        // console.log("Mouse move at:", mx, my, "inverted x:", inv_x);
        selection.value.hovered_int = {
            interpolation_idx: display_intersection_index.value,
            index_in_interpolation: inv_x
        };
        updateSlider();
    });
    slider_group.selectAll('*').remove();

    yScale = d3.scaleLinear()
        .domain([0, 1])
        .range([height, 0]);
    xScale = d3.scaleLinear()
        .domain([0, interpolations ? interpolations[0].knn_inputs.length : 1])
        .range([spyder_size + padding, width - spyder_size - padding]);
    updateSlider();
}
function endsPosition(i: number) {
    if (!svg_ref.value) return { x: 0, y: 0 };
    const x = i === 0 ? padding / 2 : wrapper_ref.value!.clientWidth - padding / 2 - spyder_size;
    return { x: x, y: yScale(0.8) - (spyder_size / 2) };
}
const interpolationPosition = computed(() => {
    if (!svg_ref.value) return { x: 0, y: 0 };
    const x = xScale(selection.value.hovered_int?.index_in_interpolation || 0) - spyder_size * hover_scale / 2;
    return { x: x, y: yScale(0.8) + padding };
});
function updateSlider() {

    const svg = d3.select(svg_ref.value);
    svg.select(".interpolation_slider").remove();
    if (displayed_interpolation.value == null) return;
    const slider_group = svg.append('g').attr('class', 'interpolation_slider');
    const line = d3.line<number>()
        .x((d, i) => xScale(d))
        .y((d) => yScale(0.8));
    slider_group.append('path')
        .datum([0, interpolations ? interpolations[0].knn_inputs.length : 1])
        .attr('class', 'select-line')
        .attr('d', line);
    slider_group.append('path')
        .datum([0, interpolations ? interpolations[0].knn_inputs.length : 1])
        .attr('class', 'full-line')
        .attr('d', line);
    slider_group.append('circle')
        .attr('class', 'hover-point')
        .attr('cx', xScale(selection.value.hovered_int?.index_in_interpolation || 0))
        .attr('cy', yScale(0.8))
        .attr('r', 5)
}

const display_intersection_index = computed(() => {
    let index = selection.value.hovered_int?.interpolation_idx;
    if (index === undefined || index < 0) {
        index = 0;
    }
    return index;
});
const displayed_interpolation = computed(() => {
    if (interpolations) {
        return interpolations[display_intersection_index.value];
    }
    return null;
});
const hovered_input = computed(() => {
    return displayed_interpolation.value ? displayed_interpolation.value.knn_inputs[selection.value.hovered_int?.index_in_interpolation || 0] : 0;
});
watch(() => selection.value.hovered_int, (int) => {
    if (displayed_interpolation.value && int?.index_in_interpolation || 0 >= 0) {
        let dp_idx = displayed_interpolation.value?.indices[int!.index_in_interpolation];
        if (!dp_idx && dp_idx !== 0) {
            state.displayed_sensitivities = [];
            return;
        }
        data_rep.client.datasets.explanationsForDpDatasetsSetNameDataPointExplanationsIdxPost(dp_idx, data_rep.set_name,
            {
                for_outputs: [hovered_output],
                resolution: 16
            }).then((result) => {
                // console.log("Sensitivity Analysis Result:", result);
                state.displayed_sensitivities = result.data[0].sensitivity_scores;
            }).catch((error) => {
                console.error("Error fetching sensitivity analysis:", error);
            });
    } else {
        state.displayed_sensitivities = [];
    }
}, { immediate: true, deep: true });

const end_points = computed(() => {
    if (displayed_interpolation.value) {
        const first = displayed_interpolation.value.inputs[0];
        const last = displayed_interpolation.value.inputs[displayed_interpolation.value.inputs.length - 1];
        return [first, last];
    }
    return [];
});
watch(() => selection.value.hovered_int, (int) => {
    // setUpLayout();
    updateSlider();
}, { immediate: true, deep: true });
onMounted(() => {
    console.log("InterpolationSlider mounted with data_rep:", data_rep);
    setUpLayout();

    setupMarkers(d3.select(svg_ref.value), 2);

});

</script>

<style scoped>
.inputs_interpolation_sliders {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
}
</style>