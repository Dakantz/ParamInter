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
    val = Math.min(max, Math.max(min, val))
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
    // console.log("Considered map:", considered_map, "offset idx:", offset_idx, "idx:", idx);
    if (considered_map) {
        if (offset_idx >= 0 && offset_idx < considered_map[0].length) {
            return considered_map.map(row => row[offset_idx]);
        }
    }
    return [];
}

export const randomNormal = d3.randomNormal()


export function setupMarkers(svg: d3.Selection<SVGSVGElement | null, unknown, null, undefined>, markerSize = 5) {

    const markerBoxWidth = markerSize;
    const markerBoxHeight = markerSize;
    const refX = markerBoxWidth / 2;
    const refY = markerBoxHeight / 2;
    const arrowPoints = [
        [0, 0],
        [markerBoxWidth, markerBoxHeight / 2],
        [0, markerBoxHeight],
        [markerBoxWidth / 2, markerBoxHeight / 2]
    ];
    svg
        .append('defs')
        .append('marker')
        .attr('id', 'arrow-pos')
        .attr('viewBox', [0, 0, markerBoxWidth, markerBoxHeight])
        .attr('refX', refX)
        .attr('refY', refY)
        .attr('markerWidth', markerBoxWidth)
        .attr('markerHeight', markerBoxHeight)
        .attr('orient', 'auto-start-reverse')
        .append('path')
        .attr('d', d3.line()(arrowPoints as [number, number][]))
        .attr('class', 'sensitivity_pos');
    svg
        .append('defs')
        .append('marker')
        .attr('id', 'arrow-neg')
        .attr('viewBox', [0, 0, markerBoxWidth, markerBoxHeight])
        .attr('refX', refX)
        .attr('refY', refY)
        .attr('markerWidth', markerBoxWidth)
        .attr('markerHeight', markerBoxHeight)
        .attr('orient', 'auto-start-reverse')
        .append('path')
        .attr('d', d3.line()(arrowPoints as [number, number][]))
        .attr('class', 'sensitivity_neg');
}

// generated using Qwen 2.5 7B, for chat contact benedikt
export function gaussianPdf(x: number, mean: number = 0, stdDev: number = 1): number {
    const pi = Math.PI;
    const exponent = -Math.pow((x - mean) / stdDev, 2) / 2;

    return (1 / (stdDev * Math.sqrt(2 * pi))) * Math.exp(exponent);
}
function erfinv(y: number, tolerance = 1e-6, maxIterations = 50) {
    // Initial guess based on Taylor series expansion near zero for erf^-1(y)
    let x0 = Math.sqrt(2 / Math.PI) * y + (Math.log(1 - y * y) / 4);

    function f(x: number) {
        return Math.exp(-x * x) - ((y + 1) / (y - 1)) * ((y + 1) / (y - 1)) ** (1 / 2) * ((Math.E ** ((-x * x) + 2)) - 1) ** 0.5;
    }

    for (let i = 0; i < maxIterations && Math.abs(f(x0)) > tolerance; ++i) {
        x0 -= f(x0) / (-2 * x0 * Math.exp(-x0 * x0));
    }

    return x0;
}
export function inverseNormalCdf(probability: number, mu: number, std: number) {
    const z = erfinv((probability - 0.5) * 2) * std + mu;
    return z;
}