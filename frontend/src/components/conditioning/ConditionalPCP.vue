<template>
    <div class="cpcp-container" ref="container">
        <svg ref="plot"></svg>
    </div>
</template>

<script lang="ts" setup>
import { onBeforeUnmount, onMounted, useTemplateRef, watch } from 'vue';
import * as d3 from 'd3';
import type { ConditionResult, UncertaintyAttribution } from '../../api/Api';
import { CondValue, confidenceOf, PRED_COLOR, OUTPUT_COLOR, INPUT_COLOR, COND_COLOR, attributionCap } from './types';

/**
 * Parallel coordinates over every column (inputs, then outputs) of a dataset.
 *  - drag (brush) along an axis to condition that column on a range,
 *  - double click an axis to condition it on a single value (drag the diamond to move it,
 *    double click the diamond to remove it),
 *  - the GP-VAE prediction is drawn as mixture samples + mean line + a mean +- std band between
 *    each pair of neighbouring axes; the opacity of everything between two axes encodes how
 *    certain the prediction is there (1 - posterior std / data std, averaged over both axes).
 *  - with an attribution for the detail column, a small bar under each axis label shows how much
 *    that column's condition reduces (red) / pinning it would reduce (blue) σ of the detail column.
 */
const props = defineProps<{
    columns: string[];
    output_cols: string[];
    domains: Record<string, [number, number]>;
    data_rows: number[][];
    result: ConditionResult | null;
    conditions: Record<string, CondValue>;
    hover_column: string | null;
    /** linked highlight (e.g. a hovered attribution row) */
    highlight?: string | null;
    /** attribution of the detail column: drawn as a small bar under each axis label */
    attribution?: UncertaintyAttribution | null;
}>();
const emit = defineEmits<{
    (e: 'update-condition', column: string, value: CondValue | null): void;
    (e: 'hover', column: string | null): void;
}>();

const container = useTemplateRef('container');
const plot = useTemplateRef('plot');

const MARGIN = { top: 46, right: 40, bottom: 34, left: 40 };
const HEIGHT = 440;

let x: d3.ScalePoint<string> = d3.scalePoint();
let y: Record<string, d3.ScaleLinear<number, number>> = {};
let brushes: Record<string, d3.BrushBehavior<unknown>> = {};

function cssSafe(dim: string): string {
    return dim.replace(/[^a-zA-Z0-9_-]/g, '_');
}

function rowMatches(row: number[]): boolean {
    for (let i = 0; i < props.columns.length; i++) {
        const c = props.conditions[props.columns[i]];
        if (!c) continue;
        const [lo, hi] = props.domains[props.columns[i]];
        const half = Math.max(c.width / 2, (hi - lo) * 0.03);
        if (Math.abs(row[i] - c.value) > half) return false;
    }
    return true;
}

