<template>
    <div class="beeswarm-chart" ref="container">
        <svg ref="plot" :width="dims.width" :height="dims.height"></svg>
        <div class="beeswarm-tooltip" v-if="state.tooltip"
            :style="{ left: state.tooltip.x + 'px', top: state.tooltip.y + 'px' }">
            <div><b>{{ state.tooltip.row }}</b></div>
            <div>value: {{ state.tooltip.value.toFixed(4) }}</div>
            <div v-if="state.tooltip.color !== null">{{ color_label || 'feature value' }}: {{
                state.tooltip.color?.toFixed(4) }}</div>
            <div v-if="state.tooltip.index !== null">index: {{ state.tooltip.index }}</div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { reactive, useTemplateRef, watch, onMounted, onBeforeUnmount } from 'vue';
import * as d3 from 'd3';
import { colormaps_d3 } from '../helpers/colormaps';
import { BeeswarmRow } from './types';

const emit = defineEmits<{
    (e: 'hover-row', features: string[] | null): void;
    // The dataset-level row index (row.indices[i]) of the specific point hovered, or null when
    // no point is hovered - lets consumers (e.g. the scatterplot matrix's popover) highlight that
    // same data point, when it happens to also be in whatever sample they're showing.
    (e: 'hover-point', index: number | null): void;
}>();
const { rows, row_height, color_label, colormap } = defineProps({
    rows: {
        type: Array as () => BeeswarmRow[],
        default: () => [],
    },
    row_height: {
        type: Number,
        default: 28,
    },
    color_label: {
        type: String,
        default: '',
    },
    colormap: {
        type: String,
        default: 'Roma',
    },
});

const container = useTemplateRef('container');
const plot = useTemplateRef('plot');

const margin = { top: 24, right: 56, bottom: 28, left: 16 };
const label_width = 140;
const legend_width = 10;
const legend_gap = 14;
const legend_max_height = 160;
const legend_gradient_id = `beeswarm-legend-${Math.random().toString(36).slice(2)}`;

const dims = reactive({ width: 600, height: 200 });

const state = reactive({
    tooltip: null as null | { x: number; y: number; row: string; value: number; color: number | null; index: number | null },
});

function colorScaleFor(row: BeeswarmRow) {
    const values = row.color_values && row.color_values.length ? row.color_values : row.values;
    const [lo, hi] = d3.extent(values) as [number, number];
    const domain = (lo === undefined || hi === undefined || lo === hi) ? [0, 1] : [lo, hi];
    return d3.scaleSequential().domain(domain).interpolator(colormaps_d3[colormap] || colormaps_d3['Roma']);
}

