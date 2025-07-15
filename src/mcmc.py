import numpy as np
import yfinance as yf

def monte_carlo_dcf_valuation(ticker, initial_fcf, wacc, terminal_growth_rate, projection_years=5, num_simulations=10_000):
    # Fetch fundamental data using yfinance
    stock = yf.Ticker(ticker)
    info = stock.info

    # Try to get shares outstanding (fall back to None if unavailable)
    shares_outstanding = info.get('sharesOutstanding')
    if shares_outstanding is None:
        raise ValueError(f"Shares outstanding info not found for ticker {ticker}")

    # Try to get total debt and cash for net debt calculation
    # net_debt = total_debt - cash
    total_debt = info.get('totalDebt') or 0
    cash = info.get('totalCash') or 0
    net_debt = total_debt - cash

    # Parameters for growth rate simulation
    growth_mean = 0.08      # 8%
    growth_std = 0.03       # 3%

    # Prepare storage for simulation results (fair equity values)
    equity_values = []

    for _ in range(num_simulations):
        fcf = initial_fcf
        total_value = 0

        # Simulate yearly cash flows with random growth rate sampled from normal dist
        for year in range(1, projection_years + 1):
            growth_rate = np.random.normal(growth_mean, growth_std)
            fcf *= (1 + growth_rate)
            discounted_fcf = fcf / ((1 + wacc) ** year)
            total_value += discounted_fcf

        # Calculate terminal value (Gordon Growth Model)
        terminal_value = fcf * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)
        discounted_terminal_value = terminal_value / ((1 + wacc) ** projection_years)

        enterprise_value = total_value + discounted_terminal_value

        # Equity value = Enterprise value - Net Debt
        equity_value = enterprise_value - net_debt

        equity_values.append(equity_value)

    equity_values = np.array(equity_values)
    fair_value_per_share = equity_values / shares_outstanding

    mean_val = np.mean(fair_value_per_share)
    median_val = np.median(fair_value_per_share)
    std_val = np.std(fair_value_per_share)
    conf_lower = np.percentile(fair_value_per_share, 2.5)
    conf_upper = np.percentile(fair_value_per_share, 97.5)

    result = (
        f"Mean fair value per share: {mean_val:,.0f} KRW\n"
        f"Median fair value per share: {median_val:,.0f} KRW\n"
        f"Standard deviation: {std_val:,.0f} KRW\n"
        f"95% confidence interval: {conf_lower:,.0f} - {conf_upper:,.0f} KRW"
    )
    return result

# Example usage
if __name__ == "__main__":
    ticker = "103140.KS"  # Samsung Electronics (KOSPI)
    initial_fcf = 300e9   # 300 billion KRW
    wacc = 0.09           # 9%
    terminal_growth_rate = 0.03

    print(monte_carlo_dcf_valuation(ticker, initial_fcf, wacc, terminal_growth_rate))
