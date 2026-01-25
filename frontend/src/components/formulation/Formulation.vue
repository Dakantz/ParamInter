<template>
    <div class="formulation_view">
        < </div>
</template>
<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';

</script>
<style scoped>
.formulation_view {
    display: flex;
    flex-direction: row;
    padding: 10px;
    border: 1px solid #ccc;
}

.formulation_view>div {
    margin-right: 5px;
}

.formulation_input {
    display: flex;
    flex-direction: column;
}

.formulation_placeholder {
    width: 1.5em;
    border: 2px dashed #ccc;
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>