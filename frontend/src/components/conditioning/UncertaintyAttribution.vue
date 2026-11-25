<template>
    <div class="ua-panel">
        <h3>Why is σ({{ column ?? '-' }}) {{ attr ? '= ' + fmt(attr.base_std) : '' }}?
            <span v-if="loading" class="ua-loading">updating...</span>
        </h3>
        <p class="ud-sub">change of σ({{ column ?? '-' }}) per parameter, in % of its current σ
            (hover a row)</p>
        <div class="ua-summary" v-if="attr && column">
            <p v-if="target_conditioned" class="ua-line">
                <b>{{ column }}</b> is itself conditioned - its σ comes mostly from its own condition range.
            </p>
            <p v-if="best_cond" class="ua-line ua-cond">
                Most of the certainty comes from <b>{{ best_cond.col }}</b>
                (dropping it raises σ by {{ pct(best_cond.v) }}).
            </p>
            <p v-else-if="!attr.conditioned.length" class="ua-line">
                No conditions - σ({{ column }}) is the unconditioned model uncertainty.
            </p>
            <p v-if="best_pin" class="ua-line ua-pin">
                Fixing <b>{{ best_pin.col }}</b> would reduce σ({{ column }}) most (−{{ pct(best_pin.v) }}).
            </p>
            <p v-else class="ua-line">No free parameter would reduce σ({{ column }}) noticeably if fixed.</p>
        </div>
        <svg ref="chart" :class="{ stale: loading }"></svg>
        <p class="ua-legend">
            <span class="sw" :style="{ background: COND_COLOR }"></span> condition reduces σ
            <span class="sw" :style="{ background: PRED_COLOR }"></span> expected gain if pinned next
            <span class="sw" style="background: #999"></span> r² (share of variance)
        </p>
    </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, useTemplateRef, watch } from 'vue';
import * as d3 from 'd3';
import type { UncertaintyAttribution } from '../../api/Api';
import { PRED_COLOR, INPUT_COLOR, OUTPUT_COLOR, COND_COLOR, attributionCap } from './types';

/**
 * Explains the GP-VAE posterior σ of the detail column (the attribution target):
 *  - conditioned rows: how much σ(target) would grow if that condition were dropped
 *    (`condition_effect`), i.e. how much certainty that condition provides,
 *  - free rows: the expected σ(target) reduction if that column were pinned next (`pin_gain`),
 *  - a small grey bar on the right: posterior r² between the column and the target.
 * Bars are in % of the current σ(target) (`base_std`); negative values point left.
 */
const props = defineProps<{
    attribution: UncertaintyAttribution | null;
    column: string | null;
    columns: string[];
    output_cols: string[];
    loading: boolean;
    highlight: string | null;
}>();
const emit = defineEmits<{ (e: 'hover', column: string | null): void }>();

const chart = useTemplateRef('chart');
const fmt = d3.format('.3~g');
const pctFmt = d3.format('.1~%');
const pct = (v: number) => pctFmt(v);

// only show an attribution that belongs to the current detail column
const attr = computed(() => (props.attribution && props.attribution.target === props.column) ? props.attribution : null);
const target_conditioned = computed(() => !!attr.value && attr.value.conditioned.includes(attr.value.target));

/** Relative values (fraction of base σ) per column: condition effect or pin gain. */
function relValue(a: UncertaintyAttribution, k: number): number | null {
    const base = a.base_std || 1e-12;
    if (a.kind[k] === 'conditioned') return a.condition_effect[k] == null ? null : a.condition_effect[k]! / base;
    if (a.kind[k] === 'free') return a.pin_gain[k] == null ? null : a.pin_gain[k]! / base;
    return null;
}
function argmaxOf(kind: string) {
    const a = attr.value;
    if (!a) return null;
    let best: { col: string; v: number } | null = null;
    a.columns.forEach((col, k) => {
        if (a.kind[k] !== kind) return;
        const v = relValue(a, k);
        // ignore negligible effects (< 0.5 % of σ)
        if (v != null && v > 0.005 && (!best || v > best.v)) best = { col, v };
    });
    return best as { col: string; v: number } | null;
}
const best_pin = computed(() => argmaxOf('free'));
const best_cond = computed(() => argmaxOf('conditioned'));