function redraw() {
    if (!plot.value || !container.value) return;
    const width = Math.max(320, container.value.clientWidth);
    const plot_width = Math.max(80, width - margin.left - margin.right - label_width);
    const height = margin.top + margin.bottom + rows.length * row_height;
    dims.width = width;
    dims.height = height;

    const svg = d3.select(plot.value);
    svg.selectAll('*').remove();

    const all_values = rows.flatMap(r => r.values);
    const [lo, hi] = d3.extent(all_values) as [number, number];
    const pad = ((hi ?? 1) - (lo ?? 0)) * 0.08 || 1;
    const x = d3.scaleLinear()
        .domain([(lo ?? 0) - pad, (hi ?? 0) + pad])
        .range([0, plot_width]);

    const g = svg.append('g').attr('transform', `translate(${margin.left + label_width}, ${margin.top})`);

    // zero reference line
    g.append('line')
        .attr('x1', x(0)).attr('x2', x(0))
        .attr('y1', 0).attr('y2', rows.length * row_height)
        .attr('stroke', '#bbb')
        .attr('stroke-dasharray', '3,3');

    // x axis
    svg.append('g')
        .attr('transform', `translate(${margin.left + label_width}, ${margin.top + rows.length * row_height})`)
        .call(d3.axisBottom(x).ticks(6).tickSize(4))
        .call(sel => sel.select('.domain').attr('stroke', '#999'));

    const n_bins = Math.max(10, Math.min(50, Math.round(plot_width / 6)));
    const bin_width = plot_width / n_bins;
    const max_offset = row_height / 2 - 2;
    const dot_r = 2;
    const dot_space_adjust = 10 / Math.max(1, rows[0]?.values.length ?? 1);
    const dot_spacing = dot_r * dot_space_adjust + 0.5;

    rows.forEach((row, row_idx) => {
        const row_g = g.append('g').attr('class', 'beeswarm-row');
        const row_center = row_idx * row_height + row_height / 2;

        const emitRowEnter = () => emit('hover-row', row.features && row.features.length ? row.features : [row.key]);
        const emitRowLeave = () => emit('hover-row', null);

        // Full-row invisible hit target (spans the label + plot area) so hovering anywhere on
        // the row - not just directly over a dot - reports which feature(s) it represents.
        row_g.append('rect')
            .attr('x', -label_width)
            .attr('y', row_idx * row_height)
            .attr('width', label_width + plot_width)
            .attr('height', row_height)
            .attr('fill', 'transparent')
            .style('pointer-events', 'all')
            .on('mouseenter', emitRowEnter)
            .on('mouseleave', emitRowLeave);

        row_g.append('text')
            .attr('x', -label_width + 4)
            .attr('y', row_center)
            .attr('alignment-baseline', 'middle')
            .attr('font-size', 11)
            .text(row.label);

        const color_scale = colorScaleFor(row);
        const color_values = row.color_values && row.color_values.length ? row.color_values : row.values;

        if (row.kind === 'path') {
            const line = d3.line<number>()
                .x(v => x(v))
                .y(() => row_center);
            row_g.append('path')
                .attr('d', line(row.values))
                .attr('fill', 'none')
                .attr('stroke', '#333')
                .attr('stroke-width', 1.2);

            row_g.selectAll('circle')
                .data(d3.range(row.values.length))
                .join('circle')
                .attr('cx', i => x(row.values[i]))
                .attr('cy', row_center)
                .attr('r', i => i === 0 || i === row.values.length - 1 ? 4.5 : 3)
                .attr('fill', i => color_scale(color_values[i] ?? row.values[i]) as string)
                .attr('stroke', i => i === 0 || i === row.values.length - 1 ? '#000' : 'none')
                .attr('stroke-width', 1)
                .on('mousemove', (event: MouseEvent, i: number) => {
                    showTooltip(event, row.label, row.values[i], color_values[i] ?? null, row.indices?.[i] ?? null);
                })
                .on('mouseenter', (event: MouseEvent, i: number) => {
                    // Dots are siblings of the row's hit-rect above, not descendants of it, so
                    // the browser fires the rect's mouseleave the instant the pointer lands on a
                    // dot (mouseleave fires whenever the new hover target isn't a descendant of
                    // the element being left) - re-assert the row-level hover here so hovering a
                    // point doesn't also clear the row highlight/popover it's meant to appear in.
                    emitRowEnter();
                    emit('hover-point', row.indices?.[i] ?? null);
                })
                .on('mouseleave', () => {
                    state.tooltip = null;
                    emitRowLeave();
                    emit('hover-point', null);
                });
            return;
        }

        // bin by x position for a lightweight beeswarm jitter
        const buckets: number[][] = Array.from({ length: n_bins + 1 }, () => []);
        row.values.forEach((v, i) => {
            const bucket = Math.max(0, Math.min(n_bins, Math.round(x(v) / bin_width)));
            buckets[bucket].push(i);
        });

        const points: { i: number; x: number; y: number }[] = [];
        buckets.forEach(idxs => {
            idxs.forEach((i, order) => {
                const offset = (order - (idxs.length - 1) / 2) * dot_spacing;
                points.push({ i, x: x(row.values[i]), y: row_center + Math.max(-max_offset, Math.min(max_offset, offset)) });
            });
        });

        row_g.selectAll('circle')
            .data(points)
            .join('circle')
            .attr('cx', d => d.x)
            .attr('cy', d => d.y)
            .attr('r', dot_r)
            .attr('fill', d => color_scale(color_values[d.i]) as string)
            .attr('opacity', 0.85)
            .on('mousemove', (event: MouseEvent, d) => {
                showTooltip(event, row.label, row.values[d.i], color_values[d.i] ?? null, row.indices?.[d.i] ?? null);
            })
            .on('mouseenter', (event: MouseEvent, d) => {
                // see the comment on the equivalent handler in the 'path' branch above.
                emitRowEnter();
                emit('hover-point', row.indices?.[d.i] ?? null);
            })
            .on('mouseleave', () => {
                state.tooltip = null;
                emitRowLeave();
                emit('hover-point', null);
            });
    });

    // Color legend: each row's dots are colored on that row's own value range (see
    // colorScaleFor), so this is a relative Low->High indicator of the colormap - not a shared
    // absolute scale across rows - mirroring how SHAP's own summary plot labels its colorbar.
    if (rows.length) {
        const total_height = rows.length * row_height;
        const legend_height = Math.min(total_height, legend_max_height);
        const legend_y = (total_height - legend_height) / 2;
        const interpolator = colormaps_d3[colormap] || colormaps_d3['Roma'];

        const defs = svg.append('defs');
        const gradient = defs.append('linearGradient')
            .attr('id', legend_gradient_id)
            .attr('x1', '0').attr('x2', '0')
            .attr('y1', '1').attr('y2', '0');
        d3.range(0, 1.0001, 0.1).forEach(t => {
            gradient.append('stop').attr('offset', `${t * 100}%`).attr('stop-color', interpolator(t));
        });

        const legend_g = g.append('g')
            .attr('class', 'beeswarm-legend')
            .attr('transform', `translate(${plot_width + legend_gap}, ${legend_y})`);

        legend_g.append('rect')
            .attr('width', legend_width)
            .attr('height', legend_height)
            .attr('fill', `url(#${legend_gradient_id})`)
            .attr('stroke', '#999')
            .attr('stroke-width', 0.5);

        legend_g.append('text')
            .attr('x', legend_width + 4)
            .attr('y', 8)
            .attr('font-size', 9)
            .attr('fill', '#444')
            .text('High');

        legend_g.append('text')
            .attr('x', legend_width + 4)
            .attr('y', legend_height - 2)
            .attr('font-size', 9)
            .attr('fill', '#444')
            .text('Low');

        legend_g.append('text')
            .attr('transform', `translate(${legend_width + 16}, ${legend_height / 2}) rotate(90)`)
            .attr('text-anchor', 'middle')
            .attr('font-size', 9)
            .attr('fill', '#444')
            .text(color_label || 'value');
    }
}

function showTooltip(event: MouseEvent, row: string, value: number, color: number | null, index: number | null) {
    const rect = container.value?.getBoundingClientRect();
    state.tooltip = {
        x: (event.clientX - (rect?.left ?? 0)) + 12,
        y: (event.clientY - (rect?.top ?? 0)) + 12,
        row, value, color, index,
    };
}

let resize_observer: ResizeObserver | null = null;
onMounted(() => {
    redraw();
    if (container.value) {
        resize_observer = new ResizeObserver(() => redraw());
        resize_observer.observe(container.value);
    }
});
onBeforeUnmount(() => {
    resize_observer?.disconnect();
});
watch(() => rows, () => redraw(), { deep: true });
</script>

<style scoped>
.beeswarm-chart {
    position: relative;
    width: 100%;
}

.beeswarm-tooltip {
    position: absolute;
    pointer-events: none;
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
    white-space: nowrap;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
    z-index: 10;
}
</style>
