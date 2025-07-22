import { Api, DataPoints } from "../api/Api";
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
export class DataRepository {
    data_points: LoadedDataPoints;
    all_embeddings: AllEmbeddings;
    client: Api<unknown>;

    constructor() {
        this.data_points = new LoadedDataPoints();
        this.all_embeddings = new AllEmbeddings();
        this.client = new Api(
            { baseURL: API_BASE_URL }
        );
    }

    async loadAll(load_cb: (progress: number) => void = () => { }) {
        const all_types = (await this.client.columnTypes.getColumnTypesColumnTypesGet()).data;
        for (const type in all_types) {
            const embeddings = (await this.client.embedding.getEmbeddingEmbeddingColTypeGet(type)).data;
            this.all_embeddings.all_embeddings[type] = new Embeddings(embeddings);
            load_cb((Object.keys(this.all_embeddings.all_embeddings).length / Object.keys(all_types).length));
        }
        this.data_points = (await this.client.data.getDataDataGet()).data;

    }
}