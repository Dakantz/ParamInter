import type { ConditionResult } from '../../api/Api';

export interface CondValue {
    value: number;
    width: number; // 0 = point condition
}

export const PRED_COLOR = '#2f6db3';
export const INPUT_COLOR = '#333';
export const OUTPUT_COLOR = '#c76b00';

/** Relative posterior uncertainty of column i: posterior std / data std, clipped to [0, 1]. */
export function relUncertainty(res: ConditionResult, i: number): number {
    const ref = res.data_std[i] || res.prior_std[i] || 1;
    return Math.min(1, Math.max(0, res.std[i] / ref));
}

/** Confidence used for opacities: 1 - relative uncertainty. */
export function confidenceOf(res: ConditionResult, i: number): number {
    return 1 - relUncertainty(res, i);
}
