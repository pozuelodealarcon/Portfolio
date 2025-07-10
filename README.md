# 🇺🇸 Quantitative Investment Analysis and Optimization Tool with Buffett Methodology


📈 **A program that combines Warren Buffett’s investment philosophy with modern quantitative strategies**  
to analyze U.S. stocks and automatically generate optimized portfolios for mid-term and long-term value investment

## 🔧 Key Features

- Financial data crawling using FinancialModelingPrep API  
- Price data collection and caching via yFinance  
- Calculation of Buffett-style value investing score (B-Score)  
- Momentum scoring based on technical indicators (RSI, MACD, moving averages, etc.)  
- DCF intrinsic value evaluation based on FCF yield and CAGR  
- ESG performance classification  
- Portfolio optimization (Sharpe, Sortino, CVaR, variance minimization)  
- Queries Marketaux API for the three latest and relevant news; returns the headline and summary along with sentiment scores associated with the ticker in each article
- Results saved to Excel and automatically emailed

## 📁 Directory Structure



src/
├── buffett\_us.py        # Main executable file



## ⚙️ Installation

```bash
git clone https://github.com/pozuelodealarcon/Portfolio.git
pip install -r requirements.txt
````

> ⚠️ Set required environment variables in GitHub Secrets or `.env` file:

* `EMAIL_ADDRESS`
* `EMAIL_PASSWORD`
* `FMP_API_KEY`

GitHub Actions automatically:

* Checks and downloads recent price cache
* Calculates value and momentum scores
* Derives optimized portfolio weights
* Generates Excel reports and sends them via email

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

## Disclaimer

* This analysis and all provided information are for reference purposes only.
* The project owner and affiliates disclaim all responsibility for any investment losses or damages.

---

## 📤 Automated Execution (GitHub Actions)

Configured in `.github/workflows/buffett.yml` to run **automatically every Mondays and Fridays at 08:00 KST**.

---

## 📜 License

MIT License
(c) 2025 Hyungsuk Choi ([chs\_3411@naver.com](mailto:chs_3411@naver.com))

```
```

