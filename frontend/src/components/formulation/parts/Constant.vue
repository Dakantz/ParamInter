<template>
    <div class="formulation_snippet">
        {{ part.value }}
    </div>
</template>
<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { ConstantPart } from '../parts';
const part = defineModel<ConstantPart>({ required: true });
</script>
<style scoped>
.formulation_snippet {
    display: flex;
    flex-direction: row;
    padding: 10px;
    border: 1px solid #ccc;
}
</style>