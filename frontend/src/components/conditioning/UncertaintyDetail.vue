<template>
    <div class="ud-container" v-if="result">
        <div class="ud-panel ud-density">
            <h3>
                <span :style="{ color: is_output ? OUTPUT_COLOR : INPUT_COLOR }">{{ column ?? '-' }}</span>
                <span class="ud-sub" v-if="column"> - {{ is_conditioned ? 'conditioned' : 'predicted' }}
                    {{ is_output ? 'output' : 'input' }}</span>
            </h3>
            <p class="ud-stats" v-if="stats">
                mean <b>{{ fmt(stats.mean) }}</b> · σ <b>{{ fmt(stats.std) }}</b>
                · 95% [{{ fmt(stats.mean - 1.96 * stats.std) }}, {{ fmt(stats.mean + 1.96 * stats.std) }}]
                · σ / σ<sub>data</sub> <b>{{ fmt(stats.rel * 100) }}%</b>
            </p>
            <svg ref="density"></svg>
            <p class="ud-legend">
                <span class="sw" :style="{ background: PRED_COLOR }"></span> GP-VAE posterior density
                <span class="sw" style="background: #bbb"></span> data distribution
                <span class="sw" style="background: #d1495b"></span> condition
            </p>
        </div>
        <div class="ud-panel">
            <h3>Uncertainty per parameter</h3>
            <p class="ud-sub">posterior σ relative to the data σ (hover a bar or an axis)</p>
            <svg ref="bars"></svg>
        </div>
        <div class="ud-panel">
            <h3>Posterior correlation with {{ column ?? '-' }}</h3>
            <p class="ud-sub">how the remaining uncertainty of the other parameters co-varies</p>
            <svg ref="corr"></svg>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, useTemplateRef, watch } from 'vue';
import * as d3 from 'd3';
import type { ConditionResult } from '../../api/Api';
import { CondValue, relUncertainty, PRED_COLOR, INPUT_COLOR, OUTPUT_COLOR } from './types';

const props = defineProps<{
    result: ConditionResult | null;
    column: string | null;
    columns: string[];
    output_cols: string[];
    data_rows: number[][];
    conditions: Record<string, CondValue>;
}>();
const emit = defineEmits<{ (e: 'hover', column: string | null): void }>();

const density = useTemplateRef('density');
const bars = useTemplateRef('bars');
const corr = useTemplateRef('corr');

const fmt = d3.format('.4~g');
const ci = computed(() => (props.result && props.column) ? props.result.columns.indexOf(props.column) : -1);
const is_output = computed(() => !!props.column && props.output_cols.includes(props.column));
const is_conditioned = computed(() => !!props.column && !!props.conditions[props.column]);
const stats = computed(() => {
    const r = props.result;
    const i = ci.value;
    if (!r || i < 0) return null;
    return { mean: r.mean[i], std: r.std[i], rel: relUncertainty(r, i) };
});

