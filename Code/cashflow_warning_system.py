import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Load and prepare data
df = pd.read_csv('data/apple_cash_flow_yearly.csv', parse_dates=['date', 'filing_date'])
df = df.sort_values('date').reset_index(drop=True)

# Calculate key metrics
df['free_cash_flow'] = df['totalCashFromOperatingActivities'] + df['capitalExpenditures']
df['working_capital_change'] = df['changeToAccountReceivables'] + df['changeToInventory'] + df['changeToLiabilities']

class CashFlowStressTester:
    def __init__(self, data):
        self.data = data.copy()
        self.scenarios = {
            'base': {'op_cash': 0, 'capex': 0, 'financing': 0},
            'mild': {'op_cash': -0.075, 'capex': -0.1, 'financing': 0.125},
            'severe': {'op_cash': -0.15, 'capex': -0.2, 'financing': 0.25}
        }
    
    def run_scenario(self, scenario_name):
        scenario = self.scenarios[scenario_name]
        temp = self.data.copy()
        
        # Apply shocks
        temp['totalCashFromOperatingActivities'] *= (1 + scenario['op_cash'])
        temp['capitalExpenditures'] *= (1 + scenario['capex'])
        # temp['totalCashFromFinancingActivities'] *= (1 + scenario['financing'])
        temp['totalCashflowsFromInvestingActivities'] *= (1 + scenario['financing']) 
        
        # Recalculate derived metrics
        temp['scenario_free_cash_flow'] = temp['totalCashFromOperatingActivities'] + temp['capitalExpenditures']
        temp['scenario_cash_balance'] = temp['endPeriodCashFlow'].iloc[0] + (
        temp['scenario_free_cash_flow'] + temp['totalCashFromFinancingActivities']).cumsum()
        
        return temp

# Initialize tester
tester = CashFlowStressTester(df)

def plot_correct_waterfall(scenario='base'):
    """Generate a properly connected waterfall chart"""
    # Step 1: Get the scenario data
    scenario_df = tester.run_scenario(scenario)
    
    # Step 2: Calculate the key components we want to show
    start_cash = scenario_df['beginPeriodCashFlow'].iloc[0]
    operating = scenario_df['totalCashFromOperatingActivities'].sum()
    investing = scenario_df['totalCashflowsFromInvestingActivities'].sum()
    financing = scenario_df['totalCashFromFinancingActivities'].sum()
    end_cash = scenario_df['endPeriodCashFlow'].iloc[-1]
    
    # Step 3: Prepare the data for plotting
    categories = ['Start', 'Operations', 'Investing', 'Financing', 'End']
    values = [start_cash, operating, investing, financing, end_cash]
    
    # Step 4: Calculate the positions for each bar
    # We'll track where each bar should start (bottom) and its height
    bottoms = []
    heights = []
    
    # Start bar
    bottoms.append(0)
    heights.append(start_cash)
    
    # Operations bar
    bottoms.append(start_cash)
    heights.append(operating)
    
    # Investing bar
    bottoms.append(start_cash + operating)
    heights.append(investing)
    
    # Financing bar
    bottoms.append(start_cash + operating + investing)
    heights.append(financing)
    
    # End bar
    # bottoms.append(0)
    # heights.append(end_cash)
    end_cash_position = start_cash + operating + investing + financing
    bottoms.append(0)  # Reset to zero for plotting
    heights.append(end_cash_position) 
    
    # Step 5: Create the figure
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Step 6: Plot each bar with proper styling
    colors = ['skyblue', 'green', 'red', 'blue', 'skyblue']
    
    for i, (category, bottom, height) in enumerate(zip(categories, bottoms, heights)):
        # Plot the bar
        bar = ax.bar(category, height, bottom=bottom, 
                    color=colors[i], edgecolor='black', width=0.6)
        
        # Add the value label
        if i == 0 or i == len(categories)-1:  # Start/End labels
            label = f'${height/1e6:,.1f}M'
            label_color = 'black'
            label_y = bottom + height/2
        else:  # Change labels
            change = height
            label = f'${change/1e6:+,.1f}M'
            label_color = 'white'
            label_y = bottom + height/2 if change > 0 else bottom + height - height*0.1
        
        ax.text(i, label_y, label,
                ha='center', va='center',
                color=label_color, weight='bold',
                bbox=dict(facecolor='black', alpha=0.3) if (i not in [0, len(categories)-1] and change < 0) else None)
    
    # Step 7: Add connecting lines
    # Calculate the y-positions for line connections
    line_points = [start_cash,
                  start_cash + operating,
                  start_cash + operating + investing,
                  start_cash + operating + investing + financing,
                  end_cash]
    
    for i in range(len(line_points)-1):
        ax.plot([i, i+1], [line_points[i], line_points[i+1]], 
                'k-', lw=1, alpha=0.5)
    
    # Step 8: Format the chart
    ax.set_title(f'Cash Flow Waterfall: {scenario.upper()} Scenario', pad=20)
    ax.set_ylabel('Amount ($ Millions)')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x/1e6:,.0f}M'))
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

# Generate the waterfall charts
plot_correct_waterfall('base')
plot_correct_waterfall('severe')

def liquidity_monitoring_dashboard(df):
    plt.figure(figsize=(16, 10))
    
    # Cash Position Trend
    ax1 = plt.subplot(2, 2, 1)
    df.plot(x='date', y='endPeriodCashFlow', ax=ax1, marker='o')
    ax1.set_title('Cash Balance Trend')
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x/1e6:,.0f}M'))
    
    # Free Cash Flow Composition
    ax2 = plt.subplot(2, 2, 2)
    components = ['totalCashFromOperatingActivities', 'capitalExpenditures', 'dividendsPaid']
    df[components].sum().plot(kind='pie', autopct='%1.1f%%', ax=ax2)
    ax2.set_title('Free Cash Flow Drivers')
    
    # Warning Indicators
    ax3 = plt.subplot(2, 2, 3)
    last_cash = df['endPeriodCashFlow'].iloc[-1]
    burn_rate = -df[df['free_cash_flow'] < 0]['free_cash_flow'].mean()
    survival = last_cash / burn_rate if burn_rate > 0 else np.inf
    
    if survival < 3:
        status = '🔴 CRISIS'
        color = 'red'
    elif survival < 6:
        status = '🟠 WARNING'
        color = 'orange'
    else:
        status = '🟢 STABLE'
        color = 'green'
    
    ax3.text(0.5, 0.6, status, fontsize=24, ha='center', color=color)
    ax3.text(0.5, 0.3, f"{survival:.1f} Months Runway", fontsize=16, ha='center')
    ax3.axis('off')
    
    # Key Metrics
    ax4 = plt.subplot(2, 2, 4)
    metrics = [
        f"Last Cash: ${last_cash/1e6:,.0f}M",
        f"Monthly Burn: ${burn_rate/1e6:,.0f}M",
        f"Working Capital Change: ${df['working_capital_change'].sum()/1e6:,.0f}M",
        f"Financing Gap: ${df['netBorrowings'].sum()/1e6:,.0f}M"
    ]
    ax4.text(0.1, 0.8, "\n".join(metrics), fontsize=12)
    ax4.axis('off')
    
    plt.tight_layout()
    plt.show()

liquidity_monitoring_dashboard(df)