function draw() {
    if (!chart.value) return;
    // label | diverging bar | text label (monospace, ~5.5 px per char at 9 px) | r² mini bar
    const rowH = 18, W = 400, L = 50;
    const BAR0 = L + 4, BAR1 = BAR0 + 116, TXT = BAR1 + 6, SH0 = W - 36, SH1 = W - 4;
    const H = props.columns.length * rowH + 24;
    const svg = d3.select(chart.value).attr('width', W).attr('height', H);
    svg.selectAll('*').remove();
    const a = attr.value;
    if (!a) return;
    const rel = props.columns.map(col => {
        const k = a.columns.indexOf(col);
        return k < 0 ? null : relValue(a, k);
    });
    const cap = attributionCap(rel, props.columns.map(col => a.kind[a.columns.indexOf(col)] ?? ''));
    const vals = rel.filter((v): v is number => v != null).map(v => Math.max(-cap, Math.min(cap, v)));
    const lo = Math.min(0, d3.min(vals) ?? 0);
    const hi = Math.max(0.05, d3.max(vals) ?? 0);
    const xs = d3.scaleLinear().domain([lo, hi]).range([BAR0, BAR1]).nice();
    const [dlo, dhi] = xs.domain();
    const shs = d3.scaleLinear().domain([0, 1]).range([SH0, SH1]);

    props.columns.forEach((col, row) => {
        const k = a.columns.indexOf(col);
        if (k < 0) return;
        const kind = a.kind[k];
        const v = rel[row];
        const is_best = (kind === 'free' && best_pin.value?.col === col) || (kind === 'conditioned' && best_cond.value?.col === col);
        const hl = col === props.highlight;
        const g = svg.append('g')
            .attr('class', `ua-row ua-row-${kind}`)
            .attr('data-col', col)
            .attr('transform', `translate(0,${row * rowH + 4})`)
            .style('cursor', 'pointer')
            .on('mouseenter', () => emit('hover', col))
            .on('mouseleave', () => emit('hover', null));
        g.append('rect').attr('class', 'ua-bg').attr('x', 0).attr('width', W).attr('height', rowH)
            .attr('fill', hl ? '#eef3fa' : kind === 'target' ? '#f4f4f4' : 'transparent');
        g.append('text').attr('class', 'ua-label').attr('x', L - 6).attr('y', rowH / 2 + 4).attr('text-anchor', 'end')
            .attr('font-size', 10).attr('font-weight', kind === 'target' || hl ? 700 : 400)
            .attr('fill', props.output_cols.includes(col) ? OUTPUT_COLOR : INPUT_COLOR).text(col);

        let label = '';
        const title: string[] = [];
        if (kind === 'target') {
            label = `target · σ = ${fmt(a.base_std)}`;
            title.push(`${col}: attribution target, posterior σ = ${fmt(a.base_std)}`);
        } else if (v != null) {
            const color = kind === 'conditioned' ? COND_COLOR : PRED_COLOR;
            const vc = Math.max(dlo, Math.min(dhi, v));
            g.append('rect').attr('class', 'ua-bar')
                .attr('x', Math.min(xs(0), xs(vc))).attr('y', 3).attr('height', rowH - 6)
                .attr('width', Math.max(1, Math.abs(xs(vc) - xs(0))))
                .attr('fill', color)
                .attr('opacity', v < 0 ? 0.35 : is_best ? 0.95 : 0.65)
                .attr('stroke', is_best ? '#111' : 'none').attr('stroke-width', 1);
            if (vc !== v) {
                // clipped bar: white break mark near its end
                const xe = xs(vc) + (v > 0 ? -7 : 7);
                g.append('path').attr('class', 'ua-clip')
                    .attr('d', `M${xe - 2},${rowH - 2} L${xe + 2},2 M${xe + 2},${rowH - 2} L${xe + 6},2`)
                    .attr('stroke', '#fff').attr('stroke-width', 1.5);
            }
            if (kind === 'conditioned') {
                label = v >= 0 ? `condition reduces σ by ${pct(v)}` : `condition raises σ by ${pct(-v)}`;
                title.push(`${col} is conditioned: without it σ(${a.target}) = ${fmt(a.remove_std[k] ?? NaN)} instead of ${fmt(a.base_std)}`);
            } else {
                label = v >= 0 ? `pin next: −${pct(v)}` : `pin next: +${pct(-v)}`;
                title.push(`fixing ${col} would change σ(${a.target}) from ${fmt(a.base_std)} to ≈ ${fmt(a.add_std[k] ?? NaN)} (expected)`);
            }
        }
        g.append('text').attr('class', 'ua-text').attr('x', TXT).attr('y', rowH / 2 + 4).attr('font-size', 9)
            .attr('font-weight', is_best ? 700 : 400)
            .attr('fill', kind === 'conditioned' ? COND_COLOR : kind === 'free' ? '#335' : '#555')
            .text(label);
        // explained share (r²) mini bar
        const s = a.explained_share[k] ?? 0;
        if (kind !== 'target') {
            g.append('rect').attr('x', SH0).attr('width', SH1 - SH0).attr('y', rowH / 2 - 2).attr('height', 4).attr('fill', '#eee');
            g.append('rect').attr('class', 'ua-share').attr('x', SH0).attr('width', Math.max(0.5, shs(s) - SH0))
                .attr('y', rowH / 2 - 2).attr('height', 4).attr('fill', '#999');
            title.push(`posterior r² with ${a.target}: ${pct(s)}`);
        }
        g.append('title').text(title.join('\n'));
    });
    const bottom = props.columns.length * rowH + 4;
    svg.append('line').attr('x1', xs(0)).attr('x2', xs(0)).attr('y1', 4).attr('y2', bottom).attr('stroke', '#888');
    svg.append('g').attr('transform', `translate(0,${bottom})`)
        .call(d3.axisBottom(xs).ticks(3).tickFormat(d3.format('.0%')))
        .call(g => g.selectAll('text').attr('font-size', 9));
    svg.append('text').attr('x', (SH0 + SH1) / 2).attr('y', bottom + 14).attr('text-anchor', 'middle')
        .attr('font-size', 9).attr('fill', '#777').text('r²');
}

watch(() => [attr.value, props.columns, props.output_cols, props.highlight], draw, { flush: 'post' });
onMounted(draw);
</script>

<style scoped>
.ua-panel {
    width: 400px;
}

.ua-panel h3 {
    font-size: 13px;
    margin: 6px 0 2px 0;
}

.ud-sub {
    font-size: 10px;
    color: #777;
    margin: 0 0 4px 0;
}

.ua-loading {
    font-size: 10px;
    font-weight: 400;
    color: #999;
}

.ua-summary {
    min-height: 30px;
}

.ua-line {
    font-size: 11px;
    margin: 0 0 2px 0;
}

.ua-cond b {
    color: #d1495b;
}

.ua-pin b {
    color: #2f6db3;
}

svg.stale {
    opacity: 0.5;
    transition: opacity 0.2s;
}

.ua-legend {
    font-size: 10px;
    color: #666;
}

.sw {
    display: inline-block;
    width: 10px;
    height: 10px;
    margin: 0 3px 0 8px;
    vertical-align: middle;
}
</style>
