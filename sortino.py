import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import norm
from scipy.stats import skew, kurtosis
from scipy.stats.mstats import gmean
from datetime import datetime, timedelta
import shelve

# Seleccionar Criterio de Optimización
optimization_criterion = 'sortino'  # Cambia a 'sharpe', 'cvar', 'sortino' o 'variance' para optimizar esos criterios

# Elegir Acciones por agregar al Protafolio y Seleccionar periodo de muestra
# symbols = ['379800.KS', '379810.KS', 'BTC-KRW', '047810.KS', '012450.KS', 'AAPL', 'MSFT', 'NVDA', 'GOOG', 'AMZN', 'META', 'BRK-B', 'AVGO', 'TSM', 'WMT', 'LLY', 'JPM']
symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOG', 'AMZN', 'META', 'BRK-B', 'AVGO', 'TSM', 'WMT', 'LLY', 'JPM', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'KO', 'PFE']

# with shelve.open("ticker_cache") as cache:
#     for ticker, name in cache.items():
#         symbols.append(ticker)

# 오늘 날짜
end_date = datetime.today()

# 1년 전 날짜 (365일 전)
start_date = end_date - timedelta(days=365)

# 문자열 포맷으로 변환 (yfinance에 맞게)
start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

# 데이터 다운로드
data = yf.download(symbols, start=start_str, end=end_str, auto_adjust=True)['Close']



returns = data.pct_change().dropna()
# Sharpe Ratio 최적화 함수
def objective_sharpe(weights): 
    port_return = np.dot(weights, returns.mean()) * 252
    port_vol = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    return -port_return / port_vol  # 최대화 위해 음수

# CVaR 최적화 함수 (5% VaR 기준)
def objective_cvar(weights):
    portfolio_returns = returns.dot(weights)  # 수정: np.dot(returns, weights)도 가능하지만 DataFrame이면 .dot이 더 안전
    alpha = 0.05
    var = np.percentile(portfolio_returns, 100 * alpha)
    cvar = portfolio_returns[portfolio_returns <= var].mean()
    return cvar  # minimize에서 최소화(손실 최대화) → 부호 바꿔야 함
    # return -cvar  # CVaR 최대화하려면 음수로 반환

# Sortino Ratio 최적화 함수
def objective_sortino(weights):
    portfolio_returns = returns.dot(weights)  # 수정: np.dot(weights) → returns.dot(weights)
    mean_return = portfolio_returns.mean() * 252
    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    if downside_std == 0:
        return 0  # 또는 큰 값 반환
    sortino_ratio = mean_return / downside_std
    return -sortino_ratio  # 최대화 위해 음수

# 분산 최소화 함수
def objective_variance(weights):
    return np.dot(weights.T, np.dot(returns.cov() * 252, weights))

# Las restricciones
cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

# Los límites para los pesos
bounds = tuple((0, 1) for x in range(len(symbols)))


