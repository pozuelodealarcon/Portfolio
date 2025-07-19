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
        <span class="rank">순위</span>
        <span class="ticker">종목명</span>
        <span class="change">주가 (1개월대비)</span>
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

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&display=swap');
<style scoped>
.wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 30px 20px;
  background: #f3f6fa;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
  font-weight: 700;
  letter-spacing: -0.02em;
}

.description {
  font-size: 1rem;
  color: #4a4a4a;
  margin-bottom: 30px;
  line-height: 1.6;
  font-weight: 500;
  letter-spacing: -0.01em;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 컬럼 헤더 - 한글용 Noto Sans KR */
.list-header {
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: 'Noto Sans KR', sans-serif;
  font-weight: 800;
  font-size: 1rem;
  padding-bottom: 10px;
  border-bottom: 2px solid #dee2e6;
  margin-bottom: 10px;
  color: #495057;
}

.list-header .rank,
.list-header .ticker,
.list-header .change {
  flex: 1;
  text-align: center;
}

/* 리스트 */
.ticker-list {
  list-style: none;
  padding: 0;
  margin: 0 0 30px;
  display: flex;
  flex-direction: column-reverse;
}

.ticker-list li {
  font-weight: 600;
  font-size: 1.25rem;
  color: #007bff;
  margin-bottom: 14px;
  opacity: 0;
  animation: fadeInUp 0.6s forwards;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.rank {
  flex: 1;
  color: #001f4d;
  font-weight: 900;
  text-align: center;
  font-family: 'Courier New', monospace;
}

.ticker {
  flex: 1;
  text-align: center;
  color: #004085;
  letter-spacing: 0.01em;
  font-variant: normal;
}

.change {
  flex: 1;
  font-weight: 600;
  font-size: 1.1rem;
  text-align: center;
  border-radius: 10px;
  padding: 4px 10px;
  user-select: none;
}

.change.positive {
  background-color: #d4edda;
  color: #155724;
}

.change.negative {
  background-color: #f8d7da;
  color: #721c24;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.subscribe-form {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 15px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.subscribe-form input {
  padding: 10px 16px;
  border: 1px solid #c1c7d0;
  border-radius: 22px;
  font-size: 1rem;
  width: 65%;
  outline: none;
  transition: border-color 0.25s ease;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.subscribe-form input:focus {
  border-color: #007bff;
}

.subscribe-form button {
  padding: 10px 26px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 22px;
  cursor: pointer;
  font-weight: 700;
  font-size: 1rem;
  transition: background-color 0.3s ease;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.subscribe-form button:hover {
  background: #0056b3;
}

.feedback {
  margin-top: 14px;
  font-size: 0.9rem;
  color: #333;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
</style>
