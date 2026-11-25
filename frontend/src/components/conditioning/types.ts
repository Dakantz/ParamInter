import type { ConditionResult } from '../../api/Api';

export interface CondValue {
    value: number;
    width: number; // 0 = point condition
}

export const PRED_COLOR = '#2f6db3';
export const INPUT_COLOR = '#333';
export const OUTPUT_COLOR = '#c76b00';
export const COND_COLOR = '#d1495b';

/** Relative posterior uncertainty of column i: posterior std / data std, clipped to [0, 1]. */
export function relUncertainty(res: ConditionResult, i: number): number {
    const ref = res.data_std[i] || res.prior_std[i] || 1;
    return Math.min(1, Math.max(0, res.std[i] / ref));
}

/** Confidence used for opacities: 1 - relative uncertainty. */
export function confidenceOf(res: ConditionResult, i: number): number {
    return 1 - relUncertainty(res, i);
}

/**
 * Upper end of the bar scale for attribution values (fractions of σ(target)). A strong condition
 * can be worth several 100 % of σ, which would squash every "pin next" bar to a few pixels, so the
 * scale is capped at 2.5x the largest pin gain (at least 25 %); longer bars are drawn clipped.
 */
export function attributionCap(rel: (number | null)[], kind: string[]): number {
    const all = rel.filter((v): v is number => v != null).map(Math.abs);
    const free = rel.filter((v, k): v is number => v != null && kind[k] === 'free');
    const vmax = Math.max(0.05, ...all);
    if (!free.length) return vmax;
    return Math.min(vmax, Math.max(0.25, 2.5 * Math.max(...free)));
}
