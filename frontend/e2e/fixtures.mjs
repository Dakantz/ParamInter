// Fixture data shared across e2e test files, plus a small router to turn a subset of it into a
// `fixtureFor(url, method)` function for `page.setRequestInterception` (see helpers.mjs).

export const dataDescription = {
    input_cols: ['temp', 'pressure'],
    output_cols: ['strength'],
    all_columns: ['temp', 'pressure', 'strength'],
    num_samples: 10,
    num_features: 2,
    num_outputs: 1,
    min_values: { temp: 0, pressure: 0, strength: 0 },
    max_values: { temp: 100, pressure: 100, strength: 100 },
    mean_values: { temp: 50, pressure: 50, strength: 50 },
    std_values: { temp: 10, pressure: 10, strength: 10 },
};

export const managerSettings = {
    data_description: dataDescription,
    data_name: 'Hilti',
    short_data_name: 'hilti',
    loaded: true,
};

export const beeswarmResult = {
    output_col: 'strength',
    features: ['temp', 'pressure'],
    indices: [0, 1],
    shap_values: { temp: [0.1, -0.2], pressure: [0.3, 0.05] },
    feature_values: { temp: [10, 20], pressure: [30, 40] },
    base_value: 5,
};

export const columnTypesHilti = { temp: ['input'], pressure: ['input'], strength: ['output'] };

// A random sample of raw input rows, as served by GET /datasets/{set}/data/sample - used by both
// the parallel-coordinates selector (Interpolator) and the scatterplot matrix (Effects).
export const dataSampleHilti = {
    indices: [0, 1, 2, 3],
    inputs: [[10, 30], [20, 40], [80, 60], [90, 70]],
};

// order-2 interaction result for the one pair hilti has (temp & pressure), as served by
// POST /datasets/hilti/effects/interaction.
export const interactionResultHilti = {
    output_col: 'strength',
    order: 2,
    indices: [0, 1],
    combinations: [
        { features: ['temp', 'pressure'], mean_abs: 0.2, values: [0.1, -0.1] },
    ],
    feature_values: { temp: [10, 20], pressure: [30, 40] },
};

// A second dataset with 7 input dimensions (> the 6-dimension cutoff), used to exercise the
// parallel-coordinates selector branch of the Interpolator (the old spider-chart + similar-points
// selector is used at <= 6 dimensions - see `hilti`, which has 2, above).
export const wideInputCols = ['a', 'b', 'c', 'd', 'e', 'f', 'g'];
export const wideDataDescription = {
    input_cols: wideInputCols,
    output_cols: ['y'],
    all_columns: [...wideInputCols, 'y'],
    num_samples: 10,
    num_features: wideInputCols.length,
    num_outputs: 1,
    min_values: Object.fromEntries([...wideInputCols, 'y'].map((c) => [c, 0])),
    max_values: Object.fromEntries([...wideInputCols, 'y'].map((c) => [c, 100])),
    mean_values: Object.fromEntries([...wideInputCols, 'y'].map((c) => [c, 50])),
    std_values: Object.fromEntries([...wideInputCols, 'y'].map((c) => [c, 20])),
};
export const wideManagerSettings = {
    data_description: wideDataDescription,
    data_name: 'Wide7',
    short_data_name: 'wide7',
    loaded: true,
};
export const columnTypesWide7 = Object.fromEntries([
    ...wideInputCols.map((c) => [c, ['input']]),
    ['y', ['output']],
]);
// 10 rows, ascending on dimension 'a' (0, 10, 20, ..., 90) so a brush test has a predictable
// range to narrow against.
export const dataSampleWide7 = {
    indices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    inputs: Array.from({ length: 10 }, (_, i) => wideInputCols.map((_, j) => (i * 10 + j * 3) % 100)),
};

// A dataset with 16 input dimensions, used to verify the scatterplot matrix shrinks its cell
// size to fit the panel's actual width instead of overflowing (a fixed cell size used to make
// the matrix render far wider than its container for datasets with many input columns).
export const manyDimsCols = Array.from({ length: 16 }, (_, i) => `d${i}`);
export const manyDimsDataDescription = {
    input_cols: manyDimsCols,
    output_cols: ['y'],
    all_columns: [...manyDimsCols, 'y'],
    num_samples: 5,
    num_features: manyDimsCols.length,
    num_outputs: 1,
    min_values: Object.fromEntries([...manyDimsCols, 'y'].map((c) => [c, 0])),
    max_values: Object.fromEntries([...manyDimsCols, 'y'].map((c) => [c, 100])),
    mean_values: Object.fromEntries([...manyDimsCols, 'y'].map((c) => [c, 50])),
    std_values: Object.fromEntries([...manyDimsCols, 'y'].map((c) => [c, 20])),
};
export const manyDimsManagerSettings = {
    data_description: manyDimsDataDescription,
    data_name: 'ManyDims',
    short_data_name: 'manydims',
    loaded: true,
};
export const columnTypesManyDims = Object.fromEntries([
    ...manyDimsCols.map((c) => [c, ['input']]),
    ['y', ['output']],
]);
export const dataSampleManyDims = {
    indices: [0, 1, 2, 3, 4],
    inputs: Array.from({ length: 5 }, (_, i) => manyDimsCols.map((_, j) => (i * 17 + j * 5) % 100)),
};

// Builds a `fixtureFor(url, method)` function from a `{'METHOD /path': value}` map, so each test
// file only wires up the endpoints it actually exercises instead of importing one giant router.
export function makeFixtureRouter(routes) {
    return (url, method) => {
        const key = `${method} ${new URL(url).pathname}`;
        return routes[key];
    };
}
