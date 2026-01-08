<template>
    <div class="formulation_snippet">
        {{ part.inputName }}
    </div>
</template>
<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { ConstantPart, InputPart } from '../parts';
const part = defineModel<InputPart>({ required: true });
</script>
<style scoped>
.formulation_snippet {
    display: flex;
    flex-direction: row;
    padding: 10px;
    border: 1px solid #ccc;
}
</style>