function drawDensity() {
    if (!density.value) return;
    const W = 460, H = 200, M = { t: 10, r: 14, b: 26, l: 14 };
    const svg = d3.select(density.value).attr('width', W).attr('height', H);
    svg.selectAll('*').remove();
    const r = props.result;
    const i = ci.value;
    const col_idx = props.column ? props.columns.indexOf(props.column) : -1;
    if (!r || i < 0) return;
    const grid = r.grid[i];
    const dens = r.density[i];
    const xs = d3.scaleLinear().domain([grid[0], grid[grid.length - 1]]).range([M.l, W - M.r]);

    // data histogram as a density on the same axis
    const vals = col_idx >= 0 ? props.data_rows.map(row => row[col_idx]) : [];
    const bins = d3.bin().domain(xs.domain() as [number, number]).thresholds(30)(vals);
    const hist = bins.map(b => ({ x0: b.x0!, x1: b.x1!, d: vals.length ? b.length / vals.length / ((b.x1! - b.x0!) || 1) : 0 }));
    const ymax = Math.max(d3.max(dens) ?? 1, d3.max(hist, h => h.d) ?? 1);
    const ys = d3.scaleLinear().domain([0, ymax * 1.05]).range([H - M.b, M.t]);

    svg.append('g').selectAll('rect').data(hist).join('rect')
        .attr('x', h => xs(h.x0) + 0.5).attr('width', h => Math.max(0, xs(h.x1) - xs(h.x0) - 1))
        .attr('y', h => ys(h.d)).attr('height', h => ys(0) - ys(h.d))
        .attr('fill', '#ccc');

    const m = r.mean[i], s = r.std[i];
    svg.append('rect').attr('x', xs(m - 1.96 * s)).attr('width', Math.max(1, xs(m + 1.96 * s) - xs(m - 1.96 * s)))
        .attr('y', M.t).attr('height', H - M.b - M.t).attr('fill', PRED_COLOR).attr('opacity', 0.08);
    svg.append('rect').attr('x', xs(m - s)).attr('width', Math.max(1, xs(m + s) - xs(m - s)))
        .attr('y', M.t).attr('height', H - M.b - M.t).attr('fill', PRED_COLOR).attr('opacity', 0.12);

    const pts = grid.map((g, k) => [g, dens[k]] as [number, number]);
    svg.append('path').datum(pts)
        .attr('d', d3.area<[number, number]>().x(p => xs(p[0])).y0(ys(0)).y1(p => ys(p[1])).curve(d3.curveMonotoneX))
        .attr('fill', PRED_COLOR).attr('opacity', 0.35);
    svg.append('path').datum(pts)
        .attr('d', d3.line<[number, number]>().x(p => xs(p[0])).y(p => ys(p[1])).curve(d3.curveMonotoneX))
        .attr('fill', 'none').attr('stroke', PRED_COLOR).attr('stroke-width', 2);
    svg.append('line').attr('x1', xs(m)).attr('x2', xs(m)).attr('y1', M.t).attr('y2', H - M.b)
        .attr('stroke', PRED_COLOR).attr('stroke-dasharray', '4 3');

    const c = props.column ? props.conditions[props.column] : undefined;
    if (c) {
        if (c.width > 0) {
            svg.append('rect').attr('x', xs(c.value - c.width / 2)).attr('width', Math.max(2, xs(c.value + c.width / 2) - xs(c.value - c.width / 2)))
                .attr('y', H - M.b - 6).attr('height', 6).attr('fill', '#d1495b');
        } else {
            svg.append('line').attr('x1', xs(c.value)).attr('x2', xs(c.value)).attr('y1', M.t).attr('y2', H - M.b)
                .attr('stroke', '#d1495b').attr('stroke-width', 2);
        }
    }
    svg.append('g').attr('transform', `translate(0,${H - M.b})`).call(d3.axisBottom(xs).ticks(6))
        .call(g => g.selectAll('text').attr('font-size', 9));
}

