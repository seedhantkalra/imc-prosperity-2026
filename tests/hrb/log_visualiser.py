
# ============================================================
# CONFIGURATION
# ============================================================
LOG_PATH = "/content/drive/MyDrive/Prosperity/logs/(insert.log)"
TICKS_PER_DAY = 10000

COLORS = ["#34d399", "#a78bfa", "#fb923c", "#f472b6", "#38bdf8", "#facc15"]

def load_and_parse_log(filepath):
    """Parses the Prosperity JSON log into a usable Pandas DataFrame and extracts trades."""
    print(f"Loading log from: {filepath}...")
    with open(filepath, 'r') as f:
        log_data = json.load(f)

    activities_csv = log_data.get("activitiesLog", "")
    if not activities_csv:
        raise ValueError("No activitiesLog found in the file. Check if the backtest completed successfully.")

    # Read the embedded CSV
    df = pd.read_csv(io.StringIO(activities_csv), sep=";")

    # Clean and cast columns
    df['timestamp'] = df['timestamp'].astype(int)
    df['profit_and_loss'] = df['profit_and_loss'].fillna(0).astype(float)
    
    # Extract order book pricing if available
    if 'bid_price_1' in df.columns and 'ask_price_1' in df.columns:
        df['bid_price_1'] = df['bid_price_1'].astype(float)
        df['ask_price_1'] = df['ask_price_1'].astype(float)
        df['mid_price'] = (df['bid_price_1'] + df['ask_price_1']) / 2.0

    # Extract trades
    trades_list = log_data.get("tradeHistory", [])

    return df, trades_list

# --- 1. Load Data ---
df, trades_list = load_and_parse_log(LOG_PATH)
products = [p for p in df['product'].dropna().unique() if p != '']

# --- 2. Build PnL Pivot Table ---
pnl_pivot = df.pivot(index='timestamp', columns='product', values='profit_and_loss')
pnl_pivot = pnl_pivot.ffill().fillna(0)
pnl_pivot['TOTAL'] = pnl_pivot.sum(axis=1)

# --- 3. Process Trade History for Visuals & Turnover ---
turnover_dict = {p: 0 for p in products}
total_turnover = 0
our_trades = []

for trade in trades_list:
    is_buyer = trade.get('buyer') == "SUBMISSION"
    is_seller = trade.get('seller') == "SUBMISSION"
    
    if is_buyer or is_seller:
        sym = trade.get('symbol')
        qty = abs(trade.get('quantity', 0))
        price = trade.get('price', 0)
        ts = trade.get('timestamp', 0)
        
        turnover_dict[sym] += qty
        total_turnover += qty
        
        our_trades.append({
            'timestamp': ts,
            'product': sym,
            'price': price,
            'quantity': qty,
            'side': 'BUY' if is_buyer else 'SELL'
        })

df_trades = pd.DataFrame(our_trades)

# --- 4. Generate Summary Table ---
print("\n" + "="*85)
print("🏆 INSTITUTIONAL PNL & RISK DASHBOARD")
print("="*85)
print(f"{'PRODUCT':<12} | {'FINAL PNL':>10} | {'MAX DD':>8} | {'SHARPE':>8} | {'CALMAR':>8} | {'TURNOVER (Vol)':>14}")
print("-" * 85)

total_pnl = pnl_pivot['TOTAL'].iloc[-1]
total_rolling_max = pnl_pivot['TOTAL'].cummax()
total_drawdown = (total_rolling_max - pnl_pivot['TOTAL']).max()
total_diff = pnl_pivot['TOTAL'].diff().fillna(0)
total_sharpe = (total_diff.mean() / total_diff.std()) * np.sqrt(TICKS_PER_DAY) if total_diff.std() != 0 else 0.0
total_calmar = total_pnl / total_drawdown if total_drawdown > 0 else float('inf')

for p in products:
    final_pnl = pnl_pivot[p].iloc[-1]
    rolling_max = pnl_pivot[p].cummax()
    max_dd = (rolling_max - pnl_pivot[p]).max()
    pnl_diff = pnl_pivot[p].diff().fillna(0)
    std_dev = pnl_diff.std()
    sharpe = (pnl_diff.mean() / std_dev) * np.sqrt(TICKS_PER_DAY) if std_dev != 0 else 0.0
    calmar = (final_pnl / max_dd) if max_dd > 0 else float('inf')
    turnover = turnover_dict.get(p, 0)
    calmar_str = f"{calmar:>8.2f}" if calmar != float('inf') else f"{'INF':>8}"
    print(f"{p:<12} | {final_pnl:>10,.0f} | {-max_dd:>8,.0f} | {sharpe:>8.2f} | {calmar_str} | {turnover:>14,.0f}")