function drawStatic() {
    if (!plot.value || !container.value || !props.columns.length) return;
    const width = Math.max(container.value.clientWidth, 120 * props.columns.length);
    const svg = d3.select(plot.value).attr('width', width).attr('height', HEIGHT);
    svg.selectAll('*').remove();

    x = d3.scalePoint<string>().domain(props.columns).range([MARGIN.left + 30, width - MARGIN.right]);
    y = {};
    for (const col of props.columns) {
        const [lo, hi] = props.domains[col] ?? [0, 1];
        const pad = (hi - lo) * 0.05 || 1;
        y[col] = d3.scaleLinear().domain([lo - pad, hi + pad]).range([HEIGHT - MARGIN.bottom, MARGIN.top]);
    }

    svg.append('g').attr('class', 'data-layer');
    svg.append('g').attr('class', 'pred-layer');
    const axes = svg.append('g').attr('class', 'axes-layer');
    svg.append('g').attr('class', 'attr-layer');
    svg.append('g').attr('class', 'handle-layer');

    const step = x.step();
    brushes = {};
    for (const col of props.columns) {
        const is_out = props.output_cols.includes(col);
        const g = axes.append('g')
            .attr('class', `axis axis-${cssSafe(col)}`)
            .attr('transform', `translate(${x(col)},0)`)
            .on('mouseenter', () => emit('hover', col))
            .on('mouseleave', () => emit('hover', null));
        g.append('rect')
            .attr('class', 'hover-bg')
            .attr('x', -step / 2).attr('width', step)
            .attr('y', 4).attr('height', HEIGHT - 8)
            .attr('fill', 'transparent');
        g.append('g').call(d3.axisLeft(y[col]).ticks(6).tickSize(4))
            .call(sel => sel.selectAll('text').attr('font-size', 9))
            .call(sel => sel.select('.domain').attr('stroke', '#777'));
        g.append('text')
            .attr('class', 'axis-label')
            .attr('y', 14).attr('text-anchor', 'middle')
            .attr('font-size', 11).attr('font-weight', 600)
            .attr('fill', is_out ? OUTPUT_COLOR : INPUT_COLOR)
            .text(col);
        g.append('text')
            .attr('class', `axis-unc axis-unc-${cssSafe(col)}`)
            .attr('y', 28).attr('text-anchor', 'middle')
            .attr('font-size', 9).attr('fill', '#666');

        const brush = d3.brushY<unknown>()
            .extent([[-11, MARGIN.top], [11, HEIGHT - MARGIN.bottom]])
            .on('brush end', (event: d3.D3BrushEvent<unknown>) => {
                if (!event.sourceEvent) return;
                const sel = event.selection as [number, number] | null;
                if (!sel) {
                    const existing = props.conditions[col];
                    if (existing && existing.width > 0) emit('update-condition', col, null);
                    return;
                }
                const a = y[col].invert(sel[1]);
                const b = y[col].invert(sel[0]);
                emit('update-condition', col, { value: (a + b) / 2, width: Math.abs(b - a) });
            });
        brushes[col] = brush as d3.BrushBehavior<unknown>;
        const bg = g.append('g').attr('class', `brush brush-${cssSafe(col)}`).call(brush);
        bg.select('.overlay').attr('fill', 'transparent').attr('stroke', 'none');
        bg.select('.selection').attr('fill', '#d1495b').attr('fill-opacity', 0.18)
            .attr('stroke', '#d1495b').attr('stroke-width', 1);
        bg.selectAll('.handle').attr('fill', 'transparent');
        bg.on('dblclick', (event: MouseEvent) => {
            const [, py] = d3.pointer(event, g.node());
            bg.call(brush.move as any, null);
            emit('update-condition', col, { value: y[col].invert(py), width: 0 });
        });
    }
    syncBrushes();
    drawData();
    drawPrediction();
    drawAttribution();
}

function drawHighlight() {
    if (!plot.value) return;
    // linked highlight: thicker, darker axis line (a filled background would cover the lines)
    for (const col of props.columns) {
        const hl = !!props.highlight && col === props.highlight;
        d3.select(plot.value).select(`g.axis-${cssSafe(col)} .domain`)
            .attr('stroke', hl ? '#111' : '#777').attr('stroke-width', hl ? 3 : 1);
        d3.select(plot.value).select(`g.axis-${cssSafe(col)} text.axis-label`)
            .attr('text-decoration', hl ? 'underline' : null);
    }
}

