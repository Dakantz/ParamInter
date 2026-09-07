<template>
    <div class="splom-container">
        <Loading v-if="state.loading" />
        <div class="splom-scroll" ref="container">
            <svg ref="plot"></svg>
            <div v-if="popover_cell" class="splom-popover" :style="popoverStyle">
                <svg ref="popoverPlot"></svg>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { reactive, computed, watch, nextTick, onMounted, onBeforeUnmount, useTemplateRef, type PropType } from 'vue';
import * as d3 from 'd3';
import { DataRepository } from '../../proc/data-store';
import Loading from '../ui/Loading.vue';

const { data_rep, highlight_row, highlight_cell, highlight_point_index } = defineProps({
    data_rep: {
        type: Object as () => DataRepository,
        required: true,
    },
    highlight_row: {
        type: String as PropType<string | null>,
        default: null,
    },
    highlight_cell: {
        type: Array as () => string[],
        default: null,
    },
    // Dataset-level row index of a point hovered elsewhere (e.g. a Beeswarm dot) - highlighted in
    // the magnified popover when it's among the currently sampled rows (see `state.indices`).
    highlight_point_index: {
        type: Number as PropType<number | null>,
        default: null,
    },
});

// Cells shrink to fit the container's width rather than a fixed size (a fixed size would make
// the matrix overflow its panel for anything but a handful of dimensions) - clamped so it never
// gets illegibly small or silly large. The popover picks up the legibility slack at small sizes.
const MIN_CELL = 26;
const MAX_CELL = 88;
const MARGIN = { top: 8, right: 8, bottom: 30, left: 46 };
const POINT_R = 1.4;
const ROW_HIGHLIGHT = '#ffe9b3';
const CELL_HIGHLIGHT = '#ffbf69';
const POPOVER_MARGIN = { top: 12, right: 16, bottom: 46, left: 58 };

const container = useTemplateRef('container');
const plot = useTemplateRef('plot');
const popoverPlot = useTemplateRef('popoverPlot');

interface Cell { row: string; col: string; ri: number; ci: number }

const state = reactive({
    loading: false,
    dims: [] as string[],
    rows: [] as number[][],
    indices: [] as number[],
    domains: {} as Record<string, [number, number]>,
    cell_size: MAX_CELL,
    hovered_cell: null as { row: string; col: string } | null,
});

function getDesc() {
    // EffectsPanels only calls data_rep.loadDescription() (which populates manager_settings),
    // not loadAll() (which populates .description) - so fall back to manager_settings here the
    // same way EffectsPanels itself does, rather than relying on .description alone.
    return data_rep.description || data_rep.manager_settings?.data_description || null;
}

async function loadData() {
    const desc = getDesc();
    if (!desc || !desc.input_cols?.length) return;
    state.loading = true;
    try {
        state.dims = [...desc.input_cols];
        state.domains = {};
        for (const dim of state.dims) {
            const lo = desc.min_values?.[dim] ?? 0;
            const hi = desc.max_values?.[dim] ?? 1;
            state.domains[dim] = [lo, hi];
        }
        // Cap total rendered points at roughly 20k circles (n_dims^2 cells x sample_size points).
        // const sample_size = Math.max(
        //     40,
        //     Math.min(250, Math.floor(20000 / Math.max(1, state.dims.length * state.dims.length))),
        // );
        const sample_size = -1;
        const res = await data_rep.client.datasets.getDataSampleDatasetsSetNameDataSampleGet(
            data_rep.set_name,
            { max_samples: sample_size, seed: 0 },
        );
        state.rows = res.data.inputs;
        state.indices = res.data.indices;
        redraw();
    } catch (error) {
        console.error('Error loading data for scatterplot matrix:', error);
        state.rows = [];
    } finally {
        state.loading = false;
    }
}

watch(() => [data_rep.description, data_rep.manager_settings], () => {
    if (getDesc()) loadData();
}, { immediate: true, deep: true });

