# Buffet Style Quantitative Investment Analysis and Optimization Program


### A **full-stack program** that combines Warren Buffett’s investment philosophy with modern quantitative strategies and AI-powered analysis to analyze U.S. stocks, interpret market sentiment, and automatically generate optimized portfolios for mid- and long-term value investing

### 💌 [Join Our Free Stock Insights Newsletter](https://portfolio-production-54cf.up.railway.app/)

> Get Buffett-style stock picks, AI-driven market news, and optimized portfolios—delivered automatically.
---

## 🔧 Key Features

* Financial data crawling using FinancialModelingPrep API
* Price data collection and caching via yFinance
* Calculation of Buffett-style value investing score (B-Score)
* Momentum scoring based on technical indicators (RSI, MACD, moving averages, etc.)
* Portfolio optimization using Modern Portfolio Theory (Sharpe, Sortino, CVaR, variance minimization)
* Queries Marketaux API for the latest news
* **DCF intrinsic value evaluation based on 10,000 Monte Carlo simulations per ticker**
* **AI-powered macroeconomic and news sentiment analysis using Gemini 2.5 Flash**
* **Vue.js frontend for subscription web and Flask API backend running on Railway**
* Results saved to Excel and automatically emailed to subscribers

---

## 📁 Directory Structure

```
src/
├── buffett_us.py         # Main analysis script
cool-vue-app/src/
├── App.vue             # Vue.js frontend for subscription web
server.py                # Flask backend for managing email subscriptions
recipients.json       # Auto-updated subscriber email list
```

---

## 1. Analysis Logic

### ① Valuation Metrics

* **Indicators:** PBR, PER, DCF, etc.
* Considers relative undervaluation against industry averages
* Some metrics are normalized into rank scores for evaluation

### ② Financial Health Assessment

* **Indicators:** D/E, CR, ICR, ROE, ROA, EPS growth, dividend growth, operating margin, etc.
* Scoring criteria defined in the `buffett_score()` function
* Example:

  * D/E ≤ 0.5 → +1 point
  * EPS < 0 → deduction

### ③ Momentum Scoring

* Points accumulated when technical conditions met:

  * 20-day MA > 60-day MA (medium-term uptrend)
  * 50-day MA > 200-day MA (long-term breakout)
  * 20-day/60-day returns ≥ 10%
  * RSI rebound confirmation
  * MACD golden cross

### ④ AI-Powered Sentiment & Macroeconomic Summary

* Uses **Gemini 2.5 Flash Google Search** to:

  * Summarize recent macroeconomic trends
  * Interpret news articles with sentiment scoring
  * Generate stock picks based on quantitative + narrative alignment

---

## 2. Scoring and Stock Selection

* **B-Score** = Valuation score + Financial health score
* Total score = B-Score + Momentum score
* Select top X stocks by total score to build the portfolio

---

## 3. DCF Intrinsic Value Calculation

* Uses past 5 years of Free Cash Flow (FCF) data
* Intrinsic value calculated via DCF model based on FCF growth and discount rate
* Assesses undervaluation compared to current market price

---

## 4. Portfolio Optimization

* Calculates portfolio weights based on top stocks under four optimization criteria:

| Criterion | Objective Function                           |
| --------- | -------------------------------------------- |
| Sharpe    | Maximize annual return / volatility          |
| Sortino   | Maximize annual return / downside volatility |
| CVaR      | Minimize average loss in worst 5% scenarios  |
| Variance  | Minimize overall return variance             |

* Results saved in separate Excel sheets (e.g., `Weights_CVaR`, `Weights_Sharpe`, etc.)

---

## 📤 Automation & Deployment

### ✅ GitHub Actions

* Configured in `.github/workflows/buffett.yml` to run **every Monday, Wednesday, and Friday at 08:00 KST**
* Auto-downloads prices, computes scores, optimizes weights, and sends results via email

### ✅ Railway Deployment

* **Flask backend + Vue frontend** deployed via Railway
* Public-facing email subscription system with auto-update to `recipients.json`
* Auto commits/pushes email of a new subscriber to GitHub using REST API

---

## Disclaimer

* This analysis and all provided information are for reference purposes only.
* The project owner and affiliates disclaim all responsibility for any investment losses or damages.

---

## 📜 License

MIT License
(c) 2025 Hyungsuk Choi ([chs\_3411@naver.com](mailto:chs_3411@naver.com))