print("-" * 85)
total_calmar_str = f"{total_calmar:>8.2f}" if total_calmar != float('inf') else f"{'INF':>8}"
print(f"{'TOTAL PORT.':<12} | {total_pnl:>10,.0f} | {-total_drawdown:>8,.0f} | {total_sharpe:>8.2f} | {total_calmar_str} | {total_turnover:>14,.0f}")
print("="*85 + "\n")

# --- 5. Plotly Chart 1: Combined PnL Over Time ---
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=pnl_pivot.index, y=pnl_pivot['TOTAL'], mode='lines', name='Total PnL', line=dict(width=3, color='#22d3ee')))
for i, product in enumerate(products):
    fig1.add_trace(go.Scatter(x=pnl_pivot.index, y=pnl_pivot[product], mode='lines', name=product, line=dict(dash='dash', width=1.5, color=COLORS[i % len(COLORS)])))
fig1.add_hline(y=0, line_dash="dot", line_color="#555")
fig1.update_layout(title="Combined Portfolio Performance (Equity Curve)", template="plotly_dark", hovermode="x unified", xaxis_title="Timestamp", yaxis_title="Profit & Loss", height=500)

# --- 6. Plotly Chart 2: Per-Product Subplots (Area Fill) ---
fig2 = make_subplots(rows=len(products), cols=1, shared_xaxes=True, subplot_titles=[f"{p} Performance" for p in products], vertical_spacing=0.08)
for i, p in enumerate(products):
    color = COLORS[i % len(COLORS)]
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fill_color = f"rgba({r},{g},{b},0.1)"
    fig2.add_trace(go.Scatter(x=pnl_pivot.index, y=pnl_pivot[p], name=p, fill="tozeroy", line=dict(color=color, width=2), fillcolor=fill_color), row=i+1, col=1)
    fig2.add_hline(y=0, line_dash="dot", line_color="#555", row=i+1, col=1)
fig2.update_layout(title="Individual Asset Growth & Drawdown Visualizer", template="plotly_dark", hovermode="x unified", height=300 * len(products), showlegend=False)

# --- 7. Plotly Chart 3: Microstructure Execution Map ---
# This plots the spread channel and maps our exact trade executions on top of it.
fig3 = make_subplots(rows=len(products), cols=1, shared_xaxes=True, subplot_titles=[f"{p} Execution Map (Bid/Ask Spread vs Trades)" for p in products], vertical_spacing=0.1)

for i, p in enumerate(products):
    df_prod = df[df['product'] == p].sort_values('timestamp')
    
    if 'bid_price_1' in df_prod.columns and 'ask_price_1' in df_prod.columns:
        # Plot the Ask Line (Top of Spread)
        fig3.add_trace(go.Scatter(
            x=df_prod['timestamp'], y=df_prod['ask_price_1'],
            mode='lines', line=dict(width=1, color='rgba(239, 68, 68, 0.5)'), name=f'{p} Best Ask', showlegend=False
        ), row=i+1, col=1)
        
        # Plot the Bid Line (Bottom of Spread)
        fig3.add_trace(go.Scatter(
            x=df_prod['timestamp'], y=df_prod['bid_price_1'],
            mode='lines', line=dict(width=1, color='rgba(16, 185, 129, 0.5)'), fill='tonexty', fillcolor='rgba(255, 255, 255, 0.05)', name=f'{p} Best Bid', showlegend=False
        ), row=i+1, col=1)
        
    # Overlay Trades
    if not df_trades.empty:
        prod_trades = df_trades[df_trades['product'] == p]
        
        buys = prod_trades[prod_trades['side'] == 'BUY']
        if not buys.empty:
            fig3.add_trace(go.Scatter(
                x=buys['timestamp'], y=buys['price'],
                mode='markers', marker=dict(symbol='triangle-up', size=8, color='#10b981', line=dict(width=1, color='white')),
                name=f'{p} BUYS', text=buys['quantity'], hovertemplate="Price: %{y}<br>Vol: %{text}"
            ), row=i+1, col=1)
            
        sells = prod_trades[prod_trades['side'] == 'SELL']
        if not sells.empty:
            fig3.add_trace(go.Scatter(
                x=sells['timestamp'], y=sells['price'],
                mode='markers', marker=dict(symbol='triangle-down', size=8, color='#ef4444', line=dict(width=1, color='white')),
                name=f'{p} SELLS', text=sells['quantity'], hovertemplate="Price: %{y}<br>Vol: %{text}"
            ), row=i+1, col=1)

fig3.update_layout(title="Microstructure Execution Map (Zoom in to see trade placement)", template="plotly_dark", hovermode="x unified", height=400 * len(products))

# Render all
fig1.show()
fig2.show()
fig3.show()
