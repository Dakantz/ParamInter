import { ThresholdNumberArrayGenerator } from "d3";
import { Api, DataDescription, DataPoint, DataPoints } from "../api/Api";
import { API_BASE_URL } from "../config";

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

}
export class DPCache {
    data_points: Record<number, DataPoint>;
    constructor(private rep: DataRepository) {

        this.data_points = {};
    }
    getDP(idx: number): Promise<DataPoint> {
        if (this.data_points[idx]) {
            return Promise.resolve(this.data_points[idx]);
        }
        return this.rep.client.dataPoint.getDataPointDataPointIdxIndexGet(idx).then((response) => {
            this.data_points[idx] = response.data;
            return response.data;
        });
    }
}
export class DataRepository {
    data_points: LoadedDataPoints;
    all_embeddings: AllEmbeddings;
    client: Api<unknown>;
    dps: DPCache;
    all_types: Record<string, string[]> = {};
    description: DataDescription | null = null;
    constructor() {
        this.data_points = new LoadedDataPoints();
        this.all_embeddings = new AllEmbeddings();
        this.client = new Api(
            { baseURL: API_BASE_URL }
        );
        this.dps = new DPCache(this);
    }

    async loadAll(load_cb: (progress: number, loaded_keys: string[]) => void = () => { }) {
        this.all_types = (await this.client.columnTypes.getColumnTypesColumnTypesGet()).data;
        for (const type in this.all_types) {
            const embeddings = (await this.client.embedding.getEmbeddingEmbeddingColTypeGet(type)).data;
            this.all_embeddings.all_embeddings[type] = new Embeddings(embeddings);
            load_cb((Object.keys(this.all_embeddings.all_embeddings).length / Object.keys(this.all_types).length), Object.keys(this.all_embeddings.all_embeddings));
        }
        this.description = (await this.client.dataDescription.getDataDescriptionDataDescriptionGet()).data;
        // this.data_points = (await this.client.data.getDataDataGet()).data;

    }
    getTypeIndex(type: string): number {
        return this.all_types["full"].indexOf(type);
    }

}