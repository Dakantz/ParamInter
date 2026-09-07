<template>
    <div class="pc-container">
        <h2>{{ title }}</h2>
        <p class="info">Drag along an axis to narrow the range for that dimension; click a
            remaining line to select that point.</p>
        <div class="pc-toolbar">
            <span class="pc-count">{{ state.active_count }} / {{ state.rows.length }} shown</span>
            <button v-if="has_active_brushes" @click="clearBrushes">Reset filters</button>
        </div>
        <Loading v-if="state.loading" />
        <div class="pc-scroll" ref="container">
            <svg ref="plot"></svg>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { reactive, watch, onMounted, onBeforeUnmount, useTemplateRef, computed } from 'vue';
import * as d3 from 'd3';
import { DataRepository } from '../../proc/data-store';
import Loading from '../ui/Loading.vue';

const emit = defineEmits<{
    (e: 'preview', idx: number): void;
    (e: 'select', idx: number): void;
}>();
const { data_rep, title } = defineProps({
    data_rep: {
        type: Object as () => DataRepository,
        required: true,
    },
    title: {
        type: String,
        default: 'Find a Datapoint',
    },
});

const MAX_LINES = 500;
const AXIS_SPACING = 46;
const AXIS_WIDTH = 440;
const MARGIN = { top: 24, right: 32, bottom: 24, left: 150 };

const ACTIVE_COLOR = '#3a8000';
const INACTIVE_COLOR = '#ccc';
const HOVER_COLOR = '#d1495b';

interface Row {
    index: number;
    values: number[];
}

const container = useTemplateRef('container');
const plot = useTemplateRef('plot');

const state = reactive({
    loading: false,
    dims: [] as string[],
    rows: [] as Row[],
    domains: {} as Record<string, [number, number]>,
    brushes: {} as Record<string, [number, number] | null>,
    active_count: 0,
});

const has_active_brushes = computed(() => Object.values(state.brushes).some(b => b !== null));

function cssSafe(dim: string): string {
    return dim.replace(/[^a-zA-Z0-9_-]/g, '_');
}

function isActive(row: Row): boolean {
    for (let i = 0; i < state.dims.length; i++) {
        const brush = state.brushes[state.dims[i]];
        if (!brush) continue;
        const v = row.values[i];
        if (v === undefined || v < brush[0] || v > brush[1]) return false;
    }
    return true;
}

async function loadData() {
    const desc = data_rep.description;
    if (!desc || !desc.input_cols?.length) return;
    state.loading = true;
    try {
        state.dims = [...desc.input_cols];
        state.brushes = {};
        state.domains = {};
        for (const dim of state.dims) {
            const lo = desc.min_values?.[dim] ?? 0;
            const hi = desc.max_values?.[dim] ?? 1;
            state.domains[dim] = [lo, hi];
        }

        const res = await data_rep.client.datasets.getDataSampleDatasetsSetNameDataSampleGet(
            data_rep.set_name,
            { max_samples: MAX_LINES },
        );
        const { indices, inputs } = res.data;
        state.rows = indices.map((index, i) => ({ index, values: inputs[i] }));
        state.active_count = state.rows.length;
        redraw();
    } catch (error) {
        console.error('Error loading data for parallel coordinates selector:', error);
        state.rows = [];
    } finally {
        state.loading = false;
    }
}

watch(() => data_rep.description, (desc) => {
    if (desc) loadData();
}, { immediate: true, deep: true });

function lineStyleFor(sel: d3.Selection<SVGPathElement, Row, any, any>) {
    sel.attr('stroke', d => isActive(d) ? ACTIVE_COLOR : INACTIVE_COLOR)
        .attr('stroke-width', d => isActive(d) ? 1 : 1)
        .attr('opacity', d => isActive(d) ? 0.45 : 0.06)
        .style('pointer-events', d => isActive(d) ? 'auto' : 'none');
}

function applyActive() {
    if (!plot.value) return;
    const svg = d3.select(plot.value);
    const selection = svg.selectAll<SVGPathElement, Row>('path.pc-line');
    lineStyleFor(selection);
    state.active_count = state.rows.filter(isActive).length;
}

let brush_behaviors: Record<string, d3.BrushBehavior<unknown>> = {};

function clearBrushes() {
    if (!plot.value) return;
    const svg = d3.select(plot.value);
    for (const dim of state.dims) {
        state.brushes[dim] = null;
        const behavior = brush_behaviors[dim];
        if (behavior) {
            svg.select<SVGGElement>(`g.pc-brush-${cssSafe(dim)}`).call(behavior.move, null);
        }
    }
    applyActive();
}