function redraw() {
    if (!plot.value || !container.value || !state.dims.length) return;
    const n = state.dims.length;
    const available = container.value.clientWidth - MARGIN.left - MARGIN.right;
    const cell_size = Math.max(MIN_CELL, Math.min(MAX_CELL, Math.floor(available / n)));
    state.cell_size = cell_size;
    const width = MARGIN.left + MARGIN.right + n * cell_size;
    const height = MARGIN.top + MARGIN.bottom + n * cell_size;

    const svg = d3.select(plot.value);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const scales: Record<string, d3.ScaleLinear<number, number>> = {};
    const dim_index: Record<string, number> = {};
    state.dims.forEach((dim, i) => {
        dim_index[dim] = i;
        const [lo, hi] = state.domains[dim];
        const pad = (hi - lo) * 0.05 || 1;
        scales[dim] = d3.scaleLinear().domain([lo - pad, hi + pad]).range([cell_size - 3, 3]);
    });

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left}, ${MARGIN.top})`);

    const cell_data: Cell[] = [];
    state.dims.forEach((row_dim, ri) => {
        state.dims.forEach((col_dim, ci) => {
            cell_data.push({ row: row_dim, col: col_dim, ri, ci });
        });
    });

    const cells = g.selectAll<SVGGElement, Cell>('g.splom-cell')
        .data(cell_data)
        .join('g')
        .attr('class', 'splom-cell')
        .attr('transform', d => `translate(${d.ci * cell_size}, ${d.ri * cell_size})`);

    cells.append('rect')
        .attr('class', 'splom-cell-bg')
        .attr('width', cell_size)
        .attr('height', cell_size)
        .attr('fill', 'transparent');

    cells.append('rect')
        .attr('width', cell_size)
        .attr('height', cell_size)
        .attr('fill', 'none')
        .attr('stroke', '#eee');

    cells.each(function (d) {
        const cell = d3.select(this);
        if (d.row === d.col) {
            cell.append('text')
                .attr('x', cell_size / 2)
                .attr('y', cell_size / 2)
                .attr('text-anchor', 'middle')
                .attr('alignment-baseline', 'middle')
                .attr('font-size', Math.min(9, cell_size / 7))
                .attr('font-weight', 'bold')
                .text(d.row.length > 13 ? d.row.slice(0, 12) + '…' : d.row);
            return;
        }
        const x_scale = scales[d.col];
        const y_scale = scales[d.row];
        const col_i = dim_index[d.col];
        const row_i = dim_index[d.row];
        cell.selectAll('circle')
            .data(state.rows)
            .join('circle')
            .attr('cx', r => x_scale(r[col_i]))
            .attr('cy', r => y_scale(r[row_i]))
            .attr('r', POINT_R)
            .attr('fill', '#3a8000')
            .attr('opacity', 0.5);

        // Full-cell invisible hit target so hovering anywhere in the cell (not just directly on
        // a point) shows the magnified popover for that pair.
        cell.append('rect')
            .attr('width', cell_size)
            .attr('height', cell_size)
            .attr('fill', 'transparent')
            .style('pointer-events', 'all')
            .on('mouseenter', () => { state.hovered_cell = { row: d.row, col: d.col }; })
            .on('mouseleave', () => { state.hovered_cell = null; });
    });

    // Ticks only along the left column and bottom row (per-cell axes would be unreadable).
    state.dims.forEach((dim, i) => {
        g.append('g')
            .attr('transform', `translate(${i * cell_size}, ${n * cell_size})`)
            .call(d3.axisBottom(scales[dim]).ticks(3).tickSize(3))
            .call(sel => sel.selectAll('text').attr('font-size', 7))
            .call(sel => sel.select('.domain').attr('stroke', '#ccc'));
        g.append('g')
            .attr('transform', `translate(0, ${i * cell_size})`)
            .call(d3.axisLeft(scales[dim]).ticks(3).tickSize(3))
            .call(sel => sel.selectAll('text').attr('font-size', 7))
            .call(sel => sel.select('.domain').attr('stroke', '#ccc'));
    });

    applyHighlight();
}

function applyHighlight() {
    if (!plot.value) return;
    const svg = d3.select(plot.value);
    svg.selectAll<SVGRectElement, Cell>('rect.splom-cell-bg')
        .attr('fill', d => {
            if (highlight_cell && (
                (d.row === highlight_cell[0] && d.col === highlight_cell[1]) ||
                (d.row === highlight_cell[1] && d.col === highlight_cell[0])
            )) return CELL_HIGHLIGHT;
            if (!highlight_cell && highlight_row && d.row === highlight_row) return ROW_HIGHLIGHT;
            return 'transparent';
        });
}

watch(() => [highlight_row, highlight_cell], applyHighlight, { deep: true });

// The popover shows one magnified scatterplot: whichever cell the mouse is directly over in the
// matrix, falling back to the cell an order-2 Dependency-row hover highlighted (so that hover
// path also gets a legible view, not just the tiny in-matrix cell).
const popover_cell = computed(() => {
    if (state.hovered_cell) return state.hovered_cell;
    if (highlight_cell) return { row: highlight_cell[0], col: highlight_cell[1] };
    return null;
});

const popoverSize = computed(() => {
    const base = container.value?.clientWidth || 300;
    return Math.round(base / 3);
});

const popoverStyle = computed(() => ({
    width: `${popoverSize.value}px`,
    height: `${popoverSize.value}px`,
}));

function drawPopover() {
    if (!popoverPlot.value) return;
    const cell = popover_cell.value;
    const svg = d3.select(popoverPlot.value);
    if (!cell || !state.rows.length) {
        svg.selectAll('*').remove();
        return;
    }
    const size = popoverSize.value;
    const inner_w = Math.max(20, size - POPOVER_MARGIN.left - POPOVER_MARGIN.right);
    const inner_h = Math.max(20, size - POPOVER_MARGIN.top - POPOVER_MARGIN.bottom);
    const [lo_x, hi_x] = state.domains[cell.col];
    const [lo_y, hi_y] = state.domains[cell.row];
    const pad_x = (hi_x - lo_x) * 0.05 || 1;
    const pad_y = (hi_y - lo_y) * 0.05 || 1;
    const x_scale = d3.scaleLinear().domain([lo_x - pad_x, hi_x + pad_x]).range([0, inner_w]);
    const y_scale = d3.scaleLinear().domain([lo_y - pad_y, hi_y + pad_y]).range([inner_h, 0]);
    const col_i = state.dims.indexOf(cell.col);
    const row_i = state.dims.indexOf(cell.row);

    svg.selectAll('*').remove();
    svg.attr('width', size).attr('height', size);

    const g = svg.append('g').attr('transform', `translate(${POPOVER_MARGIN.left}, ${POPOVER_MARGIN.top})`);

    const isHighlighted = (r: number[], i: number) =>
        highlight_point_index != null && i === highlight_point_index;

    const points = g.selectAll('circle')
        .data(state.rows)
        .join('circle')
        .attr('cx', r => x_scale(r[col_i]))
        .attr('cy', r => y_scale(r[row_i]))
        .attr('r', (r, i) => isHighlighted(r, i) ? 5.5 : 3)
        .attr('fill', (r, i) => isHighlighted(r, i) ? '#e0501e' : '#3a8000')
        .attr('stroke', (r, i) => isHighlighted(r, i) ? '#000' : 'none')
        .attr('opacity', (r, i) => isHighlighted(r, i) ? 1 : 0.6);
    // Draw the highlighted point last so it isn't hidden under overlapping neighbors.
    points.filter((r, i) => isHighlighted(r, i)).raise();

    g.append('g')
        .attr('transform', `translate(0, ${inner_h})`)
        .call(d3.axisBottom(x_scale).ticks(6).tickSize(4))
        .call(sel => sel.select('.domain').attr('stroke', '#999'));
    g.append('g')
        .call(d3.axisLeft(y_scale).ticks(6).tickSize(4))
        .call(sel => sel.select('.domain').attr('stroke', '#999'));

    // Variable names live on the axes (not a header above the plot), so the popover reads like a
    // normal labeled scatterplot rather than a magnified matrix cell.
    g.append('text')
        .attr('class', 'popover-axis-label popover-x-label')
        .attr('x', inner_w / 2)
        .attr('y', inner_h + POPOVER_MARGIN.bottom - 6)
        .attr('text-anchor', 'middle')
        .attr('font-size', 10)
        .attr('font-weight', 'bold')
        .text(truncateLabel(cell.col, inner_w));

    g.append('text')
        .attr('class', 'popover-axis-label popover-y-label')
        .attr('transform', `translate(${-POPOVER_MARGIN.left + 14}, ${inner_h / 2}) rotate(-90)`)
        .attr('text-anchor', 'middle')
        .attr('font-size', 10)
        .attr('font-weight', 'bold')
        .text(truncateLabel(cell.row, inner_h));
}

// Axis labels sit in fixed-width margins, so long variable names are clipped to roughly what
// fits (~5.5px/char at the 10px label font) rather than overflowing into the plot or neighbors.
function truncateLabel(label: string, available_px: number) {
    const max_chars = Math.max(3, Math.floor(available_px / 5.5));
    return label.length > max_chars ? label.slice(0, max_chars - 1) + '…' : label;
}

watch(popover_cell, () => nextTick(drawPopover));
watch(() => state.rows, () => nextTick(drawPopover));
watch(() => highlight_point_index, () => nextTick(drawPopover));

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
.splom-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.splom-scroll {
    position: relative;
    width: 100%;
    max-height: 60vh;
    overflow: auto;
}

.splom-popover {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.98);
    border: 1px solid #999;
    border-radius: 4px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    pointer-events: none;
    z-index: 5;
}
</style>