function drawBars() {
    if (!bars.value) return;
    const r = props.result;
    const rowH = 18, W = 360, L = 70;
    const H = props.columns.length * rowH + 24;
    const svg = d3.select(bars.value).attr('width', W).attr('height', H);
    svg.selectAll('*').remove();
    if (!r) return;
    const xs = d3.scaleLinear().domain([0, 1]).range([L, W - 40]);
    props.columns.forEach((col, k) => {
        const i = r.columns.indexOf(col);
        const rel = relUncertainty(r, i);
        const cond = !!props.conditions[col];
        const hovered = col === props.column;
        const g = svg.append('g').attr('transform', `translate(0,${k * rowH + 4})`)
            .style('cursor', 'pointer')
            .on('mouseenter', () => emit('hover', col))
            .on('mouseleave', () => emit('hover', null));
        g.append('rect').attr('x', 0).attr('width', W).attr('height', rowH).attr('fill', hovered ? '#eef3fa' : 'transparent');
        g.append('text').attr('x', L - 6).attr('y', rowH / 2 + 4).attr('text-anchor', 'end').attr('font-size', 10)
            .attr('font-weight', hovered ? 700 : 400)
            .attr('fill', props.output_cols.includes(col) ? OUTPUT_COLOR : INPUT_COLOR).text(col);
        g.append('rect').attr('x', xs(0)).attr('y', 3).attr('height', rowH - 6)
            .attr('width', Math.max(1, xs(rel) - xs(0)))
            .attr('fill', cond ? '#d1495b' : PRED_COLOR)
            .attr('opacity', 0.35 + 0.65 * rel);
        g.append('text').attr('x', xs(rel) + 4).attr('y', rowH / 2 + 4).attr('font-size', 9).attr('fill', '#555')
            .text(cond ? 'cond.' : `${Math.round(rel * 100)}%`);
    });
    svg.append('g').attr('transform', `translate(0,${props.columns.length * rowH + 4})`)
        .call(d3.axisBottom(xs).ticks(4).tickFormat(d3.format('.0%')))
        .call(g => g.selectAll('text').attr('font-size', 9));
}

function drawCorr() {
    if (!corr.value) return;
    const r = props.result;
    const rowH = 18, W = 320, L = 70;
    const H = props.columns.length * rowH + 24;
    const svg = d3.select(corr.value).attr('width', W).attr('height', H);
    svg.selectAll('*').remove();
    const i = ci.value;
    if (!r || i < 0) return;
    const xs = d3.scaleLinear().domain([-1, 1]).range([L, W - 20]);
    const color = d3.scaleDiverging(d3.interpolateRdBu).domain([1, 0, -1]);
    props.columns.forEach((col, k) => {
        const j = r.columns.indexOf(col);
        const v = col === props.column ? 1 : (r.correlation[i][j] ?? 0);
        const g = svg.append('g').attr('transform', `translate(0,${k * rowH + 4})`);
        g.append('text').attr('x', L - 6).attr('y', rowH / 2 + 4).attr('text-anchor', 'end').attr('font-size', 10)
            .attr('fill', props.output_cols.includes(col) ? OUTPUT_COLOR : INPUT_COLOR).text(col);
        g.append('rect').attr('x', Math.min(xs(0), xs(v))).attr('y', 3).attr('height', rowH - 6)
            .attr('width', Math.abs(xs(v) - xs(0))).attr('fill', color(v))
            .attr('opacity', col === props.column ? 0.25 : 0.9);
    });
    svg.append('line').attr('x1', xs(0)).attr('x2', xs(0)).attr('y1', 0).attr('y2', props.columns.length * rowH + 4).attr('stroke', '#888');
    svg.append('g').attr('transform', `translate(0,${props.columns.length * rowH + 4})`)
        .call(d3.axisBottom(xs).ticks(5)).call(g => g.selectAll('text').attr('font-size', 9));
}

function drawAll() {
    drawDensity();
    drawBars();
    drawCorr();
}
watch(() => [props.result, props.column, props.conditions, props.data_rows], drawAll, { deep: true });
onMounted(drawAll);
</script>

<style scoped>
.ud-container {
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    padding: 6px 20px;
    border-top: 1px solid #ddd;
}

.ud-panel h3 {
    font-size: 13px;
    margin: 6px 0 2px 0;
}

.ud-sub {
    font-size: 10px;
    color: #777;
    margin: 0 0 4px 0;
    font-weight: 400;
}

.ud-stats {
    font-size: 11px;
    margin: 2px 0 4px 0;
}

.ud-legend {
    font-size: 10px;
    color: #666;
}

.sw {
    display: inline-block;
    width: 10px;
    height: 10px;
    margin: 0 3px 0 10px;
    vertical-align: middle;
}
</style>