function redraw() {
    if (!plot.value || !container.value || !state.dims.length) return;
    const width = Math.max(container.value.clientWidth, AXIS_WIDTH + MARGIN.left + MARGIN.right);
    const height = Math.max(
        container.value.clientHeight,
        state.dims.length * AXIS_SPACING + MARGIN.top + MARGIN.bottom,
    );

    const svg = d3.select(plot.value);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);
    brush_behaviors = {};

    const y = d3.scalePoint()
        .domain(state.dims)
        .range([MARGIN.top, height - MARGIN.bottom]);

    const x: Record<string, d3.ScaleLinear<number, number>> = {};
    state.dims.forEach(dim => {
        const [lo, hi] = state.domains[dim];
        const pad = (hi - lo) * 0.02 || 1;
        x[dim] = d3.scaleLinear().domain([lo - pad, hi + pad]).range([0, AXIS_WIDTH]).clamp(true);
    });

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left}, 0)`);

    const line = d3.line<number>()
        .x((v, i) => x[state.dims[i]](v))
        .y((_, i) => y(state.dims[i]) as number);

    const lines_g = g.append('g').attr('class', 'pc-lines');
    const line_sel = lines_g.selectAll<SVGPathElement, Row>('path.pc-line')
        .data(state.rows, (d: any) => d.index)
        .join('path')
        .attr('class', 'pc-line')
        .attr('fill', 'none')
        .attr('d', d => line(d.values))
        .on('mouseenter', function (_event, d) {
            if (!isActive(d)) return;
            d3.select<SVGPathElement, Row>(this).raise()
                .attr('stroke', HOVER_COLOR)
                .attr('stroke-width', 2.2)
                .attr('opacity', 1);
            emit('preview', d.index);
        })
        .on('mouseleave', function (_event) {
            lineStyleFor(d3.select<SVGPathElement, Row>(this));
            emit('preview', -1);
        })
        .on('click', function (_event, d) {
            if (!isActive(d)) return;
            emit('select', d.index);
        });
    lineStyleFor(line_sel);
    line_sel.append('title').text(d => `#${d.index}`);

    const axes_g = g.append('g').attr('class', 'pc-axes');
    state.dims.forEach(dim => {
        const axis_g = axes_g.append('g')
            .attr('class', `pc-axis pc-axis-${cssSafe(dim)}`)
            .attr('transform', `translate(0, ${y(dim)})`);

        axis_g.append('g')
            .call(d3.axisBottom(x[dim]).ticks(5).tickSize(4))
            .call(sel => sel.select('.domain').attr('stroke', '#999'))
            .call(sel => sel.selectAll('text').attr('font-size', 9));

        axis_g.append('text')
            .attr('class', 'pc-axis-label')
            .attr('transform', 'translate(-10, 4)')
            .attr('text-anchor', 'end')
            .attr('font-size', 10)
            .text(dim);

        const brush = d3.brushX<unknown>()
            .extent([[0, -9], [AXIS_WIDTH, 9]])
            .on('start brush end', (event: d3.D3BrushEvent<unknown>) => {
                if (!event.sourceEvent) return;
                const sel = event.selection as [number, number] | null;
                if (!sel) {
                    state.brushes[dim] = null;
                } else {
                    const [left_px, right_px] = sel;
                    state.brushes[dim] = [x[dim].invert(left_px), x[dim].invert(right_px)];
                }
                applyActive();
            });
        brush_behaviors[dim] = brush as d3.BrushBehavior<unknown>;

        axis_g.append('g')
            .attr('class', `pc-brush pc-brush-${cssSafe(dim)}`)
            .call(brush);
    });

    applyActive();
}

let resize_observer: ResizeObserver | null = null;
onMounted(() => {
    if (container.value) {
        resize_observer = new ResizeObserver(() => redraw());
        resize_observer.observe(container.value);
    }
});
onBeforeUnmount(() => {
    resize_observer?.disconnect();
});
</script>

<style scoped>
.pc-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.info {
    font-size: 11px;
    color: #666;
    text-align: center;
    padding: 0 8px;
}

.pc-toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 11px;
    color: #444;
    margin-bottom: 4px;
}

.pc-scroll {
    width: 100%;
    max-height: 75vh;
    overflow: auto;
}

.pc-line {
    cursor: pointer;
}

.pc-axis-label {
    fill: #333;
}
</style>
