import * as d3 from 'd3';
import { InterpolationResult } from '../../api/Api';
export const hashCode = (s: string) =>
    s.split("").reduce((a, b) => {
        a = (a << 5) - a + b.charCodeAt(0);
        return a & a;
    }, 0);

export const webglColor = (color: string) => {
    const { r, g, b, opacity } = (d3.color(color) as d3.RGBColor).rgb();
    return [r / 255, g / 255, b / 255, opacity];
};
export function reSpider(val: number, min = 0, max = 1) {
    return Math.sqrt((val - min) / (max - min));
}
export function inverseSpider(val: number, min = 0, max = 1) {
    return Math.pow(val, 2) * (max - min) + min;
}
export function outValues(int_results: InterpolationResult, idx: number) {
    let considered_map: Array<Array<number>> | null = null;
    let offset_idx = -1;
    if (idx < int_results.knn_inputs[0].length) {
        considered_map = int_results.knn_inputs;
        offset_idx = idx;
    } else if ((idx - int_results.knn_inputs[0].length) < int_results.knn_outputs[0].length) {
        considered_map = int_results.knn_outputs;
        offset_idx = idx - int_results.knn_inputs[0].length;
    } else {
        console.warn("Index out of range for inputs and outputs:", idx);
        return [];
    }
    console.log("Considered map:", considered_map, "offset idx:", offset_idx, "idx:", idx);
    if (considered_map) {
        if (offset_idx >= 0 && offset_idx < considered_map[0].length) {
            return considered_map.map(row => row[offset_idx]);
        }
    }
    return [];
}