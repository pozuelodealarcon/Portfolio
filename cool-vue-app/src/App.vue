<template>
  <div class="wrapper">
    <!-- 리본 -->
    <div class="ticker-ribbon">
      <div class="scrolling-text" v-html="marketRibbon"></div>
    </div>

    <div class="report-box">
      <h1>📈 DeepFund AI 리포트</h1>
      <p class="description">
        <span class="typewriter">{{ typedText }}</span>
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
      <p class="copyright">©2025 Hyungsuk Choi, University of Maryland</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const tickers = ref([])
const email = ref('')
const message = ref('')
const typedText = ref('')
const marketRibbon = ref('로딩 중...')

const fullText =
  '워렌 버핏의 투자 원칙을 반영한 퀀트 알고리즘이 선정한 이번 달 Top 10 가치주입니다. 보다 깊이 있는 분석과 인사이트는 무료 뉴스레터에서 확인하세요.'

// 📈 마켓 리본 텍스트 업데이트 함수
const updateRibbon = async () => {
  try {
    const res = await fetch('/api/market-data')
    const data = await res.json()
    const parts = Object.entries(data).map(
      ([name, info]) => `${name} ${info.price} ${info.change}`
    )
    marketRibbon.value = parts.join(" &nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp; ")

  } catch (err) {
    console.error('데이터 가져오기 실패:', err)
    marketRibbon.value = '📡 마켓 데이터 로드 실패'
  }
}

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

onMounted(async () => {
  // 종목 데이터 로드
  try {
    const res = await fetch('https://portfolio-production-54cf.up.railway.app/top-tickers')
    const data = await res.json()
    tickers.value = data.tickers.reverse()
  } catch (e) {
    console.error('❌ 티커 로드 실패:', e)
  }

  // 타이핑 효과
  let i = 0
  const typeInterval = setInterval(() => {
    typedText.value += fullText[i]
    i++
    if (i >= fullText.length) clearInterval(typeInterval)
  }, 30)

  // 마켓 리본 초기화 및 주기적 갱신
  await updateRibbon()
  setInterval(updateRibbon, 30000)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

/* 공통 스타일 */
.wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(145deg, #f2f6fc, #e6edf7);
  padding: 70px 20px 40px; /* 리본 고정 높이 + 여유 */
  font-family: 'Noto Sans KR', sans-serif;
  box-sizing: border-box;
}

/* 리본 슬라이딩 */
.ticker-ribbon {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  width: 100%;
  background: #0b3c5d;
  color: #fff;
  overflow: hidden;
  white-space: nowrap;
  font-weight: 600;
  font-size: 0.85rem;
  padding: 10px 0;
  box-sizing: border-box;
}

.scrolling-text {
  display: inline-block;
  padding-left: 100%;
  animation: scroll-left 40s linear infinite;
}

@keyframes scroll-left {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-100%);
  }
}

/* 보고서 박스 */
.report-box {
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 15px 45px rgba(0, 0, 0, 0.08);
  padding: 48px 32px;
  max-width: 540px;
  width: 100%;
  text-align: center;
}

/* 제목 */
h1 {
  font-size: 1.9rem;
  margin-bottom: 14px;
  color: #1e2a38;
  font-weight: 700;
}

/* 설명 타이핑 */
.description {
  font-size: 0.85rem;
  color: #5c5c5c;
  margin-bottom: 32px;
  line-height: 1.6;
  font-weight: 500;
  min-height: 3.4em;
}

.typewriter {
  border-right: 2px solid #aaa;
  white-space: pre-wrap;
  overflow: hidden;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  50% {
    border-color: transparent;
  }
}

@keyframes fadeInSlide {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 리스트 헤더 */
.list-header {
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 700;
  font-size: 0.9rem;
  border-bottom: 2px solid #e3e8ef;
  padding-bottom: 10px;
  margin-bottom: 12px;
  color: #3b3b3b;
}

.list-header span {
  flex: 1;
  text-align: center;
  font-family: 'Noto Sans KR', sans-serif; /* 명확히 지정 */
  font-weight: 700;
  font-size: 0.9rem;
  color: #3b3b3b;

}

/* 종목 리스트 */
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
}

.rank {
  flex: 1;
  color: #2d3e50;
  font-weight: 800;
  text-align: center;
  font-size: 1.1rem;
  font-family: 'Courier Prime', monospace; /* 이건 숫자 가독성 위해 유지 */
}

.ticker {
  flex: 1;
  text-align: center;
  color: #114477;
  letter-spacing: 0.01em;
  font-weight: 400;
}

.change {
  flex: 1;
  font-size: 1.1rem;
  text-align: center;
  padding: 5px 12px;
  border-radius: 12px;
  transition: all 0.2s ease-in-out;
  font-weight: 400;
}

.change.positive {
  background-color: #e2f4e9;
  color: #1e7b45;
}

.change.negative {
  background-color: #fdecea;
  color: #c0392b;
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
  font-family: 'Noto Sans KR', sans-serif;
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
  font-family: 'Noto Sans KR', sans-serif;
}

.subscribe-form button:hover {
  background: linear-gradient(135deg, #0056b3, #003e91);
}

/* 피드백 메시지 */
.feedback {
  margin-top: 16px;
  font-size: 0.85rem;
  color: #333;
  font-family: 'Noto Sans KR', sans-serif;
}

/* 카피라이트 */
.copyright {
  margin-top: 24px;
  font-size: 0.75rem;
  color: #999;
}

</style>
