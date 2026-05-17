labels = []
            else:
                true_labels, qber_scores, predicted_labels = [], [], []
            
            if true_labels and qber_scores:
                st.plotly_chart(
                    plot_eve_roc_curve(true_labels, qber_scores),
                    use_container_width=True
                )
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.plotly_chart(
                        plot_eve_confusion_matrix(true_labels, predicted_labels),
                        use_container_width=True
                    )
                
                with col_b:
                    st.plotly_chart(
                        plot_detection_threshold_analysis(true_labels, qber_scores),
                        use_container_width=True
                    )
        
        st.divider()
    
    # Summary metrics
    st.header("📊 Summary")
    
    if use_mock_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Avg Latency (Vectorised)",
                "125.3 ms",
                "-15.2%",
                help="Average latency for vectorised simulation"
            )
        
        with col2:
            st.metric(
                "Cache Hit Rate",
                "85.0%",
                "+5.2%",
                help="Percentage of cache hits"
            )
        
        with col3:
            st.metric(
                "Avg QBER (Clean)",
                "0.048",
                "-0.003",
                help="Average QBER without Eve"
            )
        
        with col4:
            st.metric(
                "Eve Detection Rate",
                "94.5%",
                "+2.1%",
                help="True positive rate for Eve detection"
            )
    
    # Export options
    with st.expander("💾 Export Options"):
        st.markdown("""
        **Available Export Formats:**
        - PNG: Static image export (right-click on any chart)
        - HTML: Interactive chart export (use Plotly's download button)
        - CSV: Raw data export (coming soon)
        """)
        
        if st.button("📥 Download All Charts as HTML"):
            st.info("Feature coming soon: Bundle all charts into a single HTML report")


# Helper function for integration
def add_charts_tab_to_app():
    """
    Add the Charts & Graphs tab to the main Streamlit app.
    
    Usage in app/streamlit_app.py:
    
    ```python
    from charts.dashboard import add_charts_tab_to_app
    
    # In your tab creation section:
    tab_charts = st.tabs(["...", "📈 Charts & Graphs", "..."])
    
    with tab_charts:
        add_charts_tab_to_app()
    ```
    """
    render_charts_dashboard()
```

---

## Integration Instructions

### Step 1: Create the `charts/` directory

```bash
mkdir -p cryptolab-bb84/charts
```

### Step 2: Copy all files

Copy each of the code blocks above into their respective files:
- `charts/__init__.py`
- `charts/latency_charts.py`
- `charts/qber_trends.py`
- `charts/caching_impact.py`
- `charts/eve_roc.py`
- `charts/mock_data.py`
- `charts/dashboard.py`

### Step 3: Update `app/streamlit_app.py`

Add the new tab to your existing Streamlit app:

```python
# At the top, add import
from charts.dashboard import render_charts_dashboard

# In your tab creation section, add:
tab1, tab2, tab3, tab4, tab5, tab6, tab_charts = st.tabs([
    "🎮 Playground",
    "📚 Step-by-Step",
    "🕵️ Eve Mode",
    "📊 Security Analytics",
    "🤖 Bob Copilot",
    "🔧 Builder Notes",
    "📈 Charts & Graphs"  # NEW TAB
])

# Add the charts tab content:
with tab_charts:
    render_charts_dashboard()
```

### Step 4: Install dependencies (if needed)

```bash
pip install plotly scikit-learn
```

### Step 5: Test the charts

```bash
streamlit run app/streamlit_app.py
```

Navigate to the "📈 Charts & Graphs" tab and interact with the visualizations.

---

## Features Summary

✅ **Performance Benchmarks**
- Latency vs qubits (log-log scale)
- Speedup comparison bar chart
- Latency heatmap

✅ **QBER Analysis**
- Time-series trend with moving average
- Anomaly detection and highlighting
- QBER distribution histogram
- Scenario comparison box plots

✅ **Caching Impact**
- Cold vs warm run comparison
- Cache hit rate pie chart
- Speedup metrics

✅ **Eve Detection**
- ROC curve with AUC
- Confusion matrix with metrics
- Threshold analysis
- Optimal threshold identification

✅ **Interactive Features**
- Plotly hover tooltips
- Zoom and pan
- Responsive layout
- Mock data for demonstration
- Sidebar controls

---

## Next Steps

1. **Real Data Integration**: Replace mock data generators with actual performance collectors
2. **Export Functionality**: Add CSV/PDF export for charts
3. **Real-time Updates**: Stream live data to charts during simulations
4. **Custom Metrics**: Add user-defined performance metrics
5. **Comparison Mode**: Compare multiple simulation runs side-by-side

This charts module provides professional-grade visualizations that will impress hackathon judges and help users understand the BB84 system's performance characteristics at a glance.