function drawAttribution() {
    if (!plot.value) return;
    const layer = d3.select(plot.value).select('g.attr-layer');
    layer.selectAll('*').remove();
    drawHighlight();
    const a = props.attribution;
    if (!a || a.target !== props.hover_column) return;
    const base = a.base_std || 1e-12;
    const rel = a.columns.map((_, k) => {
        const v = a.kind[k] === 'conditioned' ? a.condition_effect[k] : a.kind[k] === 'free' ? a.pin_gain[k] : null;
        return v == null ? null : v / base;
    });
    const vmax = attributionCap(rel, a.kind);
    const maxW = Math.min(44, x.step() * 0.45);
    a.columns.forEach((col, k) => {
        const cx = x(col);
        const v = rel[k];
        if (cx === undefined || v == null || v <= 0.002) return;
        const w = Math.max(1.5, maxW * Math.min(1, v / vmax));
        layer.append('rect')
            .attr('class', `attr-ind attr-ind-${cssSafe(col)}`)
            .attr('x', cx - w / 2).attr('width', w)
            .attr('y', 33).attr('height', 3).attr('rx', 1)
            .attr('fill', a.kind[k] === 'conditioned' ? COND_COLOR : PRED_COLOR)
            .attr('opacity', 0.8)
            .append('title').text(a.kind[k] === 'conditioned'
                ? `condition on ${col} reduces σ(${a.target}) by ${d3.format('.1~%')(v)}`
                : `pinning ${col} would reduce σ(${a.target}) by ≈ ${d3.format('.1~%')(v)}`);
    });
}

function syncBrushes() {
    if (!plot.value) return;
    const svg = d3.select(plot.value);
    for (const col of props.columns) {
        const brush = brushes[col];
        if (!brush) continue;
        const c = props.conditions[col];
        const g = svg.select<SVGGElement>(`g.brush-${cssSafe(col)}`);
        const current = d3.brushSelection(g.node() as SVGGElement) as [number, number] | null;
        if (c && c.width > 0) {
            const target: [number, number] = [y[col](c.value + c.width / 2), y[col](c.value - c.width / 2)];
            if (!current || Math.abs(current[0] - target[0]) > 0.5 || Math.abs(current[1] - target[1]) > 0.5) {
                g.call(brush.move as any, target);
            }
        } else if (current) {
            g.call(brush.move as any, null);
        }
    }
}

function lineFor(values: number[]): string {
    return d3.line<number>()
        .x((_, i) => x(props.columns[i]) as number)
        .y((v, i) => y[props.columns[i]](v))(values) ?? '';
}

function drawData() {
    if (!plot.value) return;
    const has_cond = Object.keys(props.conditions).length > 0;
    d3.select(plot.value).select('g.data-layer')
        .selectAll<SVGPathElement, number[]>('path')
        .data(props.data_rows)
        .join('path')
        .attr('d', d => lineFor(d))
        .attr('fill', 'none')
        .attr('stroke', d => has_cond && rowMatches(d) ? '#4d4d4d' : '#b9b9b9')
        .attr('stroke-width', 0.7)
        .attr('opacity', d => has_cond ? (rowMatches(d) ? 0.35 : 0.05) : 0.12);
}

