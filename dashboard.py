import streamlit as st
import pandas as pd
import os
import glob
import re
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Search Console Keyword Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Search Console Keyword Dashboard")
st.markdown("**Top Keywords by Search Volume (Positions 1-10)**")

# Extract date from filename
def extract_date_from_filename(filename):
    """Extract date from filename patterns like '2025-11-14' or '20251114'"""
    # Try YYYY-MM-DD pattern
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if date_match:
        try:
            return datetime.strptime(date_match.group(0), '%Y-%m-%d').date()
        except:
            pass
    
    # Try YYYYMMDD pattern
    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if date_match:
        try:
            return datetime.strptime(date_match.group(0), '%Y%m%d').date()
        except:
            pass
    
    # Try to get file modification date as fallback
    try:
        if os.path.exists(filename):
            return datetime.fromtimestamp(os.path.getmtime(filename)).date()
    except:
        pass
    
    return None

# Function to process Excel file
def process_search_console_file(file_path, include_date=None):
    """Process Search Console Excel file and return filtered data"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Common column name variations in Search Console exports
        position_col = None
        impressions_col = None
        clicks_col = None
        ctr_col = None
        keyword_col = None
        
        # Find columns (case-insensitive)
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'position' in col_lower or 'avg. position' in col_lower or 'avg position' in col_lower:
                position_col = col
            if 'impressions' in col_lower:
                impressions_col = col
            if 'clicks' in col_lower:
                clicks_col = col
            if 'ctr' in col_lower or 'click-through rate' in col_lower:
                ctr_col = col
            if ('query' in col_lower or 'queries' in col_lower or 
                'keyword' in col_lower or 'keywords' in col_lower or 
                'search query' in col_lower or 'top query' in col_lower or
                'top queries' in col_lower):
                keyword_col = col
        
        if position_col is None:
            st.error(f"Could not find 'Position' column in file. Available columns: {list(df.columns)}")
            return None
        
        if impressions_col is None:
            st.warning("Could not find 'Impressions' column. Using clicks as search volume metric.")
            impressions_col = clicks_col
        
        if keyword_col is None:
            st.error(f"Could not find 'Query' or 'Keyword' column. Available columns: {list(df.columns)}")
            return None
        
        # Filter for positions 1-10
        df_filtered = df[df[position_col].between(1, 10)].copy()
        
        if df_filtered.empty:
            st.warning("No keywords found in positions 1-10.")
            return None
        
        # Calculate CTR if not present but we have clicks and impressions
        if ctr_col is None and clicks_col and impressions_col:
            df_filtered['CTR'] = (df_filtered[clicks_col] / df_filtered[impressions_col] * 100).round(2)
            ctr_col = 'CTR'
        
        # Select relevant columns for display
        display_cols = [keyword_col, position_col, impressions_col]
        if clicks_col:
            display_cols.append(clicks_col)
        if ctr_col:
            display_cols.append(ctr_col)
        
        # Add any other numeric columns that might be useful
        for col in df.columns:
            if col not in display_cols and df[col].dtype in ['int64', 'float64']:
                if col not in [position_col, impressions_col, clicks_col, ctr_col]:
                    display_cols.append(col)
        
        result_df = df_filtered[display_cols].copy()
        
        # Rename columns for better display
        column_mapping = {
            keyword_col: 'Keyword',
            position_col: 'Avg Position',
            impressions_col: 'Impressions',
            clicks_col: 'Clicks' if clicks_col else None,
            ctr_col: 'CTR' if ctr_col else None
        }
        column_mapping = {k: v for k, v in column_mapping.items() if v is not None}
        result_df = result_df.rename(columns=column_mapping)
        
        # Ensure CTR is formatted as percentage if it exists
        if 'CTR' in result_df.columns:
            # If CTR is already a percentage (0-100), keep it; if it's decimal (0-1), convert
            if result_df['CTR'].max() <= 1:
                result_df['CTR'] = result_df['CTR'] * 100
        
        # Add date column if provided
        if include_date:
            result_df['Date'] = include_date
            full_df = df_filtered.copy()
            full_df['Date'] = include_date
        else:
            full_df = df_filtered.copy()
        
        return result_df, full_df
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

# Function to load all historical data
def load_all_historical_data():
    """Load and process all Excel files in the directory"""
    all_files = glob.glob("*.xlsx") + glob.glob("*.xls")
    
    if not all_files:
        return None
    
    historical_data = []
    file_dates = []
    
    for file_path in sorted(all_files):
        date = extract_date_from_filename(file_path)
        result = process_search_console_file(file_path, include_date=date)
        
        if result:
            result_df, _ = result
            historical_data.append(result_df)
            file_dates.append((file_path, date))
    
    if not historical_data:
        return None
    
    # Combine all data
    combined_df = pd.concat(historical_data, ignore_index=True)
    
    return combined_df, file_dates

# Function to get keyword opportunities
def get_keyword_opportunities(df):
    """Identify keyword opportunities"""
    opportunities = {}
    
    # High impressions, low clicks (optimization opportunities)
    if 'Impressions' in df.columns and 'Clicks' in df.columns:
        high_imp_low_clicks = df[
            (df['Impressions'] > df['Impressions'].quantile(0.75)) & 
            (df['Clicks'] < df['Clicks'].quantile(0.5))
        ].copy()
        if not high_imp_low_clicks.empty:
            opportunities['High Impressions, Low Clicks'] = high_imp_low_clicks.sort_values('Impressions', ascending=False)
    
    # Position 4-6 (quick wins to push to top 3)
    if 'Avg Position' in df.columns:
        quick_wins = df[df['Avg Position'].between(4, 6)].copy()
        if not quick_wins.empty:
            opportunities['Quick Wins (Position 4-6)'] = quick_wins.sort_values('Impressions', ascending=False)
    
    # High CTR keywords (what's working well)
    if 'CTR' in df.columns:
        high_ctr = df[df['CTR'] > df['CTR'].quantile(0.75)].copy()
        if not high_ctr.empty:
            opportunities['High CTR Keywords'] = high_ctr.sort_values('CTR', ascending=False)
    
    return opportunities

# Function to get historical insights
def get_historical_insights(combined_df, file_dates):
    """Get insights from historical data"""
    if 'Date' not in combined_df.columns or len(file_dates) < 2:
        return None
    
    insights = {}
    
    # Get latest and previous dates
    dates = sorted([d for _, d in file_dates if d is not None])
    if len(dates) < 2:
        return None
    
    latest_date = dates[-1]
    previous_date = dates[-2]
    
    latest_df = combined_df[combined_df['Date'] == latest_date].copy()
    previous_df = combined_df[combined_df['Date'] == previous_date].copy()
    
    # Biggest position movers (improved)
    latest_keywords = latest_df.set_index('Keyword')
    previous_keywords = previous_df.set_index('Keyword')
    
    merged = latest_keywords.join(previous_keywords, rsuffix='_prev', how='outer')
    
    if 'Avg Position' in merged.columns and 'Avg Position_prev' in merged.columns:
        merged['Position Change'] = merged['Avg Position_prev'].fillna(merged['Avg Position']) - merged['Avg Position']
        
        # Biggest improvements
        improvements = merged[merged['Position Change'] > 0].copy()
        if not improvements.empty:
            insights['Biggest Position Improvements'] = improvements.nlargest(20, 'Position Change')
        
        # Biggest declines
        declines = merged[merged['Position Change'] < 0].copy()
        if not declines.empty:
            insights['Biggest Position Declines'] = declines.nsmallest(20, 'Position Change')
    
    # New keywords (in latest but not in previous)
    new_keywords = latest_df[~latest_df['Keyword'].isin(previous_df['Keyword'])].copy()
    if not new_keywords.empty:
        insights['New Keywords'] = new_keywords.sort_values('Impressions', ascending=False)
    
    # Dropped keywords (in previous but not in latest)
    dropped_keywords = previous_df[~previous_df['Keyword'].isin(latest_df['Keyword'])].copy()
    if not dropped_keywords.empty:
        insights['Dropped Keywords'] = dropped_keywords.sort_values('Impressions', ascending=False)
    
    return insights, latest_date, previous_date

# Sidebar for view selection
st.sidebar.header("📊 View Mode")

view_mode = st.sidebar.radio(
    "Choose view:",
    ["Single File", "Historical Comparison"],
    help="Single File: View one file at a time | Historical: Compare all files over time"
)

# Sidebar for file selection
st.sidebar.header("📁 File Selection")

# Option 1: Upload new file
uploaded_file = st.sidebar.file_uploader(
    "Upload Search Console Excel file",
    type=['xlsx', 'xls'],
    help="Upload a new Search Console export file"
)

# Option 2: Select from existing files
existing_files = glob.glob("*.xlsx") + glob.glob("*.xls")
if existing_files:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Or select existing file:")
    selected_file = st.sidebar.selectbox(
        "Choose a file",
        options=existing_files,
        index=0 if existing_files else None
    )
else:
    selected_file = None

# Determine which file to process
file_to_process = None
file_name = None

if uploaded_file is not None:
    file_to_process = uploaded_file
    file_name = uploaded_file.name
    st.sidebar.success(f"📄 Processing: {file_name}")
elif selected_file:
    file_to_process = selected_file
    file_name = selected_file
    st.sidebar.info(f"📄 Selected: {file_name}")

# Process based on view mode
if view_mode == "Historical Comparison":
    # Historical view
    with st.spinner("Loading historical data..."):
        historical_result = load_all_historical_data()
    
    if historical_result is not None:
        combined_df, file_dates = historical_result
        
        st.subheader("📈 Historical Keyword Analysis")
        
        # Show available dates
        if file_dates:
            dates_info = ", ".join([f"{date.strftime('%Y-%m-%d') if date else 'Unknown'}" for _, date in file_dates])
            st.info(f"📅 Data from {len(file_dates)} file(s): {dates_info}")
        
        # Period comparison selector
        dates = sorted([d for _, d in file_dates if d is not None], reverse=True)
        if len(dates) >= 2:
            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Compare Periods")
            period1 = st.sidebar.selectbox("Period 1 (Latest)", options=dates, index=0)
            period2 = st.sidebar.selectbox("Period 2 (Compare to)", options=dates, index=1 if len(dates) > 1 else 0)
        else:
            period1 = dates[0] if dates else None
            period2 = None
        
        # Summary metrics over time
        if 'Date' in combined_df.columns:
            st.markdown("### 📊 Trends Over Time")
            
            # Aggregate by date
            agg_dict = {
                'Keyword': 'count',
                'Impressions': 'sum',
                'Clicks': 'sum',
                'Avg Position': 'mean'
            }
            if 'CTR' in combined_df.columns:
                agg_dict['CTR'] = 'mean'
            
            date_metrics = combined_df.groupby('Date').agg(agg_dict).reset_index()
            date_metrics.columns = ['Date'] + [col for col in date_metrics.columns if col != 'Date']
            date_metrics = date_metrics.sort_values('Date')
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                latest = date_metrics.iloc[-1]
                previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                delta = latest['Keyword'] - previous['Keyword']
                st.metric("Total Keywords (1-10)", int(latest['Keyword']), delta=int(delta))
            
            with col2:
                latest = date_metrics.iloc[-1]
                previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                delta = latest['Impressions'] - previous['Impressions']
                st.metric("Total Impressions", f"{latest['Impressions']:,.0f}", delta=f"{delta:,.0f}")
            
            with col3:
                latest = date_metrics.iloc[-1]
                previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                delta = latest['Clicks'] - previous['Clicks']
                st.metric("Total Clicks", f"{latest['Clicks']:,.0f}", delta=f"{delta:,.0f}")
            
            with col4:
                latest = date_metrics.iloc[-1]
                previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                delta = latest['Avg Position'] - previous['Avg Position']
                st.metric("Avg Position", f"{latest['Avg Position']:.1f}", delta=f"{delta:.2f}")
            
            with col5:
                if 'CTR' in date_metrics.columns:
                    latest = date_metrics.iloc[-1]
                    previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                    delta = latest['CTR'] - previous['CTR']
                    st.metric("Avg CTR", f"{latest['CTR']:.2f}%", delta=f"{delta:.2f}%")
            
            # Trend charts
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Impressions Over Time**")
                st.line_chart(date_metrics.set_index('Date')[['Impressions']])
            
            with col2:
                st.markdown("**Clicks Over Time**")
                st.line_chart(date_metrics.set_index('Date')[['Clicks']])
            
            with col3:
                if 'CTR' in date_metrics.columns:
                    st.markdown("**CTR Over Time**")
                    st.line_chart(date_metrics.set_index('Date')[['CTR']])
            
            st.markdown("---")
            
            # Historical Insights
            insights_result = get_historical_insights(combined_df, file_dates)
            if insights_result:
                insights, latest_date, previous_date = insights_result
                
                st.subheader("🔍 Historical Insights")
                
                tabs = st.tabs(["Biggest Movers", "New Keywords", "Dropped Keywords", "Keyword Comparison"])
                
                with tabs[0]:
                    col1, col2 = st.columns(2)
                    with col1:
                        if 'Biggest Position Improvements' in insights:
                            st.markdown("**📈 Biggest Position Improvements**")
                            improvements = insights['Biggest Position Improvements'][['Keyword', 'Avg Position', 'Position Change', 'Impressions', 'Clicks']].head(20)
                            improvements.columns = ['Keyword', 'Current Position', 'Position Change', 'Impressions', 'Clicks']
                            st.dataframe(improvements, use_container_width=True, hide_index=True)
                    with col2:
                        if 'Biggest Position Declines' in insights:
                            st.markdown("**📉 Biggest Position Declines**")
                            declines = insights['Biggest Position Declines'][['Keyword', 'Avg Position', 'Position Change', 'Impressions', 'Clicks']].head(20)
                            declines.columns = ['Keyword', 'Current Position', 'Position Change', 'Impressions', 'Clicks']
                            st.dataframe(declines, use_container_width=True, hide_index=True)
                
                with tabs[1]:
                    if 'New Keywords' in insights:
                        st.markdown(f"**✨ New Keywords Appeared ({len(insights['New Keywords'])} total)**")
                        new_kw = insights['New Keywords'][['Keyword', 'Avg Position', 'Impressions', 'Clicks', 'CTR' if 'CTR' in insights['New Keywords'].columns else '']].head(50)
                        new_kw = new_kw.dropna(axis=1, how='all')
                        st.dataframe(new_kw, use_container_width=True, hide_index=True)
                
                with tabs[2]:
                    if 'Dropped Keywords' in insights:
                        st.markdown(f"**❌ Keywords That Dropped Out ({len(insights['Dropped Keywords'])} total)**")
                        dropped_kw = insights['Dropped Keywords'][['Keyword', 'Avg Position', 'Impressions', 'Clicks', 'CTR' if 'CTR' in insights['Dropped Keywords'].columns else '']].head(50)
                        dropped_kw = dropped_kw.dropna(axis=1, how='all')
                        st.dataframe(dropped_kw, use_container_width=True, hide_index=True)
                
                with tabs[3]:
                    # Custom period comparison
                    if period1 and period2 and period1 != period2:
                        st.markdown(f"**Comparing {period2} → {period1}**")
                        
                        period1_df = combined_df[combined_df['Date'] == period1].copy()
                        period2_df = combined_df[combined_df['Date'] == period2].copy()
                        
                        comparison_df = period1_df[['Keyword', 'Impressions', 'Clicks', 'Avg Position']].copy()
                        comparison_df.columns = ['Keyword', f'Impressions ({period1})', f'Clicks ({period1})', f'Position ({period1})']
                        
                        prev_comparison = period2_df[['Keyword', 'Impressions', 'Clicks', 'Avg Position']].copy()
                        prev_comparison.columns = ['Keyword', f'Impressions ({period2})', f'Clicks ({period2})', f'Position ({period2})']
                        
                        comparison_df = comparison_df.merge(prev_comparison, on='Keyword', how='outer')
                        
                        comparison_df['Impression Change'] = comparison_df[f'Impressions ({period1})'].fillna(0) - comparison_df[f'Impressions ({period2})'].fillna(0)
                        comparison_df['Click Change'] = comparison_df[f'Clicks ({period1})'].fillna(0) - comparison_df[f'Clicks ({period2})'].fillna(0)
                        comparison_df['Position Change'] = comparison_df[f'Position ({period2})'].fillna(comparison_df[f'Position ({period1})']) - comparison_df[f'Position ({period1})'].fillna(comparison_df[f'Position ({period2})'])
                        
                        comparison_df = comparison_df.sort_values('Impression Change', ascending=False)
                        
                        num_results = st.slider("Number of keywords to display", 10, 200, 50, 10)
                        st.dataframe(comparison_df.head(num_results), use_container_width=True, height=600)
            
            st.markdown("---")
            
            # Top Keywords (Latest)
            st.subheader("🔝 Top Keywords (Latest Data)")
            
            latest_date = combined_df['Date'].max()
            latest_df = combined_df[combined_df['Date'] == latest_date].copy()
            
            # Filters and sorting
            col1, col2, col3 = st.columns(3)
            with col1:
                sort_by = st.selectbox("Sort by", ["Impressions", "Clicks", "CTR", "Avg Position"], index=0)
            with col2:
                position_filter = st.multiselect("Filter by Position Range", ["1-3", "4-6", "7-10"], default=[])
            with col3:
                search_term = st.text_input("🔍 Search keywords", "")
            
            # Apply filters
            filtered_df = latest_df.copy()
            
            if position_filter:
                position_ranges = []
                if "1-3" in position_filter:
                    position_ranges.extend([1, 2, 3])
                if "4-6" in position_filter:
                    position_ranges.extend([4, 5, 6])
                if "7-10" in position_filter:
                    position_ranges.extend([7, 8, 9, 10])
                filtered_df = filtered_df[filtered_df['Avg Position'].isin(position_ranges)]
            
            if search_term:
                filtered_df = filtered_df[filtered_df['Keyword'].str.contains(search_term, case=False, na=False)]
            
            # Sort
            filtered_df = filtered_df.sort_values(sort_by, ascending=(sort_by == "Avg Position"))
            
            num_results = st.slider("Number of keywords to display", 10, 200, 50, 10)
            display_cols = ['Keyword', 'Avg Position', 'Impressions', 'Clicks']
            if 'CTR' in filtered_df.columns:
                display_cols.insert(-1, 'CTR')
            
            st.dataframe(filtered_df[display_cols].head(num_results), use_container_width=True, height=600)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                csv = latest_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Latest Data as CSV",
                    data=csv,
                    file_name=f"top_keywords_latest.csv",
                    mime="text/csv"
                )
            with col2:
                if filtered_df is not None and len(filtered_df) != len(latest_df):
                    csv_filtered = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Filtered Results as CSV",
                        data=csv_filtered,
                        file_name=f"filtered_keywords.csv",
                        mime="text/csv"
                    )
        else:
            st.warning("Could not extract dates from filenames. Showing combined data without date tracking.")
            combined_df_no_date = combined_df.drop(columns=['Date']) if 'Date' in combined_df.columns else combined_df
            st.dataframe(combined_df_no_date.head(50), use_container_width=True)
    
    else:
        st.warning("No Excel files found in the directory. Please upload a file first.")
        st.info("💡 Tip: Upload multiple Search Console exports with dates in the filename (e.g., '2025-11-14') to see historical trends.")

elif file_to_process is not None:
    # Single file view
    with st.spinner(f"Processing {file_name}..."):
        result = process_search_console_file(file_to_process)
    
    if result is not None:
        result_df, full_df = result
        
        # Remove Date column if it exists (from single file processing)
        if 'Date' in result_df.columns:
            result_df = result_df.drop(columns=['Date'])
        
        # Display summary stats
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Keywords (1-10)", len(result_df))
        
        with col2:
            total_impressions = result_df['Impressions'].sum() if 'Impressions' in result_df.columns else 0
            st.metric("Total Impressions", f"{total_impressions:,.0f}")
        
        with col3:
            total_clicks = result_df['Clicks'].sum() if 'Clicks' in result_df.columns else 0
            st.metric("Total Clicks", f"{total_clicks:,.0f}")
        
        with col4:
            avg_position = result_df['Avg Position'].mean()
            st.metric("Avg Position", f"{avg_position:.1f}")
        
        with col5:
            if 'CTR' in result_df.columns:
                avg_ctr = result_df['CTR'].mean()
                st.metric("Avg CTR", f"{avg_ctr:.2f}%")
        
        st.markdown("---")
        
        # Filters and sorting
        st.subheader("🔝 Top Keywords")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sort_by = st.selectbox("Sort by", ["Impressions", "Clicks", "CTR", "Avg Position"], index=0)
        with col2:
            position_filter = st.multiselect("Filter by Position Range", ["1-3", "4-6", "7-10"], default=[])
        with col3:
            search_term = st.text_input("🔍 Search keywords", "")
        with col4:
            if 'CTR' in result_df.columns:
                min_ctr = st.number_input("Min CTR %", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            else:
                min_ctr = 0
        
        # Apply filters
        filtered_df = result_df.copy()
        
        if position_filter:
            position_ranges = []
            if "1-3" in position_filter:
                position_ranges.extend([1, 2, 3])
            if "4-6" in position_filter:
                position_ranges.extend([4, 5, 6])
            if "7-10" in position_filter:
                position_ranges.extend([7, 8, 9, 10])
            filtered_df = filtered_df[filtered_df['Avg Position'].isin(position_ranges)]
        
        if search_term:
            filtered_df = filtered_df[filtered_df['Keyword'].str.contains(search_term, case=False, na=False)]
        
        if 'CTR' in filtered_df.columns and min_ctr > 0:
            filtered_df = filtered_df[filtered_df['CTR'] >= min_ctr]
        
        # Sort
        filtered_df = filtered_df.sort_values(sort_by, ascending=(sort_by == "Avg Position"))
        
        num_results = st.slider("Number of keywords to display", 10, 200, 50, 10)
        
        display_cols = ['Keyword', 'Avg Position', 'Impressions', 'Clicks']
        if 'CTR' in filtered_df.columns:
            display_cols.insert(-1, 'CTR')
        
        st.dataframe(filtered_df[display_cols].head(num_results), use_container_width=True, height=600)
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            csv = result_df.to_csv(index=False)
            st.download_button(
                label="📥 Download All as CSV",
                data=csv,
                file_name=f"top_keywords_{file_name.replace('.xlsx', '').replace('.xls', '')}.csv",
                mime="text/csv"
            )
        with col2:
            if len(filtered_df) != len(result_df):
                csv_filtered = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Results as CSV",
                    data=csv_filtered,
                    file_name=f"filtered_keywords_{file_name.replace('.xlsx', '').replace('.xls', '')}.csv",
                    mime="text/csv"
                )
        
        # Keyword Opportunities
        st.markdown("---")
        st.subheader("🎯 Keyword Opportunities")
        
        opportunities = get_keyword_opportunities(result_df)
        
        if opportunities:
            opp_tabs = st.tabs(list(opportunities.keys()))
            
            for i, (opp_name, opp_df) in enumerate(opportunities.items()):
                with opp_tabs[i]:
                    st.markdown(f"**{opp_name}** ({len(opp_df)} keywords)")
                    display_cols_opp = ['Keyword', 'Avg Position', 'Impressions', 'Clicks']
                    if 'CTR' in opp_df.columns:
                        display_cols_opp.insert(-1, 'CTR')
                    st.dataframe(opp_df[display_cols_opp].head(50), use_container_width=True, hide_index=True)
                    
                    # Download opportunity
                    csv_opp = opp_df.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {opp_name} as CSV",
                        data=csv_opp,
                        file_name=f"{opp_name.lower().replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"download_{i}"
                    )
        
        # Additional insights
        st.markdown("---")
        st.subheader("📈 Additional Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Position Distribution by Range**")
            position_ranges_df = pd.DataFrame({
                'Range': ['1-3', '4-6', '7-10'],
                'Count': [
                    len(result_df[result_df['Avg Position'].between(1, 3)]),
                    len(result_df[result_df['Avg Position'].between(4, 6)]),
                    len(result_df[result_df['Avg Position'].between(7, 10)])
                ]
            })
            st.bar_chart(position_ranges_df.set_index('Range'))
        
        with col2:
            st.markdown("**Top 10 Keywords by CTR**")
            if 'CTR' in result_df.columns:
                top_ctr = result_df.nlargest(10, 'CTR')[['Keyword', 'CTR', 'Impressions', 'Clicks']]
                st.dataframe(top_ctr, use_container_width=True, hide_index=True)
            else:
                st.info("CTR data not available")
        
        with col3:
            st.markdown("**Position Distribution**")
            position_dist = result_df['Avg Position'].value_counts().sort_index()
            st.bar_chart(position_dist)
        
else:
    st.info("👆 Please upload a Search Console Excel file or select an existing file from the sidebar to get started.")
    st.markdown("""
    ### How to use:
    1. **Choose view mode**: 
       - **Single File**: View one file at a time with filters and opportunities
       - **Historical Comparison**: Compare all files over time (automatically detects dates from filenames)
    2. **Upload a file**: Use the file uploader in the sidebar to upload a new Search Console export
    3. **Or select existing**: Choose from files already in the directory
    4. The dashboard will automatically:
       - Filter keywords in positions 1-10
       - Sort by search volume (impressions), clicks, CTR, or position
       - Display the top keywords in an interactive table
       - Show historical trends if multiple files are available
       - Identify keyword opportunities
    
    ### Expected file format:
    - Excel file (.xlsx or .xls) exported from Google Search Console
    - Should contain columns: Query/Keyword, Position, Impressions, Clicks, CTR
    - For historical tracking, include dates in filename (e.g., `2025-11-14` or `20251114`)
    
    ### Features:
    - **Sorting**: Sort by Impressions, Clicks, CTR, or Position
    - **Filtering**: Filter by position range (1-3, 4-6, 7-10)
    - **Search**: Search keywords by text
    - **Opportunities**: Identify high-impression/low-click keywords, quick wins, and high-CTR keywords
    - **Historical Insights**: Track position changes, new keywords, and dropped keywords over time
    """)
