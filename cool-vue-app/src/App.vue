<template>
  <div class="wrapper">
    <div class="report-box">
      <h1>📈 DeepFund AI 리포트</h1>
      <p class="description">
        워렌 버핏의 보수적인 투자 철학 기반 퀀트 알고리즘이 선정한 이번달 Top 10 가치 종목입니다.<br />
        더 자세한 투자 인사이트와 분석이 궁금하다면 무료 뉴스레터를 구독해보세요.
      </p>

      <!-- 헤더 -->
      <div class="list-header">
        <span class="rank_col">순위</span>
        <span class="ticker_col">종목명</span>
        <span class="change_col">주가 (1개월대비)</span>
      </div>

      <!-- 종목 리스트 -->
      <ul class="ticker-list">
        <li
          v-for="(item, index) in tickers"
          :key="item.ticker"
          :style="{ animationDelay: `${index * 0.3}s` }"
          class="fade-in"
        >
          <span class="rank">{{ tickers.length - index }}.</span>
          <span class="ticker">{{ item.ticker }}</span>
          <span
            class="change"
            :class="{ positive: item.change.startsWith('+'), negative: item.change.startsWith('-') }"
          >
            {{ item.change }}
          </span>
        </li>
      </ul>

      <!-- 구독 폼 -->
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
      headers: { 'Content-Type': 'application/json' },
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

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@500;700&family=Courier+Prime&display=swap');

<style scoped>
.wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(145deg, #f2f6fc, #e6edf7);
  padding: 40px 20px;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
}



.report-box {
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 15px 45px rgba(0, 0, 0, 0.08);
  padding: 48px 32px;
  max-width: 540px;
  width: 100%;
  text-align: center;
}

h1 {
  font-family: 'Noto Sans KR', sans-serif;
  font-size: 1.9rem;
  margin-bottom: 14px;
  color: #1e2a38;
  font-weight: 700;
}

.description {
  font-size: 0.82rem;
  color: #5c5c5c;
  margin-bottom: 32px;
  line-height: 1.7;
  font-weight: 500;
}

.list-header {
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: 'Noto Sans KR', sans-serif;
  font-weight: 700;
  font-size: 0.90rem;
  border-bottom: 2px solid #e3e8ef;
  padding-bottom: 10px;
  margin-bottom: 12px;
  color: #3b3b3b;
}

.list-header span {
  flex: 1;
  text-align: center;
}

.ticker-list {
  list-style: none;
  padding: 0;
  margin: 0 0 30px;
  display: flex;
  flex-direction: column-reverse;
}

.ticker-list li {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 14px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #0066cc;
  margin-bottom: 16px;
  opacity: 0;
  animation: fadeInSlide 0.6s forwards;
  font-family: 'Inter', sans-serif;
}

.rank {
  flex: 1;
  color: #2d3e50;
  font-weight: 800;
  text-align: center;
  font-family: 'Courier Prime', monospace;
  font-size: 1.1rem;
}

.ticker {
  flex: 1;
  text-align: center;
  color: #114477;
  letter-spacing: 0.01em;
}

.change {
  flex: 1;
  font-size: 1.1rem;
  text-align: center;
  padding: 5px 12px;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.2s ease-in-out;
}

.rank_col {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(145deg, #f2f6fc, #e6edf7);
  padding: 40px 20px;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
}

.ticker_col {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(145deg, #f2f6fc, #e6edf7);
  padding: 40px 20px;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
}

.change_col {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(145deg, #f2f6fc, #e6edf7);
  padding: 40px 20px;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
}

.change.positive {
  background-color: #e2f4e9;
  color: #1e7b45;
}

.change.negative {
  background-color: #fdecea;
  color: #c0392b;
}

@keyframes fadeInSlide {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 구독 폼 */
.subscribe-form {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.subscribe-form input {
  padding: 10px 18px;
  border: 1px solid #ccd6e0;
  border-radius: 20px;
  font-size: 1rem;
  width: 65%;
  max-width: 280px;
  font-family: 'Inter', sans-serif;
  transition: border-color 0.25s ease;
}

.subscribe-form input:focus {
  border-color: #007bff;
  outline: none;
}

.subscribe-form button {
  padding: 10px 22px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border: none;
  border-radius: 22px;
  cursor: pointer;
  font-weight: 700;
  font-size: 1rem;
  transition: background 0.3s ease;
  font-family: 'Inter', sans-serif;
}

.subscribe-form button:hover {
  background: linear-gradient(135deg, #0056b3, #003e91);
}

.feedback {
  margin-top: 16px;
  font-size: 0.85rem;
  color: #333;
  font-family: 'Inter', sans-serif;
}
</style>
