import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load your dataset
df = pd.read_csv('data/apple_cash_flow_yearly.csv')

# Convert date columns to datetime
df['date'] = pd.to_datetime(df['date'])
df['filing_date'] = pd.to_datetime(df['filing_date'])

# Check for missing values
print(df.isnull().sum())

# Current ratio equivalent for cash flow
df['cash_flow_coverage'] = (df['totalCashFromOperatingActivities'] / 
                           abs(df['dividendsPaid'] + df['capitalExpenditures']))

# Cash conversion cycle (simplified)
df['cash_conversion_cycle'] = (df['changeToAccountReceivables'] + 
                              df['changeToInventory'] - 
                              df['changeToLiabilities'])

# Scenario 1: 20% reduction in operating cash flow
df['stress_operating_cash'] = df['totalCashFromOperatingActivities'] * 0.8
print(df['stress_operating_cash'])

# Scenario 2: 30% increase in capital expenditures
df['stress_capex'] = df['capitalExpenditures'] * 1.3
print(df['stress_capex'])

# Scenario 3: Combined stress scenario
df['combined_stress'] = (df['stress_operating_cash'] - 
                        df['stress_capex'] - 
                        df['dividendsPaid'])
print(df['combined_stress'])

# Calculate free cash flow (as defined in your fields)
df['calculated_free_cash_flow'] = df['freeCashFlow']

# Alternative FCF calculation if needed
df['alt_free_cash_flow'] = (df['totalCashFromOperatingActivities'] - 
                           df['capitalExpenditures'])

# Months of cash runway
df['cash_runway_months'] = (df['endPeriodCashFlow'] / 
                           (abs(df['calculated_free_cash_flow']) / 12))

plt.figure(figsize=(18, 6))

# First subplot - Line plot (works fine)
ax1 = plt.subplot(1, 2, 1)
df.plot(x='date', 
        y=['totalCashFromOperatingActivities', 
           'totalCashflowsFromInvestingActivities',
           'totalCashFromFinancingActivities'],
        kind='line', ax=ax1)
ax1.set_title('Cash Flow Trends')
ax1.set_ylabel('Amount')

# Second subplot - Properly formatted bar plot
ax2 = plt.subplot(1, 2, 2)

# Convert dates to numeric values first
dates = mdates.date2num(df['date'])
width = 0.4 * (dates[1] - dates[0])  # Dynamic width based on date spacing

# Plot bars using numeric dates
bars1 = ax2.bar(dates - width/2, df['calculated_free_cash_flow'], 
                width, label='Free Cash Flow')
bars2 = ax2.bar(dates + width/2, df['combined_stress'], 
                width, label='Stress Scenario')

# Format x-axis properly
ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax2.set_title('Free Cash Flow vs Stress Scenario')
ax2.legend()

# Rotate dates for readability
plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.show()

# Create sensitivity matrix
def cash_flow_sensitivity(operating_change, capex_change):
    return (df['totalCashFromOperatingActivities'] * (1 + operating_change) - 
           df['capitalExpenditures'] * (1 + capex_change) - 
           df['dividendsPaid'])

# Example sensitivity scenarios
scenarios = [
    (-0.1, 0.1),   # 10% worse operating, 10% higher capex
    (-0.2, 0.2),   # 20% worse operating, 20% higher capex
    (-0.3, 0.3)    # 30% worse operating, 30% higher capex
]

for i, (op_change, capex_change) in enumerate(scenarios, 1):
    df[f'scenario_{i}_result'] = cash_flow_sensitivity(op_change, capex_change)

pressure_test_results = {
    'worst_case_cash_position': df['combined_stress'].min(),
    'months_of_worst_case_runway': df['cash_runway_months'].min(),
    'sensitivity_to_operating_cash': (df['totalCashFromOperatingActivities'].mean() * 0.2),
    'sensitivity_to_capex': (df['capitalExpenditures'].mean() * 0.2),
    'free_cash_flow_volatility': df['calculated_free_cash_flow'].std()
}

print(pressure_test_results)

# Calculate required actions (example calculations)
required_cash_buffer = abs(df['combined_stress'].min()) * 6  # 6 months coverage
current_cash = df['endPeriodCashFlow'].mean()
additional_liquidity_needed = max(0, required_cash_buffer - current_cash)

print(f"Additional liquidity needed: ${additional_liquidity_needed:,.2f}")

# Example improvement scenario modeling
df['improved_scenario'] = (df['totalCashFromOperatingActivities'] * 1.1 * 0.9  # 10% better collections, 10% lower costs
                         - df['capitalExpenditures'] * 0.7  # 30% capex reduction
                         - df['dividendsPaid'] * 0.5)  # 50% dividend cut