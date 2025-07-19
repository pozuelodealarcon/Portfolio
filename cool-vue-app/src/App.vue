<template>
  <div class="wrapper">
    <div class="report-box">
      <h1>📈 DeepFund AI 리포트</h1>
      <p class="description">
        실적 기반 퀀트 알고리즘이 선정한 이번달 Top 10 가치 종목입니다.<br />
        더 자세한 투자 인사이트와 분석이 궁금하다면 이메일을 등록하세요.
      </p>

      <ul class="ticker-list">
        <li
          v-for="(ticker, index) in tickers"
          :key="index"
          :style="{ animationDelay: `${(tickers.length - index) * 0.3}s` }"
          class="fade-in"
        >
          {{ tickers.length - index }}. {{ ticker }}
        </li>
      </ul>

      <form class="subscribe-form" @submit.prevent="submitEmail">
        <input
          v-model="email"
          type="email"
          placeholder="이메일 입력"
          required
        />
        <button type="submit">구독</button>
      </form>

      <p v-if="message" class="feedback">{{ message }}</p>
    </div>
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
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 30px 20px;
  background: #f3f6fa;
  font-family: 'Segoe UI', sans-serif;
}

.report-box {
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.06);
  padding: 40px;
  max-width: 500px;
  width: 100%;
  text-align: center;
}

h1 {
  font-size: 1.8rem;
  margin-bottom: 12px;
  color: #0d1b2a;
}

.description {
  font-size: 0.95rem;
  color: #4a4a4a;
  margin-bottom: 30px;
  line-height: 1.6;
}

.ticker-list {
  list-style: none;
  padding: 0;
  margin: 0 0 30px;
}

.ticker-list li {
  font-size: 1.2rem;
  font-weight: 600;
  color: #007bff;
  margin-bottom: 10px;
  opacity: 0;
  animation: fadeInUp 0.6s forwards;
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
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 10px;
}

.subscribe-form input {
  padding: 8px 14px;
  border: 1px solid #ccc;
  border-radius: 20px;
  font-size: 0.9rem;
  width: 60%;
  outline: none;
}

.subscribe-form button {
  padding: 8px 18px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-weight: 600;
}

.subscribe-form button:hover {
  background: #0056b3;
}

.feedback {
  margin-top: 12px;
  font-size: 0.85rem;
  color: #444;
}
</style>
