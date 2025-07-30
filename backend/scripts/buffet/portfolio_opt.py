import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import skew, kurtosis, gmean


def objective_sharpe(weights, returns):
    port_return = np.dot(weights, returns.mean()) * 252
    port_vol = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    return -port_return / port_vol


def objective_cvar(weights, returns):
    portfolio_returns = returns.dot(weights)
    alpha = 0.05
    var = np.percentile(portfolio_returns, 100 * alpha)
    cvar = portfolio_returns[portfolio_returns <= var].mean()
    return cvar


def objective_sortino(weights, returns):
    portfolio_returns = returns.dot(weights)
    mean_return = portfolio_returns.mean() * 252
    downside_std = portfolio_returns[portfolio_returns < 0].std() * np.sqrt(252)
    if downside_std == 0:
        return 0
    return -mean_return / downside_std


def objective_variance(weights, returns):
    return np.dot(weights.T, np.dot(returns.cov() * 252, weights))


def max_drawdown(return_series):
    comp_ret = (1 + return_series).cumprod()
    peak = comp_ret.expanding(min_periods=1).max()
    dd = (comp_ret / peak) - 1
    return dd.min()


def detailed_portfolio_statistics(weights, returns):
    portfolio_returns = returns.dot(weights)
    mean_return = gmean(portfolio_returns + 1) ** 252 - 1
    std_dev = portfolio_returns.std() * np.sqrt(252)
    skewness = skew(portfolio_returns)
    kurt = kurtosis(portfolio_returns)
    max_dd = max_drawdown(portfolio_returns)
    try:
        tnx = np.nan  # ...existing code for TNX fetch...
        risk_free_rate = 0.04
    except Exception:
        risk_free_rate = 0.04
    sharpe_ratio = (mean_return - risk_free_rate) / std_dev
    alpha = 0.05
    sorted_returns = np.sort(portfolio_returns)
    var_index = int(np.floor(alpha * len(sorted_returns)))
    var = sorted_returns[var_index]
    cvar = sorted_returns[:var_index].mean()
    cvar_ann = (1 + cvar) ** 252 - 1
    downside_std = portfolio_returns[portfolio_returns < 0].std() * np.sqrt(252)
    sortino = mean_return / downside_std if downside_std != 0 else np.nan
    variance = std_dev**2
    return (
        mean_return,
        std_dev,
        skewness,
        kurt,
        max_dd,
        len(portfolio_returns),
        sharpe_ratio,
        cvar_ann,
        sortino,
        variance,
    )
