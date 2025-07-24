<template>
  <div class="wrapper">
    <!-- 리본 -->
    <div class="ticker-ribbon">
      <div class="scrolling-text" v-html="marketRibbon"></div>
    </div>

    <div class="report-box">
      <img
        :src="logo"
        alt="DeepFund AI 로고"
        class="logo fade-in"
        :style="{ animationDelay: '0.2s' }"
      />
      <div class="description-wrap">
        <p class="description">
          <span class="typewriter" v-html="typedText"></span>
        </p>
        <transition name="fade">
          <span
            v-if="showInfoIcon"
            class="info-icon info-icon-absolute"
            @click="showPrinciple = !showPrinciple"
            title="투자원칙 설명"
          >i</span>
        </transition>
        <div v-if="showPrinciple" class="principle-popup" @click.stop>
          <strong>DeepFund는 투자 판단의 근거를 밸류에이션, 실적 모멘텀, 그리고 가격/수급이라는 세 가지 범주로 나누어 체계적으로 평가합니다.</strong><br><br>
          <b>🏦 밸류에이션이란?</b><br>
          <span class="principle-bullet">기업의 내재가치는 장기적인 투자 성과의 핵심입니다. 밸류에이션 분석은 현재 주가가 그 기업의 실제 가치에 비해 과대평가되어 있는지, 혹은 저평가되어 있는지를 평가하는 과정입니다.</span><br>
          <b>밸류에이션 팩터 (7개):</b><br>
          <span class="principle-bullet">• DCF(할인현금흐름)</span>
          <span class="principle-bullet">• PER(주가수익비율)</span>
          <span class="principle-bullet">• PBR(주가순자산비율)</span>
          <span class="principle-bullet">• FCF수익률</span>
          <span class="principle-bullet">• 업종 PER 비교</span>
          <span class="principle-bullet">• 부채비율(D/E), 유동비율(CR)</span><br>
          <b>📈 실적모멘텀이란?</b><br>
          <span class="principle-bullet">가치투자의 핵심은 "훌륭한 기업을 적정한 가격에 사는 것"입니다. 실적 모멘텀은 기업이 지속적인 수익 창출 역량과 재무 건전성을 보유하고 있는지를 평가합니다.</span><br>
          <b>실적모멘텀 팩터 (6개):</b><br>
          <span class="principle-bullet">• ROE/ROA Z-Score</span>
          <span class="principle-bullet">• 이자보상비율(ICR)</span>
          <span class="principle-bullet">• FCF 성장률 (5년간)</span>
          <span class="principle-bullet">• EPS 성장률 (5년간)</span>
          <span class="principle-bullet">• 배당 성장률 (10년간)</span>
          <span class="principle-bullet">• 영업이익 성장률 (최근 4개 분기, 4개 년도 대비)</span><br>
          <b>💰 가격/수급이란?</b><br>
          <span class="principle-bullet">단기적 주가 흐름은 시장의 감정과 수급에 의해 좌우됩니다. 투자자는 이를 통해 기회와 리스크를 선별할 수 있어야 합니다.</span><br>
          <b>가격/수급 팩터 (5개):</b><br>
          <span class="principle-bullet">• 이동평균선 크로스오버 (20/60일선, 50/200일선)</span>
          <span class="principle-bullet">• 단기/중기 수익률 (20/60일)</span>
          <span class="principle-bullet">• MACD 골든크로스</span>
          <span class="principle-bullet">• RSI 반등 신호</span>
          <span class="principle-bullet">• 거래량 변화</span>
        </div>
      </div>

      <!-- 헤더 -->
      <div class="list-header fade-in" :style="{ animationDelay: '3.1s' }">
        <span class="rank">순위</span>
        <span class="ticker">종목명</span>
        <span class="change">주가 (1개월▲)</span>
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
          <a
      class="ticker"
      :href="`https://www.google.com/search?q=${encodeURIComponent(item.ticker)}`"
      target="_blank"
      rel="noopener noreferrer"
      style="text-decoration: underline; color: #114477; cursor: pointer;"
    >
      {{ item.ticker }}
    </a>
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

      <!-- 페이지 맨 아래에 위치할 구간 -->
      <div id="newsletter"></div>


      <p v-if="message" class="feedback">{{ message }}</p>
      <p class="copyright">©2025 Hyungsuk Choi, University of Maryland</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import logo from './logo.png'

const tickers = ref([])
const email = ref('')
const message = ref('')
const typedText = ref('')
const marketRibbon = ref('로딩 중...')
const showPrinciple = ref(false)
const showInfoIcon = ref(false)

const fullText =
  `<span style="font-weight:700; color:#114477;">워렌 버핏</span>의 투자 원칙을 반영한 퀀트 알고리즘이 선정한 
  <span style="color:#007bff; font-weight:800;">이번 달 Top 10 가치주</span>입니다.<br>
  심층 분석과 인사이트는 무료 <a href="#newsletter" class="scroll-link" style="color:#007bff; font-weight:700; text-decoration: underline; cursor: pointer;">뉴스레터</a>에서 확인하세요.`;

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
    marketRibbon.value = '📡 페이지를 새로고침해 주시기 바랍니다.'
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

