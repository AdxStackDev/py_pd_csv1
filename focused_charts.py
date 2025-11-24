# ====================================================
# 📈 Focused Chart Generation (Compare Page)
# ====================================================
def generate_focused_charts(current_date: datetime.date):
    """Generate 6 focused charts for the compare page."""
    
    # Fetch current and previous day data
    data_map = fetch_last_n_days_data(current_date, n=5)
    sorted_dates = sorted(data_map.keys())
    
    if len(sorted_dates) < 1:
        raise Exception("Not enough data available.")
        
    today_df = data_map[sorted_dates[-1]].copy()
    today_df = calculate_net_sentiment(today_df)
    
    prev_df = data_map[sorted_dates[-2]].copy() if len(sorted_dates) >= 2 else today_df
    
    # Common Layout Settings
    layout_args = dict(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font=dict(color="#e2e8f0", size=12),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    charts = {}
    
    # ============================================
    # 1. NSE Participant Data Overview Table
    # ============================================
    def get_value(df, client, col):
        row = df[df["Client Type"] == client]
        if row.empty: return 0
        return int(row[col].values[0])
    
    table_data = []
    segments = [
        ("Index Long", "Future Index Long"),
        ("Index Short", "Future Index Short"),
        ("Stock Long", "Future Stock Long"),
        ("Stock Short", "Future Stock Short")
    ]
    
    for participant in ["FII", "DII", "PRO", "CLIENT"]:
        for segment_name, col_name in segments:
            current_val = get_value(today_df, participant, col_name)
            prev_val = get_value(prev_df, participant, col_name)
            net_change = current_val - prev_val
            
            # Determine position type
            if "Long" in segment_name:
                position = "Long Heavy" if net_change > 0 else "Short Heavy"
            else:
                position = "Short Heavy" if net_change > 0 else "Long Heavy"
            
            table_data.append({
                "Participant": participant,
                "Segment": segment_name,
                "Net Change": net_change,
                "Current OI": current_val,
                "Position": position,
                "Previous OI": prev_val
            })
    
    table_df = pd.DataFrame(table_data)
    
    # Color cells based on net change
    def get_color(val):
        if val > 0:
            return '#10b981'  # Green
        elif val < 0:
            return '#ef4444'  # Red
        return '#94a3b8'  # Gray
    
    cell_colors = [[get_color(v) if isinstance(v, (int, float)) else '#1e293b' for v in table_df["Net Change"]]]
    
    fig_table = go.Figure(data=[go.Table(
        header=dict(
            values=["Participant", "Segment", "Net Change", "Current OI", "Position", "Previous OI"],
            fill_color='#1e293b',
            align='center',
            font=dict(color='#e2e8f0', size=14, family='Arial Black'),
            height=40
        ),
        cells=dict(
            values=[table_df["Participant"], table_df["Segment"], table_df["Net Change"], 
                   table_df["Current OI"], table_df["Position"], table_df["Previous OI"]],
            fill_color=[['#0f172a']*len(table_df), ['#0f172a']*len(table_df), cell_colors[0],
                       ['#0f172a']*len(table_df), ['#0f172a']*len(table_df), ['#0f172a']*len(table_df)],
            align='center',
            font=dict(color='#e2e8f0', size=12),
            height=30
        )
    )])
    
    fig_table.update_layout(
        title=dict(text="NSE Participant Data Overview", font=dict(size=20, color='#3b82f6')),
        **layout_args,
        height=750
    )
    fig_table.write_html(os.path.join(STATIC_DIR, "overview_table.html"), include_plotlyjs='cdn', full_html=False)
    charts['overview_table'] = "overview_table.html"
    
    # ============================================
    # 2. Nifty 50 vs FII Futures Sentiment
    # ============================================
    # Create simulated Nifty 50 data (placeholder - replace with actual data source)
    nifty_data = []
    fii_short_pct = []
    dates = []
    
    for d in sorted_dates:
        day_df = data_map[d]
        fii_row = day_df[day_df["Client Type"] == "FII"]
        if not fii_row.empty:
            longs = fii_row["Future Index Long"].values[0]
            shorts = fii_row["Future Index Short"].values[0]
            total = longs + shorts
            short_pct = (shorts / total * 100) if total > 0 else 50
            
            dates.append(d)
            nifty_data.append(25000 + len(dates) * 100)  # Simulated
            fii_short_pct.append(short_pct)
    
    fig_nifty = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_nifty.add_trace(
        go.Scatter(x=dates, y=nifty_data, name="Nifty 50", line=dict(color='#3b82f6', width=3)),
        secondary_y=False
    )
    
    fig_nifty.add_trace(
        go.Scatter(x=dates, y=fii_short_pct, name="FII Short %", 
                  fill='tozeroy', line=dict(color='#10b981', width=2)),
        secondary_y=True
    )
    
    fig_nifty.update_xaxes(title_text="Date", color='#e2e8f0')
    fig_nifty.update_yaxes(title_text="Nifty 50 Index", secondary_y=False, color='#3b82f6')
    fig_nifty.update_yaxes(title_text="FII Short %", secondary_y=True, color='#10b981')
    
    fig_nifty.update_layout(
        title=dict(text="Nifty 50 vs FII Futures Sentiment", font=dict(size=20, color='#3b82f6')),
        **layout_args,
        height=500,
        hovermode='x unified'
    )
    fig_nifty.write_html(os.path.join(STATIC_DIR, "nifty_sentiment.html"), include_plotlyjs='cdn', full_html=False)
    charts['nifty_sentiment'] = "nifty_sentiment.html"
    
    # ============================================
    # 3. Participant Net Options Analysis
    # ============================================
    participants = ["FII", "DII", "PRO", "CLIENT"]
    
    fig_options = make_subplots(
        rows=2, cols=2,
        subplot_titles=participants,
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    
    for i, participant in enumerate(participants):
        row, col = positions[i]
        p_data = today_df[today_df["Client Type"] == participant]
        
        if not p_data.empty:
            net_index_calls = get_value(today_df, participant, "Call Diff")
            net_index_puts = get_value(today_df, participant, "Put Diff")
            
            fig_options.add_trace(
                go.Bar(x=["Net Calls", "Net Puts"], 
                      y=[net_index_calls, net_index_puts],
                      marker_color=['#10b981' if net_index_calls >= 0 else '#ef4444',
                                   '#10b981' if net_index_puts >= 0 else '#ef4444'],
                      showlegend=False),
                row=row, col=col
            )
    
    fig_options.update_layout(
        title=dict(text="Participant Net Options Analysis", font=dict(size=20, color='#3b82f6')),
        **layout_args,
        height=650
    )
    fig_options.write_html(os.path.join(STATIC_DIR, "options_analysis.html"), include_plotlyjs='cdn', full_html=False)
    charts['options_analysis'] = "options_analysis.html"
    
    # ============================================
    # 4. Futures Positioning Data (for cards)
    # ============================================
    futures_data = []
    
    for participant in participants:
        index_long = get_value(today_df, participant, "Future Index Long")
        index_short = get_value(today_df, participant, "Future Index Short")
        stock_long = get_value(today_df, participant, "Future Stock Long")
        stock_short = get_value(today_df, participant, "Future Stock Short")
        
        index_prev_long = get_value(prev_df, participant, "Future Index Long")
        index_prev_short = get_value(prev_df, participant, "Future Index Short")
        stock_prev_long = get_value(prev_df, participant, "Future Stock Long")
        stock_prev_short = get_value(prev_df, participant, "Future Stock Short")
        
        index_total = index_long + index_short
        stock_total = stock_long + stock_short
        
        futures_data.append({
            "participant": participant,
            "index_futures": {
                "longs": index_long,
                "shorts": index_short,
                "long_pct": round((index_long / index_total * 100) if index_total > 0 else 50, 1),
                "short_pct": round((index_short / index_total * 100) if index_total > 0 else 50, 1),
                "net_change": (index_long - index_short) - (index_prev_long - index_prev_short)
            },
            "stock_futures": {
                "longs": stock_long,
                "shorts": stock_short,
                "long_pct": round((stock_long / stock_total * 100) if stock_total > 0 else 50, 1),
                "short_pct": round((stock_short / stock_total * 100) if stock_total > 0 else 50, 1),
                "net_change": (stock_long - stock_short) - (stock_prev_long - stock_prev_short)
            }
        })
    
    charts['futures_data'] = futures_data
    
    # ============================================
    # 5. Call-Put Difference (Sentiment) - Horizontal Bar
    # ============================================
    sentiment_data = []
    for participant in participants:
        net_sentiment = get_value(today_df, participant, "Net Sentiment")
        sentiment_data.append({"participant": participant, "sentiment": net_sentiment})
    
    sentiment_df = pd.DataFrame(sentiment_data)
    
    fig_sentiment = go.Figure(go.Bar(
        x=sentiment_df["sentiment"],
        y=sentiment_df["participant"],
        orientation='h',
        marker=dict(
            color=sentiment_df["sentiment"],
            colorscale=[[0, '#ef4444'], [0.5, '#94a3b8'], [1, '#10b981']],
            line=dict(color='#1e293b', width=2)
        ),
        text=sentiment_df["sentiment"],
        textposition='auto'
    ))
    
    fig_sentiment.add_vline(x=0, line_dash="dash", line_color='#94a3b8', line_width=2)
    
    fig_sentiment.update_layout(
        title=dict(text="Call-Put Difference (Sentiment)", font=dict(size=20, color='#3b82f6')),
        xaxis_title="Net Sentiment (Call Diff - Put Diff)",
        yaxis_title="Participant",
        **layout_args,
        height=450
    )
    fig_sentiment.write_html(os.path.join(STATIC_DIR, "sentiment_hbar.html"), include_plotlyjs='cdn', full_html=False)
    charts['sentiment_hbar'] = "sentiment_hbar.html"
    
    # ============================================
    # 6. Position Intensity Heatmap
    # ============================================
    heatmap_data = today_df.set_index("Client Type")[["Future Index Long", "Future Index Short", 
                                                        "Option Index Call Long", "Option Index Put Long"]]
    
    fig_heat = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Viridis',
        text=heatmap_data.values,
        texttemplate='%{text:,.0f}',
        textfont={"size": 12},
        colorbar=dict(title="OI Value")
    ))
    
    fig_heat.update_layout(
        title=dict(text="Position Intensity Heatmap", font=dict(size=20, color='#3b82f6')),
        **layout_args,
        height=500
    )
    fig_heat.write_html(os.path.join(STATIC_DIR, "position_heat.html"), include_plotlyjs='cdn', full_html=False)
    charts['position_heat'] = "position_heat.html"
    
    return charts

