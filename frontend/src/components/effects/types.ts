// Which field of an InteractionBackgroundResult the Scatterplot Matrix popover's KNN-interpolated
// background is colored by.
export type BackgroundMode = 'output' | 'shap';

export interface BeeswarmRow {
    key: string;
    label: string;
    values: number[];
    color_values?: number[];
    indices?: number[];
    kind?: 'swarm' | 'path';
    // The input feature(s) this row represents, e.g. [f] for a first-order SHAP row or
    // [fi, fj, ...] for an order-n interaction combo. Lets consumers (e.g. the scatterplot
    // matrix) know exactly which dimension(s) to highlight on hover without parsing `label`.
    features?: string[];
    // Mean |SHAP (interaction) value| for this row, shown as a compact number next to the row
    // label when present.
    mean_abs?: number;
}
