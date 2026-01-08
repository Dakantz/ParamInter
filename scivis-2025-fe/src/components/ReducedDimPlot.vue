<template>
    <div class="reduced-dim-plot">
        <div :id="`plot-${embedding_name}`" class="plot-container" ref="plot" style="width: 420px; height: 420px; ">
        </div>
        <!-- <svg width="360" height="360" xmlns="http://www.w3.org/2000/svg" ref="plot" :id="`plot-${embedding_name}`">
            <g transform="scale(360,360)">
                <g ref="spyders"></g>
            </g>

        </svg> -->
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, useTemplateRef, onMounted, computed } from 'vue';
import { DataRepository, Embeddings, LoadedDataPoints } from '../proc/types';
import * as d3 from 'd3';
import * as fc from 'd3fc';
import { ModelRef } from 'vue';
import { MappedData, PlotSelection, PlotSelectionResults } from './types';
import { AnnotationData, seriesSvgAnnotation } from './helpers/annotation-series';
import { webglColor } from './helpers/utils';
const { embedded_data, full_data, data_rep, results, embedding_name } = defineProps({
    embedded_data: {
        type: Embeddings,
        required: true
    },
    full_data: {
        type: LoadedDataPoints,
        required: true
    },
    data_rep: {
        type: DataRepository,
        required: true
    },
    embedding_name: {
        type: String,
        required: true
    },
    results: {
        type: Object as () => PlotSelectionResults,
        default: () => new PlotSelectionResults()
    }

});

const selection: ModelRef<PlotSelection> = defineModel({
    type: PlotSelection,
    default: () => new PlotSelection()
});

const ui_params = reactive({
    point_size: 2,
    spyder_size: 64
});

const plot = useTemplateRef('plot');
// const spyders = useTemplateRef('spyders');

const xScale = d3.scaleLinear().domain([0, 1]);
const yScale = d3.scaleLinear().domain([0, 1]);
const xScaleOriginal = xScale.copy();
const yScaleOriginal = yScale.copy();


const pointSeries = fc
    .seriesWebglPoint()
    .equals((a: MappedData, b: MappedData) => a === b)
    .size(1)
    .crossValue((d: MappedData) => d.x)
    .mainValue((d: MappedData) => d.y);

// const zoom = d3
//     .zoom()
//     .scaleExtent([0.8, 10])
//     .on("zoom", () => {
//         // update the scales based on current zoom
//         xScale.domain((d3 as any).event.transform.rescaleX(xScaleOriginal).domain());
//         yScale.domain((d3 as any).event.transform.rescaleY(yScaleOriginal).domain());
//         redraw();
//     });
let quadtree = d3.quadtree<MappedData>();
const annotations = [] as MappedData[];

// const annotationSeries = seriesSvgAnnotation()
//   .notePadding(15)
//   .type(d3.annotationCallout);

const pointer = fc.pointer().on("point", ([coord]: any) => {
    annotations.pop();
    // console.log("Pointer coordinates:", coord);
    if (!coord || !quadtree) {
        return;
    }

    // find the closes datapoint to the pointer
    const x = xScale.invert(coord.x);
    const y = yScale.invert(coord.y);
    const radius = Math.abs(xScale.invert(coord.x) - xScale.invert(coord.x - 20));
    const closestDatum = quadtree.find(x, y, radius);


    // if the closest point is within 20 pixels, show the annotation
    if (closestDatum) {
        annotations[0] = closestDatum;
        // selection.value.hovered_index = closestDatum.index;
    }

    redraw();
})
const mapped_data = computed(() => {
    return embedded_data.embeddings.map((d, i) => ({
        x: d[0],
        y: d[1],
        data: d,
        index: i
    } as MappedData));
});

