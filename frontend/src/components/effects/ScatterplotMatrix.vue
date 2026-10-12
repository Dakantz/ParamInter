<template>
    <div class="splom-container">
        <div v-if="state.loading" class="splom-loading-bar">
            <LoadingBar :progress="load_progress" :label="load_label" />
        </div>
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
import { InteractionBackgroundResult } from '../../api/Api';
import { colormaps_d3 } from '../helpers/colormaps';
import { BackgroundMode } from './types';
import LoadingBar from '../ui/LoadingBar.vue';

const { data_rep, highlight_row, highlight_cell, highlight_point_index, output_col, background_mode } = defineProps({
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
    // Output column the KNN-interpolated popover background is computed against - no background
    // is fetched/shown without one.
    output_col: {
        type: String,
        default: '',
    },
    // Which field of the interpolated background to color the popover by - both are returned by
    // the same request, so switching this never re-fetches, only re-renders.
    background_mode: {
        type: String as PropType<BackgroundMode>,
        default: 'output',
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
const BG_RESOLUTION = 40;
const BG_K_NEIGHBORS = 5;
const BG_FETCH_DEBOUNCE_MS = 150;

const container = useTemplateRef('container');
const plot = useTemplateRef('plot');
const popoverPlot = useTemplateRef('popoverPlot');

interface Cell { row: string; col: string; ri: number; ci: number }
const indices = [] as number[];
const state = reactive({
    loading: false,
    dims: [] as string[],
    // rows: [] as number[][],
    // indices: [] as number[],
    domains: {} as Record<string, [number, number]>,
    cell_size: MAX_CELL,
    hovered_cell: null as { row: string; col: string } | null,
    // KNN-interpolated background for whichever (var1=col, var2=row) pair the popover currently
    // shows - null while nothing has loaded yet for that pair (see fetchBackground below).
    background: null as InteractionBackgroundResult | null,
    // Total row count of the dataset, for the loading bar's progress fraction - known up front
    // from the dataset description, before any page has come back.
    total_rows: 0,
});

// Progress fraction for the loading bar - state.indices grows as each page of loadData() lands.
const load_progress = computed(() => (
    state.total_rows > 0 ? indices.length / state.total_rows : 0
));
const load_label = computed(() => (
    state.total_rows > 0 ? `${indices.length} / ${state.total_rows} rows` : 'loading…'
));

// Keyed by set/output/pair so re-hovering an already-seen cell (or flipping background_mode,
// which only changes which field of the same response is drawn) never re-fetches.
const background_cache = new Map<string, InteractionBackgroundResult>();
let background_req_seq = 0;
let background_timer: ReturnType<typeof setTimeout> | null = null;

function backgroundKey(var1: string, var2: string) {
    return `${data_rep.set_name}::${output_col}::${var1}::${var2}`;
}

async function fetchBackground(cell: { row: string; col: string }) {
    const key = backgroundKey(cell.col, cell.row);
    const seq = ++background_req_seq;
    try {
        const res = await data_rep.client.datasets.getInteractionBackgroundDatasetsSetNameEffectsInteractionBackgroundPost(
            data_rep.set_name,
            {
                output_col,
                var1: cell.col,
                var2: cell.row,
                resolution: BG_RESOLUTION,
                k_neighbors: BG_K_NEIGHBORS,
            },
        );
        background_cache.set(key, res.data);
        // Ignore stale responses: only apply if this is still the latest request and the popover
        // is still showing the same pair it was fetched for.
        if (seq !== background_req_seq) return;
        const current = popover_cell.value;
        if (current && current.row === cell.row && current.col === cell.col) {
            state.background = res.data;
        }
    } catch (error) {
        console.error('Error fetching interaction background:', error);
    }
}

function getDesc() {
    // EffectsPanels only calls data_rep.loadDescription() (which populates manager_settings),
    // not loadAll() (which populates .description) - so fall back to manager_settings here the
    // same way EffectsPanels itself does, rather than relying on .description alone.
    return data_rep.description || data_rep.manager_settings?.data_description || null;
}
let rows = [] as number[][];
// The full dataset is loaded a page at a time (not a random sample) rather than as one request:
// each page redraws immediately, so the matrix fills in progressively instead of blocking on the
// whole dataset, and no single request has to carry the full payload.
const BATCH_SIZE = 2000;

// Bumped on every loadData() call so a stale in-flight batch loop (e.g. from a dataset switch)
// stops appending once a newer load has started.
let load_seq = 0;

async function loadData() {
    const desc = getDesc();
    if (!desc || !desc.input_cols?.length) return;
    const seq = ++load_seq;
    state.loading = true;
    rows = [];
    indices.length = 0;
    state.total_rows = desc.num_samples ?? 0;
    try {
        state.dims = [...desc.input_cols];
        state.domains = {};
        for (const dim of state.dims) {
            const lo = desc.min_values?.[dim] ?? 0;
            const hi = desc.max_values?.[dim] ?? 1;
            state.domains[dim] = [lo, hi];
        }

        for (let offset = 0; ; offset += BATCH_SIZE) {
            if (seq !== load_seq) return;
            const res = await data_rep.client.datasets.getDataPageDatasetsSetNameDataPageGet(
                data_rep.set_name,
                { offset, limit: BATCH_SIZE },
            );
            if (seq !== load_seq) return;
            if (!res.data.indices.length) break;
            indices.push(...res.data.indices);
            rows.push(...res.data.inputs);
            redraw();
            if (res.data.indices.length < BATCH_SIZE) break;
        }
    } catch (error) {
        console.error('Error loading data for scatterplot matrix:', error);
        if (seq === load_seq) rows = [];
    } finally {
        if (seq === load_seq) state.loading = false;
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
            .data(rows)
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

// The KNN-interpolated background, rasterized to a small canvas and embedded as one <image> -
// far cheaper than one <rect> per grid cell, and it gives a smooth gradient look matching the
// heatmaps in hilti_exp.py's exploratory version of this feature.
function drawBackground(
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    cell: { row: string; col: string },
    inner_w: number,
    inner_h: number,
) {
    const bg = state.background;
    if (!bg || bg.var1 !== cell.col || bg.var2 !== cell.row) return;
    const grid = background_mode === 'shap' ? bg.shap_effect : bg.predictions;
    const res_y = grid.length;
    const res_x = grid[0]?.length ?? 0;
    if (!res_y || !res_x) return;

    const [lo, hi] = d3.extent(grid.flat()) as [number, number];
    const domain: [number, number] = (lo === undefined || hi === undefined || lo === hi) ? [0, 1] : [lo, hi];
    const color = d3.scaleSequential().domain(domain).interpolator(colormaps_d3['Roma']);

    const canvas = document.createElement('canvas');
    canvas.width = res_x;
    canvas.height = res_y;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const img = ctx.createImageData(res_x, res_y);
    for (let i = 0; i < res_y; i++) {
        // Grid rows run low->high on var2 (bg.y); canvas rows run top->bottom, and the popover's
        // y_scale puts high values at the top - flip rows here so the two line up.
        const src_row = res_y - 1 - i;
        for (let j = 0; j < res_x; j++) {
            const c = d3.rgb(color(grid[src_row][j]));
            const idx = (i * res_x + j) * 4;
            img.data[idx] = c.r;
            img.data[idx + 1] = c.g;
            img.data[idx + 2] = c.b;
            img.data[idx + 3] = 255;
        }
    }
    ctx.putImageData(img, 0, 0);

    g.append('image')
        .attr('href', canvas.toDataURL())
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', inner_w)
        .attr('height', inner_h)
        .attr('preserveAspectRatio', 'none')
        .attr('opacity', 0.9);

    g.append('text')
        .attr('class', 'splom-bg-caption')
        .attr('x', 0)
        .attr('y', -4)
        .attr('font-size', 8)
        .attr('fill', '#555')
        .text(`background: ${background_mode === 'shap' ? 'SHAP effect' : 'model output'} (${lo.toFixed(2)}–${hi.toFixed(2)})`);
}

function drawPopover() {
    if (!popoverPlot.value) return;
    const cell = popover_cell.value;
    const svg = d3.select(popoverPlot.value);
    if (!cell || !rows.length) {
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

    // Drawn first (behind the axes/points appended below) - the KNN-interpolated model
    // output/SHAP-effect surface for this pair, when it's finished loading.
    drawBackground(g, cell, inner_w, inner_h);

    const isHighlighted = (r: number[], i: number) =>
        highlight_point_index != null && i === highlight_point_index;

    const points = g.selectAll('circle')
        .data(rows)
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
watch(() => rows, () => nextTick(drawPopover));
watch(() => highlight_point_index, () => nextTick(drawPopover));
watch(() => state.background, () => nextTick(drawPopover));
// Both fields are already in whatever's cached for the current pair, so a mode flip only needs a
// re-render - never a re-fetch.
watch(() => background_mode, () => nextTick(drawPopover));

// Debounced so quickly sweeping the mouse across the matrix doesn't fire a request per cell -
// only the cell the pointer settles on for a beat actually gets fetched.
watch([popover_cell, () => output_col], ([cell]) => {
    if (background_timer) clearTimeout(background_timer);
    if (!cell || !output_col) {
        state.background = null;
        return;
    }
    const cached = background_cache.get(backgroundKey(cell.col, cell.row));
    if (cached) {
        state.background = cached;
        return;
    }
    state.background = null;
    background_timer = setTimeout(() => fetchBackground(cell), BG_FETCH_DEBOUNCE_MS);
});

let resize_observer: ResizeObserver | null = null;
onMounted(() => {
    if (container.value) {
        resize_observer = new ResizeObserver(() => redraw());
        resize_observer.observe(container.value);
    }
});
onBeforeUnmount(() => {
    if (background_timer) clearTimeout(background_timer);
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

.splom-loading-bar {
    width: 100%;
    max-width: 320px;
    margin: 8px 0;
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
