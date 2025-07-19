<template>
  <div class="wrapper">
    <div class="ticker-box">
      <h2>🔥 이번주 Top 10 추천 종목</h2>
      <ul>
        <li
          v-for="(ticker, index) in tickers"
          :key="index"
          :style="{ animationDelay: `${(tickers.length - index) * 0.3}s` }"
          class="fade-in"
        >
          {{ tickers.length - index }}. {{ ticker }}
        </li>
      </ul>
    </div>

    <form class="subscribe-form" @submit.prevent="submitEmail">
      <input
        v-model="email"
        type="email"
        placeholder="이메일 입력"
        required
      />
      <button type="submit">구독</button>
      <p v-if="message">{{ message }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const tickers = ref([])
const email = ref('')
const message = ref('')

onMounted(async () => {
  try {
    const res = await fetch('https://portfolio-production-54cf.up.railway.app/top-tickers')
    const data = await res.json()
    tickers.value = data.tickers.reverse() // 10위부터 1위
  } catch (e) {
    console.error('❌ 티커 로드 실패:', e)
  }
})

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

<style scoped>
.wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 20px;
  background: #f9f9f9;
  font-family: 'Segoe UI', sans-serif;
  position: relative;
}

.ticker-box {
  background: white;
  padding: 30px 40px;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  text-align: center;
  width: 100%;
  max-width: 500px;
  margin-bottom: 60px;
}

.ticker-box h2 {
  margin-bottom: 20px;
  font-size: 1.5rem;
  color: #333;
}

.ticker-box ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.ticker-box li {
  font-size: 1.25rem;
  font-weight: 600;
  color: #007bff;
  margin-bottom: 8px;
  opacity: 0;
  animation: fadeInUp 0.5s forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.subscribe-form {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 12px 20px;
  border-radius: 40px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 10px;
  align-items: center;
}

.subscribe-form input {
  border: 1px solid #ccc;
  border-radius: 20px;
  padding: 8px 14px;
  outline: none;
  width: 200px;
  font-size: 0.9rem;
}

.subscribe-form button {
  background: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 16px;
  cursor: pointer;
  font-weight: 600;
}

.subscribe-form button:hover {
  background: #0056b3;
}

.subscribe-form p {
  font-size: 0.85rem;
  margin: 0;
  color: #333;
}
</style>