function updateData() {
    quadtree = d3
        .quadtree<MappedData>()
        .x(d => d.x)
        .y(d => d.y)
        .addAll(mapped_data.value);
    redraw();
}
const annotationSeries = seriesSvgAnnotation(data_rep, ui_params.spyder_size);
// const createAnnotationData = datapoint => ({
//   note: {
//     label: datapoint.first_author_name + " " + datapoint.year,
//     bgPadding: 5,
//     title: trunc(datapoint.title, 100)
//   },
//   x: datapoint.x,
//   y: datapoint.y,
//   dx: 20,
//   dy: 20
// });
const chart = fc
    .chartCartesian({
        xScale: xScale,
        yScale: yScale,
    })
    .webglPlotArea(
        // only render the point series on the WebGL layer
        fc
            .seriesWebglMulti()
            .series([pointSeries])
            .mapping((d: any) => d.data)
    )
    .svgPlotArea(
        // // only render the annotations series on the SVG layer
        fc.seriesSvgMulti()
            .series([annotationSeries])
            .mapping((d: any) => d.svg)
    )
    // .svgPlotArea(
    //     // render the selection series on the SVG layer
    //     fc.seriesSvgMulti()
    //         .series([selectionSeries])
    //         .mapping(d => d.selection)
    // )
    .decorate(sel =>
        sel
            .enter()
            .select("d3fc-svg.plot-area")
            .on('click', () => {
                if (annotations.length > 0) {
                    const clickedData = annotations[0];
                    console.log("Clicked data:", clickedData);
                    if (selection.value.selected_indices.length == 2) {
                        selection.value.selected_indices = [];
                    }
                    selection.value.selected_indices = [...selection.value.selected_indices, clickedData.index];
                    results.interpolation = null
                }
                redraw();
            })
            .on("mouseleave", () => {
                console.log("Mouse left the plot area, clearing annotations.");
                selection.value.hovered_index = -1;
                annotations.length = 0; // Clear the annotations array
                redraw();
            })
            .call(pointer)
        // .on("measure.range", () => {
        //     xScaleOriginal.range([0, (d3 as any).event.detail.width]);
        //     yScaleOriginal.range([(d3 as any).event.detail.height, 0]);
        // })
        // .call(zoom as any)
    ).xAxisHeight('0px').yAxisWidth('0px');

const redraw = () => {
    // console.log("Redrawing plot with data:", mapped_data.value, "and annotations:", annotations, "on plot:", plot.value?.id);
    d3.select(plot.value)
        .datum({
            svg: {
                annotations,
                selection: selection.value.selected_indices.map(i => mapped_data.value[i]),
                hovered: mapped_data.value[selection.value.hovered_index || -1] || null,
                interpolation: results.interpolation,
                embeddinging_name: embedding_name
            } as AnnotationData,
            data: mapped_data.value
        })
        .call(chart);
    // d3.select(plot.value).append("p").html("Hover over points to see details");
};
watch(() => embedded_data, (newData) => {
    if (plot.value) {
        updateData();
    }
}, {});


watch(() => selection.value, (newSelection) => {
    redraw();
}, { immediate: true, deep: true });

const similiarityColorScale = d3
    .scaleSequential()
    .domain([0, 1])
    .interpolator(d3.interpolateRdYlGn);

watch(() => results.similarities, (sim) => {
    // console.log("Updating similarity colors with data:", sim);
    const similarityFill = (d: MappedData) => {
        const similarity = sim[d.index];
        if (similarity === undefined) {
            return [0, 0, 0, 1]; // Default color for undefined similarities
        }
        const color = similiarityColorScale(similarity);
        return webglColor(color);
    };
    const point_color = fc.webglFillColor().value(similarityFill).data(mapped_data.value);
    pointSeries.decorate((program: any) => point_color(program));
    if (plot.value) {
        redraw();
    }
}, { immediate: true });
watch(() => results.interpolation, (int) => {
    redraw();
}, { immediate: true, deep: true });
onMounted(() => {
    if (plot.value) {
        updateData();
    }
});
</script>

<style>
.reduced-dim-plot {
    min-width: 420px;
    min-height: 420px;
    max-width: 420px;
    max-height: 420px;
    margin: 7px;
    display: flex;
}

.plot-container {
    background-color: rgb(223, 239, 238);
}

.annotation {
    fill: rgba(208, 162, 35, 0.754);
    stroke: rgba(137, 107, 0, 0.826);
    stroke-width: 1px;
}

.selection {
    fill: rgba(0, 0, 255, 0.374);
    stroke: rgba(0, 0, 128, 0.543);
    stroke-width: 1px;
}

.hovered {
    fill: rgba(128, 255, 0, 0.5);
    stroke: rgba(58, 128, 0, 0.72);
    stroke-width: 1px;
}

.interpolation {
    fill: none;
    stroke: rgba(4, 79, 150, 0.879);
    stroke-width: 2px;
}

.interpolation_spyder {
    fill: rgba(4, 79, 150, 0.511);
    stroke: rgba(0, 0, 128, 0.295);
    stroke-width: 1px;
}
</style>
