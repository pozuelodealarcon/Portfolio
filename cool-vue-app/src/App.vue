<template>
  <div class="container">
    <h1>📧 버핏식 투자 분석자료 구독 신청</h1>
    <form @submit.prevent="submitEmail">
      <input
        v-model="email"
        type="email"
        placeholder="Enter your email"
        required
      />
      <button type="submit">Subscribe</button>
    </form>
    <p v-if="message">{{ message }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const email = ref('')
const message = ref('')



const submitEmail = async () => {
  try {
    const response = await fetch('https://portfolio-production-54cf.up.railway.app/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: email.value }),
    })
    const data = await response.json()
    message.value = data.message || '✅ 구독이 완료되었습니다.'
    email.value = ''
  } catch (err) {
    message.value = '⚠️ 이메일 구독 중 오류가 발생했습니다.'
    console.error('❌ Fetch Error:', err)
  }
}

</script>

<style>
.container {
  max-width: 390px;
  margin: 100px auto;
  text-align: center;
  font-family: Arial;
}
input {
  padding: 10px;
  width: 80%;
  border-radius: 8px;
  border: 1px solid #ccc;
  margin-bottom: 10px;
}
button {
  padding: 10px 20px;
  background: #007bff;
  border: none;
  color: white;
  border-radius: 8px;
  cursor: pointer;
}
button:hover {
  background: #0056b3;
}
</style>
