import { InterpolationResult } from "../api/Api";

export class PlotSelection {
    constructor(
        public selected_indices: number[] = [],
        public hovered_index: number | null = null
    ) { }
    public addIndex(index: number) {
        if (!this.selected_indices.includes(index)) {
            this.selected_indices.push(index);
        }
    }
    public removeIndex(index: number) {
        const idx = this.selected_indices.indexOf(index);
        if (idx !== -1) {
            this.selected_indices.splice(idx, 1);
        }
    }
}
export class PlotSelectionResults {
    constructor(
        public similarities: number[] = [],
        public interpolation: InterpolationResult | null = null,
    ) { }
}

export interface MappedData {
    x: number;
    y: number;
    data: any;
    index: number;
}