# Optimización
init_guess = np.array(len(symbols) * [1. / len(symbols),])
if optimization_criterion == 'sharpe':
    opt_results = minimize(objective_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
elif optimization_criterion == 'cvar':
    opt_results = minimize(objective_cvar, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
elif optimization_criterion == 'sortino':
    opt_results = minimize(objective_sortino, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
elif optimization_criterion == 'variance':
    opt_results = minimize(objective_variance, init_guess, method='SLSQP', bounds=bounds, constraints=cons)

# Los pesos óptimos
optimal_weights = opt_results.x


# Optimizar todos los criterios
opt_results_cvar = minimize(objective_cvar, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
opt_results_sortino = minimize(objective_sortino, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
opt_results_variance = minimize(objective_variance, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
opt_results_sharpe = minimize(objective_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=cons)

# Pesos óptimos para cada criterio
optimal_weights_cvar = opt_results_cvar.x
optimal_weights_sortino = opt_results_sortino.x
optimal_weights_variance = opt_results_variance.x
optimal_weights_sharpe = opt_results_sharpe.x

# Graficar la frontera eficiente
port_returns = []
port_volatility = []
sharpe_ratio = []
all_weights = []  # almacena los pesos de todas las carteras simuladas

num_assets = len(symbols)
num_portfolios = 50000

np.random.seed(101)

for single_portfolio in range(num_portfolios):
    weights = np.random.random(num_assets)
    weights /= np.sum(weights)
    returns_portfolio = np.dot(weights, returns.mean()) * 252
    volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    sr = returns_portfolio / volatility
    sharpe_ratio.append(sr)
    port_returns.append(returns_portfolio)
    port_volatility.append(volatility)
    all_weights.append(weights)  # registra los pesos para esta cartera

plt.figure(figsize=(12, 8))
plt.scatter(port_volatility, port_returns, c=sharpe_ratio, cmap='viridis')
plt.colorbar(label='Sharpe Ratio')
plt.xlabel('Volatility')
plt.ylabel('Return')

# Calcular y graficar los retornos y la volatilidad del portafolio óptimo para cada criterio
opt_returns_cvar = np.dot(optimal_weights_cvar, returns.mean()) * 252
opt_volatility_cvar = np.sqrt(np.dot(optimal_weights_cvar.T, np.dot(returns.cov() * 252, optimal_weights_cvar)))
opt_portfolio_cvar = plt.scatter(opt_volatility_cvar, opt_returns_cvar, color='hotpink', s=50, label='CVaR')

opt_returns_sortino = np.dot(optimal_weights_sortino, returns.mean()) * 252
opt_volatility_sortino = np.sqrt(np.dot(optimal_weights_sortino.T, np.dot(returns.cov() * 252, optimal_weights_sortino)))
opt_portfolio_sortino = plt.scatter(opt_volatility_sortino, opt_returns_sortino, color='g', s=50, label='Sortino')

opt_returns_variance = np.dot(optimal_weights_variance, returns.mean()) * 252
opt_volatility_variance = np.sqrt(np.dot(optimal_weights_variance.T, np.dot(returns.cov() * 252, optimal_weights_variance)))
opt_portfolio_variance = plt.scatter(opt_volatility_variance, opt_returns_variance, color='b', s=50, label='Variance')

opt_returns_sharpe = np.dot(optimal_weights_sharpe, returns.mean()) * 252
opt_volatility_sharpe = np.sqrt(np.dot(optimal_weights_sharpe.T, np.dot(returns.cov() * 252, optimal_weights_sharpe)))
opt_portfolio_sharpe = plt.scatter(opt_volatility_sharpe, opt_returns_sharpe, color='r', s=50, label='Sharpe')

plt.legend(loc='upper right')

plt.show()


# Función para calcular el drawdown máximo
def max_drawdown(return_series):
    comp_ret = (1 + return_series).cumprod()
    peak = comp_ret.expanding(min_periods=1).max()
    dd = (comp_ret/peak) - 1
    return dd.min()

def detailed_portfolio_statistics(weights):
    portfolio_returns = returns.dot(weights)
    mean_return_annualized = gmean(portfolio_returns + 1)**252 - 1
    std_dev_annualized = portfolio_returns.std() * np.sqrt(252)
    skewness = skew(portfolio_returns)
    kurt = kurtosis(portfolio_returns)
    max_dd = max_drawdown(portfolio_returns)
    count = len(portfolio_returns)
    tnx = yf.Ticker("^TNX")
    tnx_data = tnx.history(period="1d")
    latest_yield = tnx_data['Close'].iloc[-1]
    risk_free_rate = round(latest_yield/100.0, 2)
    sharpe_ratio = (mean_return_annualized - risk_free_rate) / std_dev_annualized

    # CVaR 계산 (5% 수준)
    alpha = 0.05
    sorted_returns = np.sort(portfolio_returns)
    var_index = int(np.floor(alpha * len(sorted_returns)))
    var = sorted_returns[var_index]
    cvar = sorted_returns[:var_index].mean()
    # 연율화
    cvar_annualized = (1 + cvar) ** 252 - 1

    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_std_dev = downside_returns.std() * np.sqrt(252)
    sortino_ratio = mean_return_annualized / downside_std_dev if downside_std_dev != 0 else np.nan
    variance = std_dev_annualized ** 2 
    
    return mean_return_annualized, std_dev_annualized, skewness, kurt, max_dd, count, sharpe_ratio, cvar_annualized, sortino_ratio, variance
# Calcular estadísticas para cada portafolio
statistics_cvar = detailed_portfolio_statistics(optimal_weights_cvar)
statistics_sortino = detailed_portfolio_statistics(optimal_weights_sortino)
statistics_variance = detailed_portfolio_statistics(optimal_weights_variance)
statistics_sharpe = detailed_portfolio_statistics(optimal_weights_sharpe)

# Nombres de las estadísticas
statistics_names = ['Retorno anualizado', 'Volatilidad anualizada', 'Skewness', 'Kurtosis', 'Max Drawdown', 'Conteo de datos', 'Sharpe Ratio', 'CVaR', 'Ratio Sortino', 'Varianza']

# Diccionario que asocia los nombres de los métodos de optimización con los pesos óptimos y las estadísticas
portfolio_data = {
    'CVaR': {
        'weights': optimal_weights_cvar,
        'statistics': detailed_portfolio_statistics(optimal_weights_cvar)
    },
    'Sortino': {
        'weights': optimal_weights_sortino,
        'statistics': detailed_portfolio_statistics(optimal_weights_sortino)
    },
    'Variance': {
        'weights': optimal_weights_variance,
        'statistics': detailed_portfolio_statistics(optimal_weights_variance)
    },
    'Sharpe': {
        'weights': optimal_weights_sharpe,
        'statistics': detailed_portfolio_statistics(optimal_weights_sharpe)
    },
}

# Imprimir los pesos y las estadísticas para cada método de optimización
for method, data in portfolio_data.items():
    print("\n")
    print("========================================================================================================")
    print("\n")
    print(f"Pesos del portafolio óptimo para {method}:")
    print("\n")
    for symbol, weight in zip(symbols, data['weights']):
        if weight < 1e-4:  # considera cualquier peso menor que 0.01% como cero
            print(f"{symbol}: prácticamente 0%")
        else:
            print(f"{symbol}: {weight*100:.2f}%")

    print("\n")
    print(f"Estadísticas descriptivas del portafolio óptimo para {method}:")
    print("\n")
    # 어떤 값에만 *100을 곱할지 구분
    percent_names = ['Retorno anualizado', 'Volatilidad anualizada', 'Max Drawdown']

    for name, stat in zip(statistics_names, data['statistics']):
        if name in percent_names:
            print(f"{name}: {stat*100:.2f}%")
        else:
            print(f"{name}: {stat:.2f}")

print("\n")
print("========================================================================================================")

# 각 최적화 방법별로 포트폴리오 비중과 통계 출력 (한국어)
for method, data in portfolio_data.items():
    print("\n")
    print("========================================================================================================")
    print("\n")
    print(f"{method} 기준 최적 포트폴리오 비중:")
    print("\n")
    for symbol, weight in zip(symbols, data['weights']):
        if weight < 1e-4:  # 0.01% 미만은 0%로 간주
            print(f"{symbol}: 사실상 0%")
        else:
            print(f"{symbol}: {weight*100:.2f}%")

    print("\n")
    print(f"{method} 기준 최적 포트폴리오의 요약 통계:")
    print("\n")
    percent_names = ['연환산 수익률', '연환산 변동성', '최대 낙폭']

    # 통계 이름도 한국어로
    statistics_names_kr = [
        '연환산 수익률', '연환산 변동성', '왜도', '첨도', '최대 낙폭', '데이터 개수',
        '샤프 비율', 'CVaR', '소르티노 비율', '분산'
    ]

    for name_kr, stat in zip(statistics_names_kr, data['statistics']):
        if name_kr in percent_names:
            print(f"{name_kr}: {stat*100:.2f}%")
        else:
            print(f"{name_kr}: {stat:.2f}")

print("\n")
print("========================================================================================================")