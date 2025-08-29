import * as d3 from 'd3';
export const hashCode = s =>
    s.split("").reduce((a, b) => {
        a = (a << 5) - a + b.charCodeAt(0);
        return a & a;
    }, 0);

export const webglColor = (color: string) => {
    const { r, g, b, opacity } = (d3.color(color) as d3.RGBColor).rgb();
    return [r / 255, g / 255, b / 255, opacity];
};
export function reSpider(val){
    return Math.sqrt(val);
}
export function inverseSpider(val){
    return Math.pow(val, 2);
}