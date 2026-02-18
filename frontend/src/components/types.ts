import { reactive } from "vue";
import { CostOverview, DataPoint, DataPointMinimzer, FilterCondition, InterpolationResult, LinearTarget } from "../api/Api";
export type DataPointMinimizerRecord = Record<string, {
    objective: LinearTarget,
    filter: FilterCondition
}>;
export function minimizerToRecord(minimizer: DataPointMinimzer | null): DataPointMinimizerRecord {
    let newTargets: Record<string, {
        objective: LinearTarget,
        filter: FilterCondition
    }> = {};
    minimizer?.targets?.forEach((t) => {
        newTargets[t.name] = {
            objective: t,
            filter: {
                name: t.name,
            }
        };

    });
    minimizer?.filters?.forEach((f) => {
        if (newTargets[f.name]) {
            newTargets[f.name].filter = f;
        }
    });
    return newTargets;
}
export function recordToMinimizer(record: DataPointMinimizerRecord): DataPointMinimzer {
    let minimizer: DataPointMinimzer = {
        targets: Object.values(record).map(t => t.objective),
        filters: Object.values(record).map(t => t.filter)
    };
    return minimizer;
}
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
    public fromQueryParams(params: URLSearchParams) {
        const selectionParam = params.get('selection');
        console.log("Parsing selection from query params:", selectionParam);
        if (selectionParam) {
            try {
                const decoded = atob(selectionParam);
                const parsed = JSON.parse(decoded);
                this.selected_indices = reactive(parsed.selected_indices || []);
                this.hovered_int = parsed.hovered_int || null;
                this.previewed_index = parsed.previewed_index || null;
                this.target = reactive(parsed.target || null);
                console.log("Parsed selection from query params:", parsed, "new selection object:", this);
            } catch (error) {
                console.error("Failed to parse selection from query params:", error);
            }
        }
    }
    public setTarget(target: DataPointMinimizerRecord | null) {
        let new_target = target ? recordToMinimizer(target) : null;
        if (JSON.stringify(this.target) !== JSON.stringify(new_target)) {
            this.target = new_target;
        }
    }
    public targetToRecord(): DataPointMinimizerRecord {
        return this.target ? minimizerToRecord(this.target) : {};
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
export class CostOverviewData implements CostOverview {
    constructor(
        public costs: number[] = [],
        public within_filter: boolean[] = [],
    ) { }
}