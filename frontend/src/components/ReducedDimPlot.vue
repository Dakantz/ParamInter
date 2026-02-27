<template>
    <div class="reduced-dim-plot">
        <div class="legend-container" ref="legend" v-if="show_legend">
            <svg width="200" height="100" ref="legend-svg">
            </svg>

        </div>

        <div :id="`plot-${embedding_name}`" class="plot-container" ref="plot" style="width: 22vw; height: 22vw; ">
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
import { DataRepository, Embeddings, LoadedDataPoints } from '../proc/data-store';
import * as d3 from 'd3';
import * as fc from 'd3fc';
import { ModelRef } from 'vue';
import { CostOverviewData, MappedData, PlotSelection, PlotSelectionResults } from './types';
import { AnnotationData, seriesSvgAnnotation } from './helpers/annotation-series';
import { webglColor } from './helpers/utils';
import { CostOverview, InterpolationResult } from '../api/Api';
import { colormaps_d3 } from './helpers/colormaps';
const { embedded_data, full_data, data_rep, results, embedding_name, interpolations } = defineProps({
    embedded_data: {
        type: Embeddings || null,
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
    interpolations: {
        type: Object as () => InterpolationResult[] | null,
        default: () => []
    },
    results: {
        type: Object as () => CostOverviewData | null,
        default: () => null
    },
    show_legend: {
        type: Boolean,
        default: true
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

const legend = useTemplateRef('legend');
const legend_svg = useTemplateRef('legend-svg');

// const spyders = useTemplateRef('spyders');

const xScale = d3.scaleLinear().domain([0, 1]);
const yScale = d3.scaleLinear().domain([0, 1]);
const xScaleOriginal = xScale.copy();
const yScaleOriginal = yScale.copy();


const pointSeries = fc
    .seriesWebglPoint()
    .equals((a: MappedData, b: MappedData) => a === b)
    .size(10)
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

const similiarityColorScale = d3
    .scaleSequential()
    .domain([0, 1])
    .range([0, 1])
    .interpolator(colormaps_d3['Roma']);
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
    .svgPlotArea(
        // // only render the annotations series on the SVG layer
        fc.seriesSvgMulti()
            .series([annotationSeries])
            .mapping((d: any) => d.svg)
    )
    .webglPlotArea(
        // only render the point series on the WebGL layer
        fc
            .seriesWebglMulti()
            .series([pointSeries])
            .mapping((d: any) => d.data)
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
                    // console.log("Clicked data:", clickedData);
                    if (selection.value.selected_indices.length == 2) {
                        selection.value.selected_indices = [];
                    }
                    selection.value.selected_indices = [...selection.value.selected_indices, clickedData.index];
                }
                redraw();
            })
            .on("mouseleave", () => {
                // console.log("Mouse left the plot area, clearing annotations.");

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
    let selection_idx = selection.value.selected_indices;

    d3.select(plot.value)
        .datum({
            svg: {
                annotations,
                selection: selection_idx.map(i => mapped_data.value[i]),
                hovered: selection.value.hovered_int,
                interpolations: interpolations,
                embeddinging_name: embedding_name,
                previewed_data: selection.value.previewed_index !== null ? mapped_data.value[selection.value.previewed_index] : null
            } as AnnotationData,
            data: mapped_data.value
        })
        .call(chart);
    // d3.select(plot.value).append("p").html("Hover over points to see details");
};

const generateLegend = () => {
    if (!legend_svg.value || !legend.value) return;
    const parentRect = legend.value.getBoundingClientRect();
    d3.select(legend_svg.value)
        .attr("width", parentRect.width)
        .attr("height", parentRect.height);

    const legendItemPadding = 5;
    const excludedBoxSize = 30;
    const xScaleLegend = d3.scaleLinear().domain([0, 1]).range([legendItemPadding, parentRect.width - legendItemPadding * 4 - excludedBoxSize]);

    const yScaleLegend = d3.scaleLinear().domain([0, 1]).range([12, parentRect.height - 12]);



    const legendItems = d3.select(legend_svg.value)
        .append("g")
        .attr("class", "legend-item")

    legendItems.append("text")
        .attr("x", xScaleLegend(0))
        .attr("y", yScaleLegend(-0.1))
        .attr("text-anchor", "start")
        .attr("alignment-baseline", "middle")
        .text("cost:")
        .style("font-size", "8px")
        .style("fill", "black");
    // upper / lower text for similarity values
    legendItems.append("text")
        .attr("x", xScaleLegend(0))
        .attr("y", yScaleLegend(1.5))
        .attr("text-anchor", "start")
        .attr("alignment-baseline", "middle")
        .text("low")
        .style("font-size", "8px")
        .style("fill", "black");
    legendItems.append("text")
        .attr("x", xScaleLegend(1))
        .attr("y", yScaleLegend(1.5))
        .attr("text-anchor", "end")
        .attr("alignment-baseline", "middle")
        .text("high")
        .style("font-size", "8px")
        .style("fill", "black");

    // create a gradient for the legend
    const defs = d3.select(legend_svg.value).append("defs");
    const gradient = defs.append("linearGradient")
        .attr("id", "legend-gradient")
        .attr("x1", "0%")
        .attr("y1", "0%")
        .attr("x2", "100%")
        .attr("y2", "0%");
    const resolution = 10;
    for (let i = 0; i <= resolution; i++) {
        const t = i / resolution;
        gradient.append("stop")
            .attr("offset", `${t * 100}%`)
            .attr("stop-color", similiarityColorScale(t))
            .attr("stop-opacity", 1);
    }
    // add a rectangle with the gradient fill
    const rectWidth = xScaleLegend(1) - xScaleLegend(0);
    const rectHeight = yScaleLegend(0.5) - yScaleLegend(0);
    console.log("Adding legend rectangle with dimensions:", rectWidth, "x", parentRect.height);
    d3.select(legend_svg.value)
        .append("rect")
        .attr("x", xScaleLegend(0))
        .attr("y", yScaleLegend(0.5))
        .attr("width", rectWidth)
        .attr("height", rectHeight)
        .style("fill", "url(#legend-gradient)");

    d3.select(legend_svg.value)
        .append("rect")
        .attr("x", xScaleLegend(1) + legendItemPadding * 2)
        .attr("y", yScaleLegend(0.5))
        .attr("width", rectHeight)
        .attr("height", rectHeight)
        .style("fill", "black");

    legendItems.append("text")
        .attr("x", xScaleLegend(1) + legendItemPadding * 2)
        .attr("y", yScaleLegend(1.5))
        .attr("text-anchor", "start")
        .attr("alignment-baseline", "middle")
        .text("excluded")
        .style("font-size", "8px")
        .style("fill", "black");
};

watch(() => embedded_data, (newData) => {
    if (plot.value) {
        updateData();
    }
}, {});


watch(() => selection.value, (newSelection) => {
    redraw();
}, { immediate: true, deep: true });


watch(() => results, (sim) => {
    // console.log("Updating similarity colors with data:", sim);
    const similarityFill = (d: MappedData) => {
        const similarity = sim?.costs[d.index];

        if (similarity === undefined || !sim?.within_filter[d.index]) {
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
watch(() => interpolations, (int) => {
    redraw();
}, { immediate: true });
onMounted(() => {
    if (plot.value) {
        updateData();
    }
    if (legend_svg.value) {
        generateLegend();
    }
});
</script>

<style>
.reduced-dim-plot {
    min-width: 22vw;
    min-height: 22vw;
    max-width: 22vw;
    max-height: 22vw;
    margin: 7px;
    display: flex;
    flex-direction: column;
    align-items: start;
    justify-items: center;
    background-color: rgb(250, 254, 254);

}

.legend-container {
    width: 200px;
    height: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.plot-container {}

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