function handleClickOutside(e) {
  if (!e.target.closest('.info-icon') && !e.target.closest('.principle-popup')) {
    showPrinciple.value = false
  }
}
onMounted(async () => {
  // ① 종목 데이터 로드
  try {
    const res = await fetch('https://portfolio-production-54cf.up.railway.app/top-tickers')
    const data = await res.json()
    tickers.value = data.tickers.reverse()
  } catch (e) {
    console.error('❌ 티커 로드 실패:', e)
  }

  // ② 타이핑 효과 시작
  let i = 0;
  let tempText = '';

  const typeInterval = setInterval(() => {
    if (i >= fullText.length) {
      clearInterval(typeInterval);
      setTimeout(() => {
        showInfoIcon.value = true
        // 타이핑 완료 후 스크롤 이벤트 연결 (한 번만 실행)
        setTimeout(() => {
          const link = document.querySelector('.scroll-link');
          const target = document.getElementById('newsletter');
          if (link && target) {
            link.addEventListener('click', (e) => {
              e.preventDefault();
              target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
          }
        }, 100);
      }, 200); // typewriter 끝나고 0.2초 후 i 아이콘 등장
      return;
    }

    const char = fullText[i];

    if (char === '<') {
      // 태그 시작: 끝까지 찾아서 한 번에 붙이기
      const tagEnd = fullText.indexOf('>', i);
      if (tagEnd !== -1) {
        tempText += fullText.substring(i, tagEnd + 1);
        i = tagEnd + 1;
      } else {
        // 예외 처리: 태그가 닫히지 않았을 경우
        tempText += char;
        i++;
      }
    } else {
      // 일반 텍스트는 한 글자씩
      tempText += char;
      i++;
    }

    typedText.value = tempText;
  }, 30);
  // 마켓 리본 초기화 및 주기적 갱신
  await updateRibbon()
  setInterval(updateRibbon, 30000)

  document.addEventListener('click', handleClickOutside)
});
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})


</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

.logo {
  width: 100%;
  max-width: 400px;   /* 원하는 크기로 키우기 (예: 300px) */
  height: auto;
  margin-top: 8px;    /* 위쪽 마진 줄이기 */
  margin-bottom: 8px; /* 아래쪽 마진 줄이기 */
  display: block;
  margin-left: auto;
  margin-right: auto;
}


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
  position: relative;
  font-size: 1.2rem;
  color: #5c5c5c;
  margin-bottom: 32px;
  line-height: 2.0;
  font-weight: 700;
  min-height: 3.4em;
  text-align: center;
}
.info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
  font-size: 0.95em;
  font-weight: bold;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  color: #007bff;
  border: 1.5px solid #007bff;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  user-select: none;
  transition: background 0.2s;
}
.info-icon:hover {
  background: #007bff;
  color: #fff;
}
.principle-popup {
  position: absolute;
  top: 32px;
  right: 0;
  z-index: 10;
  background: #fff;
  color: #222;
  border: 1px solid #ccd6e0;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.10);
  padding: 16px 18px;
  font-size: 0.98em;
  min-width: 180px;
  text-align: left;
  line-height: 1.7;
  animation: fadeInUp 0.3s;
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.5s cubic-bezier(.4,0,.2,1), transform 0.5s cubic-bezier(.4,0,.2,1);
}
.principle-bullet {
  color: #666a73;
  font-size: 0.97em;
  font-weight: 500;
  letter-spacing: 0.01em;
  display: block;
  margin-left: 2px;
  margin-bottom: 1px;
}

@media (max-width: 480px) {
  .description {
    font-size: 1.05rem;
    font-weight: 500;
    line-height: 1.6;
    color: #444;
  }

  .ticker-list li {
    font-size: 1rem;
  }

  .subscribe-form input,
  .subscribe-form button {
    font-size: 0.95rem;
  }

  .principle-popup {
    right: auto;
    left: 0;
    min-width: 140px;
    font-size: 0.92em;
    padding: 12px 16px;
  }
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
  font-family: 'Noto Sans KR', sans-serif;
}

.ticker {
  flex: 1;
  text-align: center;
  color: #114477;
  letter-spacing: 0.01em;
  font-weight: 500;
  text-decoration: none;
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
  font-family: 'Noto Sans KR', sans-serif;
  padding: 10px 22px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border: none;
  border-radius: 22px;
  cursor: pointer;
  font-weight: 700;
  font-size: 1rem;
  transition: background 0.3s ease;
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

.fade-in {
  opacity: 0;
  transform: translateY(10px);
  animation-fill-mode: forwards;
  animation-name: fadeInUp;
  animation-duration: 0.6s;
  animation-timing-function: ease-out;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

html {
  scroll-behavior: smooth;
}

.description-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.info-icon-absolute {
  position: absolute;
  top: 0;
  right: 40px;
  z-index: 20;
  width: 17px;         /* 동그라미 크기 줄임 */
  height: 17px;        /* 동그라미 크기 줄임 */
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85em;   /* i 글자 크기 줄임 */
  font-weight: bold;
  border-radius: 50%;
  background: #fff;
  color: #007bff;
  border: 1.2px solid #007bff;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  user-select: none;
  transition: background 0.2s;
}
.ticker:hover {
  color: #0056b3;
  text-decoration: underline;
  background: rgba(0,0,0,0.02);
  border-radius: 6px;
  transition: color 0.15s, background 0.15s;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s cubic-bezier(.4,0,.2,1), transform 0.5s cubic-bezier(.4,0,.2,1);
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
/* 기존 .info-icon, .principle-popup, .principle-bullet 등 스타일 유지 */
</style>
