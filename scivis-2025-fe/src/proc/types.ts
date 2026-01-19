import * as d3 from "d3";
import { Api, DataDescription, DataPoint, DataPoints } from "../api/Api";
import { API_BASE_URL } from "../config";
import { toRaw } from "vue";
import { colormaps_d3 } from "../components/helpers/colormaps";

export class Embeddings {
    constructor(
        public embeddings: number[][],
        public for_cols: string[] = [],
        public col_type: string = ""
    ) {
    }
}

export class AllEmbeddings {
    all_embeddings: Record<string, Embeddings>;

    constructor() {
        this.all_embeddings = {};
    }
}
export class LoadedDataPoints implements DataPoints {
    inputs: number[][];
    outputs: number[][];
    projected_outputs?: number[][] | undefined;
    public constructor() {
        this.inputs = [];
        this.outputs = [];
    }

}
export class DPCache {
    data_points: Record<number, DataPoint>;
    in_flight_requests: Record<number, Promise<DataPoint>>;
    constructor(private rep: DataRepository) {

        this.data_points = {};
        this.in_flight_requests = {};
    }
    getDP(idx: number): Promise<DataPoint> {
        if (this.data_points[idx]) {
            return Promise.resolve(this.data_points[idx]);
        }
        if (idx in this.in_flight_requests) {
            return this.in_flight_requests[idx];
        }
        this.in_flight_requests[idx] = this.rep.client.dataPoint.getDataPointDataPointIdxIndexGet(idx).then((res) => {
            this.data_points[idx] = res.data;
            delete this.in_flight_requests[idx];
            return res.data;
        });
        return this.in_flight_requests[idx];
    }
}
export class DataRepository {
    data_points: LoadedDataPoints;
    client: Api<unknown>;
    dps: DPCache;
    all_types: Record<string, string[]> = {};
    description: DataDescription | null = null;

    constructor() {
        this.data_points = new LoadedDataPoints();
        this.client = new Api(
            { baseURL: API_BASE_URL }
        );
        this.dps = new DPCache(this);
    }
    async loadEmbeddingType(type: string, all_embeddings: AllEmbeddings, load_cb: (progress: number, loaded_keys: string[]) => void = () => { }) {
        const embeddings = (await this.client.data.getEmbeddingDataEmbeddingColTypeGet(type)).data;
        all_embeddings.all_embeddings[type] = toRaw(new Embeddings(embeddings));
        load_cb(1, Object.keys(all_embeddings.all_embeddings));
    }
    async loadAll(load_cb: (progress: number, loaded_keys: string[]) => void = () => { }, all_embeddings: AllEmbeddings) {
        this.all_types = (await this.client.data.getColumnTypesDataColumnTypesGet()).data;
        this.description = (await this.client.data.getDataDescriptionDataDescriptionGet()).data;
        let promises: Promise<void>[] = [];
        for (const type in this.all_types) {
            promises.push(this.loadEmbeddingType(type, all_embeddings, load_cb));
        }
        await Promise.all(promises);
        // this.data_points = (await this.client.data.getDataDataGet()).data;

    }
    getTypeIndex(type: string): number {
        return this.description?.all_columns.indexOf(type) ?? -1;
    }
    getVisisbleTypes(): Record<string, string[]> {
        // console.log("New types:", this.all_types);
        if (Object.keys(this.all_types).length === 0) {
            console.warn("No types available in data repository.");
            return {}
        }
        if (Object.entries(this.all_types).length <= 3) {
            console.log("Showing only Outputs category.");
            return {
                "Input": this.all_types["Input"],
                "Output": this.all_types["Output"]
            };
        } else {
            return Object.fromEntries(
                Object.entries(this.all_types)
                    .filter((kv, i) => i < Object.entries(this.all_types).length - 1)
                    .map(([key, value]) => [key, value])
            );
        }
    }

}
export function colorForIndex(idx: number, lightness: number = 0): string {
    let offset = idx/4
    let col = d3.color(colormaps_d3['Lapaz'](offset));
    return col?.brighter(lightness).toString() || d3.schemeObservable10[idx % 10];

}