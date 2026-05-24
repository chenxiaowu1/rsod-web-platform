<template>
  <MainLayout>
    <template #sidebar><Sidebar /></template>
    <template #header><Header @open-login="showModal = true" /></template>
    <template #content><router-view /></template>
  </MainLayout>
  <LoginModal :visible="showModal" @close="showModal = false" @logged-in="onLoggedIn" />
</template>

<script setup>
import { ref, onMounted } from "vue";
import MainLayout from "./layouts/MainLayout.vue";
import Sidebar from "./components/Sidebar.vue";
import Header from "./components/Header.vue";
import LoginModal from "./components/LoginModal.vue";
import { setLoginModalTrigger, notifyLoggedIn } from "./utils/request";
import { refreshAuth } from "./utils/auth";

const showModal = ref(false);

onMounted(() => {
  setLoginModalTrigger(() => { showModal.value = true; });
});

const onLoggedIn = () => {
  showModal.value = false;
  notifyLoggedIn();
  refreshAuth();
};
</script>

<style scoped></style>