function drawPrediction() {
    if (!plot.value) return;
    const svg = d3.select(plot.value);
    const layer = svg.select('g.pred-layer');
    layer.selectAll('*').remove();
    const handles = svg.select('g.handle-layer');
    handles.selectAll('*').remove();
    const res = props.result;
    if (!res) return;
    const idx = props.columns.map(c => res.columns.indexOf(c));
    if (idx.some(i => i < 0)) return;
    const mean = idx.map(i => res.mean[i]);
    const std = idx.map(i => res.std[i]);
    const conf = idx.map(i => confidenceOf(res, i));

    // --- bands + per segment opacity between neighbouring axes
    for (let s = 0; s < props.columns.length - 1; s++) {
        const c0 = props.columns[s], c1 = props.columns[s + 1];
        const x0 = x(c0) as number, x1 = x(c1) as number;
        const pair = (conf[s] + conf[s + 1]) / 2;
        const band = [
            [x0, y[c0](mean[s] + std[s])], [x1, y[c1](mean[s + 1] + std[s + 1])],
            [x1, y[c1](mean[s + 1] - std[s + 1])], [x0, y[c0](mean[s] - std[s])],
        ];
        layer.append('path')
            .attr('class', 'pred-band')
            .attr('d', 'M' + band.map(p => p.join(',')).join('L') + 'Z')
            .attr('fill', PRED_COLOR)
            .attr('opacity', 0.06 + 0.3 * pair);
        const seg = layer.append('g').attr('class', 'pred-samples');
        for (const sample of res.samples) {
            const v0 = sample[idx[s]], v1 = sample[idx[s + 1]];
            seg.append('line')
                .attr('x1', x0).attr('x2', x1)
                .attr('y1', y[c0](v0)).attr('y2', y[c1](v1))
                .attr('stroke', PRED_COLOR)
                .attr('stroke-width', 0.8)
                .attr('opacity', 0.03 + 0.22 * pair);
        }
        layer.append('line')
            .attr('class', 'pred-mean')
            .attr('x1', x0).attr('x2', x1)
            .attr('y1', y[c0](mean[s])).attr('y2', y[c1](mean[s + 1]))
            .attr('stroke', PRED_COLOR)
            .attr('stroke-width', 2.6)
            .attr('stroke-linecap', 'round')
            .attr('opacity', 0.2 + 0.8 * pair);
    }

    // --- per axis error bar + label
    props.columns.forEach((col, s) => {
        const cx = x(col) as number;
        const hovered = props.hover_column === col;
        layer.append('rect')
            .attr('class', 'pred-errbar')
            .attr('x', cx - (hovered ? 6 : 4)).attr('width', hovered ? 12 : 8)
            .attr('y', y[col](mean[s] + std[s]))
            .attr('height', Math.max(1, y[col](mean[s] - std[s]) - y[col](mean[s] + std[s])))
            .attr('fill', PRED_COLOR)
            .attr('stroke', hovered ? '#111' : 'none')
            .attr('opacity', 0.25 + 0.6 * conf[s]);
        svg.select(`text.axis-unc-${cssSafe(col)}`)
            .text(props.conditions[col] ? 'conditioned' : `σ ${d3.format('.3~g')(std[s])}`)
            .attr('font-weight', hovered ? 700 : 400);

        const c = props.conditions[col];
        if (c && c.width === 0) {
            const drag = d3.drag<SVGPathElement, unknown>()
                .on('drag', (event) => {
                    const v = Math.min(Math.max(y[col].invert(event.y), y[col].domain()[0]), y[col].domain()[1]);
                    d3.select(event.sourceEvent.target).attr('transform', `translate(${cx},${y[col](v)})`);
                    emit('update-condition', col, { value: v, width: 0 });
                });
            handles.append('path')
                .attr('class', 'cond-handle')
                .attr('d', d3.symbol(d3.symbolDiamond, 150)())
                .attr('transform', `translate(${cx},${y[col](c.value)})`)
                .attr('fill', '#d1495b').attr('stroke', '#fff').attr('stroke-width', 1.5)
                .style('cursor', 'ns-resize')
                .on('dblclick', (event: MouseEvent) => {
                    event.stopPropagation();
                    emit('update-condition', col, null);
                })
                .on('mouseenter', () => emit('hover', col))
                .call(drag as any)
                .append('title').text(`${col} = ${d3.format('.4~g')(c.value)} (drag to move, double click to remove)`);
        }
    });
}

watch(() => [props.columns, props.domains], drawStatic, { deep: true });
watch(() => props.data_rows, drawData);
watch(() => props.conditions, () => { syncBrushes(); drawData(); drawPrediction(); }, { deep: true });
watch(() => [props.result, props.hover_column], drawPrediction);
watch(() => [props.attribution, props.hover_column, props.highlight], drawAttribution);

let observer: ResizeObserver | null = null;
let last_width = 0;
onMounted(() => {
    drawStatic();
    if (container.value) {
        observer = new ResizeObserver(() => {
            const w = container.value?.clientWidth ?? 0;
            if (Math.abs(w - last_width) > 2) {
                last_width = w;
                drawStatic();
            }
        });
        observer.observe(container.value);
    }
});
onBeforeUnmount(() => observer?.disconnect());
</script>

<style scoped>
.cpcp-container {
    width: 100%;
    overflow-x: auto;
}
</style>
