// Fixtures for the GP-VAE Conditioner view (`/conditioner/:setname`): a small 5-column dataset
// (3 inputs a, b, c + 2 outputs y1, y2) and a deterministic, condition-aware fake of
// POST /datasets/{set}/conditioning/predict, so the tests can assert on how the view reacts.
//
// The fake posterior is built so per-column uncertainty is predictable:
//   - a conditioned column gets mean = condition value and std = width / sqrt(12) (0 for a point),
//   - every other column gets std = data_std * BASE_REL[col] * SHRINK ** (#conditions),
//     where c and y1 are "low uncertainty" (rel 0.05 / 0.08) and a, b, y2 "high" (~0.9),
//   so the PCP mean segment between c and y1 is always much more opaque than a-b.

export const CONDITIONER_SET = 'gt';
export const COLS = ['a', 'b', 'c', 'y1', 'y2'];
export const INPUT_COLS = ['a', 'b', 'c'];
export const OUTPUT_COLS = ['y1', 'y2'];

const DOMAINS = { a: [0, 10], b: [0, 100], c: [-1, 1], y1: [0, 50], y2: [100, 200] };
export const BASE_REL = { a: 0.9, b: 0.85, c: 0.05, y1: 0.08, y2: 0.95 };
export const SHRINK = 0.6;
export const BANK_SIZE = 512;

// deterministic pseudo-random numbers (LCG), so every run renders the same thing
function rng(seed) {
    let s = seed >>> 0;
    return () => {
        s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
        return s / 2 ** 32;
    };
}

// 60 rows: inputs uniform in their domain, outputs a noisy function of the inputs
const rand = rng(42);
const ROWS = Array.from({ length: 60 }, () => {
    const a = DOMAINS.a[0] + rand() * 10;
    const b = rand() * 100;
    const c = -1 + rand() * 2;
    const y1 = Math.min(50, Math.max(0, 2 * a + 0.2 * b + 5 * c + (rand() - 0.5) * 6));
    const y2 = Math.min(200, Math.max(100, 150 + 4 * a - 0.3 * b + 10 * c + (rand() - 0.5) * 10));
    return [a, b, c, y1, y2];
});

const colVals = (j) => ROWS.map((r) => r[j]);
const mean = (v) => v.reduce((s, x) => s + x, 0) / v.length;
const std = (v) => { const m = mean(v); return Math.sqrt(mean(v.map((x) => (x - m) ** 2))); };

export const DATA_MEAN = COLS.map((_, j) => mean(colVals(j)));
export const DATA_STD = COLS.map((_, j) => std(colVals(j)));

export const conditionerDataSample = {
    indices: ROWS.map((_, i) => i),
    inputs: ROWS.map((r) => r.slice(0, 3)),
    outputs: ROWS.map((r) => r.slice(3)),
};

function dataDescription() {
    const by = (f) => Object.fromEntries(COLS.map((c, j) => [c, f(c, j)]));
    return {
        input_cols: INPUT_COLS,
        output_cols: OUTPUT_COLS,
        all_columns: COLS,
        num_samples: ROWS.length,
        num_features: INPUT_COLS.length,
        num_outputs: OUTPUT_COLS.length,
        min_values: by((c) => DOMAINS[c][0]),
        max_values: by((c) => DOMAINS[c][1]),
        mean_values: by((_, j) => DATA_MEAN[j]),
        std_values: by((_, j) => DATA_STD[j]),
    };
}

export const conditionerSettings = {
    data_description: dataDescription(),
    data_name: 'Gas Turbine (mock)',
    short_data_name: 'gt',
    input_cols: 3,
    output_cols: 2,
    use_ucq: true,
    loaded: true,
};

export const plainSettings = {
    ...conditionerSettings,
    data_name: 'Plain (no UCQ)',
    short_data_name: 'plain',
    use_ucq: false,
};

export const statusAvailable = { available: true, reason: '', columns: COLS, bank_size: BANK_SIZE };
export const statusUnavailable = {
    available: false,
    reason: 'Conditioning needs a GP-VAE model (use_ucq with m_GPVAE) - mock reason.',
    columns: [],
    bank_size: 0,
};

