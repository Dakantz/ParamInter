<template>
    <div class="formulation_snippet">

    </div>
</template>
<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { ConstantPart, NaryOpPart } from '../parts';
const part = defineModel<NaryOpPart>({ required: true });
</script>
<style scoped>
.formulation_snippet {
    display: flex;
    flex-direction: row;
    padding: 10px;
    border: 1px solid #ccc;
}
</style>