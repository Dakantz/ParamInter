import { DataPoint, DataPointMinimzer, FilterCondition, InterpolationResult, LinearTarget } from "../api/Api";

export class PlotSelection {
    constructor(
        public selected_indices: number[] = [],
        public hovered_int: HoveredInterpolation | null = null,
        public previewed_index: number | null = null,
        public target: DataPointMinimzer | null = null,
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
    public clearSelection() {
        this.selected_indices = [];
    }
    public setTarget(target: DataPointMinimzer | null) {
        this.target = target;
    }
}
export class PlotSelectionResults {
    constructor(
        public similarities: number[] = [],
    ) { }
}

export interface MappedData {
    x: number;
    y: number;
    data: any;
    index: number;
}
export interface HoveredInterpolation {
    interpolation_idx: number;
    index_in_interpolation: number;
}
export class ColumnObjective {
    constructor(
        public objective: LinearTarget,
        public filter: FilterCondition,
    ) {

    }
}