// Builds a plausible ConditionResult for the POSTed `conditions` [{column, value, width}].
export function makeConditionResult(conditions = []) {
    const byCol = Object.fromEntries(conditions.map((c) => [c.column, c]));
    const n = conditions.length;
    const m = [];
    const s = [];
    COLS.forEach((col, j) => {
        const c = byCol[col];
        if (c) {
            m.push(c.value);
            s.push((c.width ?? 0) / Math.sqrt(12));
        } else {
            // shift the mean a little towards the conditioned columns' relative positions
            const shift = conditions.reduce((acc, cc) => {
                const k = COLS.indexOf(cc.column);
                return k < 0 ? acc : acc + (cc.value - DATA_MEAN[k]) / (DATA_STD[k] || 1);
            }, 0);
            m.push(DATA_MEAN[j] + 0.15 * DATA_STD[j] * Math.tanh(shift));
            s.push(DATA_STD[j] * BASE_REL[col] * SHRINK ** n);
        }
    });

    const corrRand = rng(7);
    const correlation = COLS.map((_, i) => COLS.map((_, j) => (i === j ? 1 : 0)));
    for (let i = 0; i < COLS.length; i++) {
        for (let j = i + 1; j < COLS.length; j++) {
            const v = byCol[COLS[i]] || byCol[COLS[j]] ? 0 : +(corrRand() * 1.6 - 0.8).toFixed(3);
            correlation[i][j] = v;
            correlation[j][i] = v;
        }
    }

    const sampleRand = rng(11 + n);
    const gauss = () => {
        const u = Math.max(1e-9, sampleRand());
        return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * sampleRand());
    };
    const samples = Array.from({ length: 24 }, () => COLS.map((_, j) => m[j] + s[j] * gauss()));

    const G = 120;
    const grid = [];
    const density = [];
    COLS.forEach((col, j) => {
        const [lo, hi] = DOMAINS[col];
        const pad = (hi - lo) * 0.05;
        const xs = Array.from({ length: G }, (_, k) => lo - pad + ((hi - lo + 2 * pad) * k) / (G - 1));
        // floor the std so point conditions still give a finite (spiky) density
        const sd = Math.max(s[j], (hi - lo) / 200);
        grid.push(xs);
        density.push(xs.map((x) => Math.exp(-0.5 * ((x - m[j]) / sd) ** 2) / (sd * Math.sqrt(2 * Math.PI))));
    });

    return {
        columns: COLS,
        input_cols: INPUT_COLS,
        output_cols: OUTPUT_COLS,
        conditioned: conditions.map((c) => c.column),
        mean: m,
        std: s,
        prior_std: COLS.map((col, j) => DATA_STD[j] * BASE_REL[col]),
        data_mean: DATA_MEAN,
        data_std: DATA_STD,
        correlation,
        samples,
        grid,
        density,
        ess: BANK_SIZE / (1 + 3 * n),
        temperature: 1,
    };
}

// Expected sigma(target) reduction (fraction of the current sigma) when pinning a free column next;
// b is the best "pin next" candidate for every target except b itself (then: y2).
export const PIN_GAIN = { a: 0.06, b: 0.3, c: 0.12, y1: 0.08, y2: 0.18 };

// Builds a plausible UncertaintyAttribution for the POSTed {conditions, target}, consistent with
// makeConditionResult: base sigma = the posterior std of the target there, dropping condition k
// gives the std with one condition fewer (so every condition reduces sigma by 1/SHRINK - 1 =
// 66.7 % of the current sigma), pin_gain = PIN_GAIN * base, explained_share = min(1, 2 * PIN_GAIN).
export function makeAttribution(conditions = [], target = 'y2') {
    const res = makeConditionResult(conditions);
    const j = COLS.indexOf(target);
    const base = res.std[j];
    const conditioned = conditions.map((c) => c.column);
    const n = conditions.length;
    const kind = COLS.map((col) => (col === target ? 'target' : conditioned.includes(col) ? 'conditioned' : 'free'));
    const targetCond = conditioned.includes(target);
    const removeStd = COLS.map((_, k) => (kind[k] === 'conditioned'
        ? (targetCond ? base * 1.05 : DATA_STD[j] * BASE_REL[target] * SHRINK ** (n - 1))
        : null));
    const pinGain = COLS.map((col, k) => (kind[k] === 'free' ? base * PIN_GAIN[col] : null));
    return {
        target,
        columns: COLS,
        conditioned,
        kind,
        base_std: base,
        remove_std: removeStd,
        condition_effect: removeStd.map((r) => (r == null ? null : r - base)),
        add_std: pinGain.map((g) => (g == null ? null : base - g)),
        pin_gain: pinGain,
        explained_share: COLS.map((col, k) => (k === j ? 1 : kind[k] === 'free' ? Math.min(1, 2 * PIN_GAIN[col]) : 0)),
    };
}

// Router for the conditioner endpoints. Returns `{ fixtureFor, predictBodies, attributionBodies }`;
// every POSTed /conditioning/predict (/attribution) body is parsed and pushed onto
// `predictBodies` (`attributionBodies`). `attributionDelay(body)` may return a delay in ms for an
// attribution response (to test that stale responses are dropped).
// `fixtureFor(url, method, req)` matches helpers.mjs's interception callback (the third
// argument is the puppeteer request, needed for the POST body).
export function makeConditionerRouter({ status = statusAvailable, datasets, attributionDelay } = {}) {
    const predictBodies = [];
    const attributionBodies = [];
    const base = `/datasets/${CONDITIONER_SET}`;
    const routes = {
        'GET /datasets/': datasets ?? { [CONDITIONER_SET]: conditionerSettings, plain: plainSettings },
        [`GET ${base}`]: conditionerSettings,
        [`GET ${base}/conditioning/status`]: status,
        [`GET ${base}/data/sample`]: conditionerDataSample,
    };
    const fixtureFor = (url, method, req) => {
        const path = new URL(url).pathname;
        const parse = () => {
            try {
                return JSON.parse(req?.postData() ?? '{}');
            } catch {
                return {};
            }
        };
        if (method === 'POST' && path === `${base}/conditioning/predict`) {
            const body = parse();
            predictBodies.push(body);
            return makeConditionResult(body.conditions ?? []);
        }
        if (method === 'POST' && path === `${base}/conditioning/attribution`) {
            const body = parse();
            attributionBodies.push(body);
            const result = makeAttribution(body.conditions ?? [], body.target);
            const delay = attributionDelay?.(body) ?? 0;
            return delay > 0 ? new Promise((r) => setTimeout(() => r(result), delay)) : result;
        }
        return routes[`${method} ${path}`];
    };
    return { fixtureFor, predictBodies, attributionBodies };
}
