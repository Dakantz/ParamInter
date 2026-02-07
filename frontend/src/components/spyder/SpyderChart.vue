<template>
    <div ref="spider-div-container" class="spider-container">
        <svg ref="plot" width="10px" height="10px" class="plot-svg">
            <SpyderChart_Base :rep="rep" v-model="dim_data" :editable="editable" :height="spyder_size.height"
                :width="spyder_size.width" :color="color" :show_labels="show_labels" :sensitivities="sensitivities"
                :uncertainties="uncertainties" />
        </svg>
    </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, useTemplateRef, computed } from 'vue';
import * as d3 from 'd3';
import { inverseSpider, reSpider, setupMarkers } from '../helpers/utils';
import { DataDescription } from '../../api/Api';
import { DataRepository } from '../../proc/data-store';
import SpyderChart_Base from './SpyderChart_Base.vue';
const dim_data = defineModel<Array<number>>({
    default: () => []
});
const { editable, factor, sensitivities, rep, height, color, show_labels } = defineProps({
    rep: {
        type: Object as () => DataRepository,
        default: () => (null)
    },
    editable: {
        type: Boolean,
        default: false
    },
    factor: {
        type: Number,
        default: 1
    },
    sensitivities: {
        type: Array as () => Array<number>,
        default: () => []
    },
    uncertainties: {
        type: Array as () => Array<number>,
        default: () => []
    },
    height: {
        type: String,
        default: '20vh'
    },
    color: {
        type: String,
        default: 'rgba(58, 128, 0, 0.72)'
    },
    show_labels: {
        type: Boolean,
        default: true
    }
});
const plot = useTemplateRef('plot');
const spiderDivContainer = useTemplateRef('spider-div-container');

const dimensions = ref<string[]>([]);
watch(() => rep, (newRep) => {
    if (newRep && newRep.description) {
        if (dimensions.value.length === 0) {
            // initialize dim_data
            dimensions.value = [...newRep.description.input_cols];
        }

    }
}, { immediate: true, deep: true });

const state = reactive({
    dim_data: dim_data,
    editing_spider: false,
    edit_start_mouse: { x: 0, y: 0 },
});
const spyder_size = computed(() => {
    if (!spiderDivContainer.value) return { width: 100, height: 100 };
    return {
        width: spiderDivContainer.value.clientWidth,
        height: spiderDivContainer.value.clientHeight
    };
});
onMounted(() => {
    const svg = d3.select(plot.value);
    let bbox = spiderDivContainer.value?.getBoundingClientRect();
    if (!svg.empty() && bbox) {
        svg.attr('width', bbox.width);
        svg.attr('height', bbox.height);
    }

    setupMarkers(d3.select(plot.value));
});
watch(() => dimensions, () => {
}, { immediate: true });
watch(() => dim_data, () => {
    // console.log("Dimension data changed:", dim_data.value);
}, { deep: true, immediate: true });
const cursor_style = ref('default');
watch(() => editable, (editing) => {
    if (editing) {
        cursor_style.value = 'move';
    } else {
        cursor_style.value = 'default';
    }
}, { immediate: true });


watch(() => sensitivities, (sense) => {
    if (sense.length > 0) {
        // console.log("Updating sensitivities:", sense);
    }
}, { immediate: true });


</script>

<style>
.spider-container {
    width: 90%;
    min-width: 100px;
    min-height: v-bind(height);
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: v-bind(cursor_style);
    user-select: none;
}


.plot-svg {
    width: 100%;
    /* height: 100%; */
}
</style>