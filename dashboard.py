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
        keyword_col = None
        
        # Find position column (case-insensitive)
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'position' in col_lower or 'avg. position' in col_lower or 'avg position' in col_lower:
                position_col = col
            if 'impressions' in col_lower:
                impressions_col = col
            if 'clicks' in col_lower:
                clicks_col = col
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
        
        # Sort by impressions (search volume) descending
        df_filtered = df_filtered.sort_values(by=impressions_col, ascending=False)
        
        # Select relevant columns for display
        display_cols = [keyword_col, position_col, impressions_col]
        if clicks_col:
            display_cols.append(clicks_col)
        
        # Add any other numeric columns that might be useful
        for col in df.columns:
            if col not in display_cols and df[col].dtype in ['int64', 'float64']:
                if col not in [position_col, impressions_col, clicks_col]:
                    display_cols.append(col)
        
        result_df = df_filtered[display_cols].copy()
        
        # Rename columns for better display
        column_mapping = {
            keyword_col: 'Keyword',
            position_col: 'Avg Position',
            impressions_col: 'Impressions',
            clicks_col: 'Clicks' if clicks_col else None
        }
        column_mapping = {k: v for k, v in column_mapping.items() if v is not None}
        result_df = result_df.rename(columns=column_mapping)
        
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
        
        # Summary metrics over time
        if 'Date' in combined_df.columns:
            st.markdown("### 📊 Trends Over Time")
            
            # Aggregate by date
            date_metrics = combined_df.groupby('Date').agg({
                'Keyword': 'count',
                'Impressions': 'sum',
                'Clicks': 'sum',
                'Avg Position': 'mean'
            }).reset_index()
            date_metrics.columns = ['Date', 'Total Keywords', 'Total Impressions', 'Total Clicks', 'Avg Position']
            date_metrics = date_metrics.sort_values('Date')
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                latest = date_metrics.iloc[-1]
                previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                delta = latest['Total Keywords'] - previous['Total Keywords']
                st.metric("Total Keywords (1-10)", int(latest['Total Keywords']), delta=int(delta))
            
            with col2:
                latest = date_metrics.iloc[-1]
                previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                delta = latest['Total Impressions'] - previous['Total Impressions']
                st.metric("Total Impressions", f"{latest['Total Impressions']:,.0f}", delta=f"{delta:,.0f}")
            
            with col3:
                latest = date_metrics.iloc[-1]
                previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                delta = latest['Total Clicks'] - previous['Total Clicks']
                st.metric("Total Clicks", f"{latest['Total Clicks']:,.0f}", delta=f"{delta:,.0f}")
            
            with col4:
                latest = date_metrics.iloc[-1]
                previous = date_metrics.iloc[-2] if len(date_metrics) > 1 else latest
                delta = latest['Avg Position'] - previous['Avg Position']
                st.metric("Avg Position", f"{latest['Avg Position']:.1f}", delta=f"{delta:.2f}")
            
            # Trend charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Impressions Over Time**")
                st.line_chart(date_metrics.set_index('Date')[['Total Impressions']])
            
            with col2:
                st.markdown("**Clicks Over Time**")
                st.line_chart(date_metrics.set_index('Date')[['Total Clicks']])
            
            st.markdown("---")
            
            # Keyword comparison - show top keywords and their changes
            st.subheader("🔝 Top Keywords (Latest Data)")
            
            # Get latest date
            latest_date = combined_df['Date'].max()
            latest_df = combined_df[combined_df['Date'] == latest_date].copy()
            latest_df = latest_df.sort_values('Impressions', ascending=False)
            
            # Compare with previous period if available
            if len(date_metrics) > 1:
                previous_date = date_metrics.iloc[-2]['Date']
                previous_df = combined_df[combined_df['Date'] == previous_date].copy()
                
                # Create comparison
                comparison_df = latest_df[['Keyword', 'Impressions', 'Clicks', 'Avg Position']].copy()
                comparison_df.columns = ['Keyword', 'Impressions (Latest)', 'Clicks (Latest)', 'Position (Latest)']
                
                # Merge with previous data
                prev_comparison = previous_df[['Keyword', 'Impressions', 'Clicks', 'Avg Position']].copy()
                prev_comparison.columns = ['Keyword', 'Impressions (Previous)', 'Clicks (Previous)', 'Position (Previous)']
                
                comparison_df = comparison_df.merge(prev_comparison, on='Keyword', how='left')
                
                # Calculate changes
                comparison_df['Impression Change'] = comparison_df['Impressions (Latest)'] - comparison_df['Impressions (Previous)'].fillna(0)
                comparison_df['Click Change'] = comparison_df['Clicks (Latest)'] - comparison_df['Clicks (Previous)'].fillna(0)
                comparison_df['Position Change'] = comparison_df['Position (Previous)'].fillna(comparison_df['Position (Latest)']) - comparison_df['Position (Latest)']
                
                comparison_df = comparison_df.sort_values('Impressions (Latest)', ascending=False)
                
                st.markdown(f"**Comparing {previous_date} → {latest_date}**")
                num_results = st.slider("Number of keywords to display", 10, 100, 50, 10)
                st.dataframe(comparison_df.head(num_results), use_container_width=True, height=600)
            else:
                num_results = st.slider("Number of keywords to display", 10, 100, 50, 10)
                st.dataframe(latest_df[['Keyword', 'Impressions', 'Clicks', 'Avg Position']].head(num_results), 
                            use_container_width=True, height=600)
            
            # Download button
            csv = latest_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Latest Data as CSV",
                data=csv,
                file_name=f"top_keywords_latest.csv",
                mime="text/csv"
            )
        else:
            st.warning("Could not extract dates from filenames. Showing combined data without date tracking.")
            # Fallback to single file view
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
        col1, col2, col3, col4 = st.columns(4)
        
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
        
        st.markdown("---")
        
        # Display top keywords table
        st.subheader("🔝 Top Keywords by Search Volume")
        
        # Number of results to show
        num_results = st.slider("Number of keywords to display", 10, 100, 50, 10)
        
        # Display table
        st.dataframe(
            result_df.head(num_results),
            use_container_width=True,
            height=600
        )
        
        # Download button
        csv = result_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"top_keywords_{file_name.replace('.xlsx', '').replace('.xls', '')}.csv",
            mime="text/csv"
        )
        
        # Additional insights
        st.markdown("---")
        st.subheader("📈 Additional Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top 10 Keywords:**")
            top_10 = result_df.head(10)[['Keyword', 'Impressions', 'Avg Position']]
            st.dataframe(top_10, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Position Distribution:**")
            position_dist = result_df['Avg Position'].value_counts().sort_index()
            st.bar_chart(position_dist)
        
else:
    st.info("👆 Please upload a Search Console Excel file or select an existing file from the sidebar to get started.")
    st.markdown("""
    ### How to use:
    1. **Choose view mode**: 
       - **Single File**: View one file at a time
       - **Historical Comparison**: Compare all files over time (automatically detects dates from filenames)
    2. **Upload a file**: Use the file uploader in the sidebar to upload a new Search Console export
    3. **Or select existing**: Choose from files already in the directory
    4. The dashboard will automatically:
       - Filter keywords in positions 1-10
       - Sort by search volume (impressions)
       - Display the top keywords in an interactive table
       - Show historical trends if multiple files are available
    
    ### Expected file format:
    - Excel file (.xlsx or .xls) exported from Google Search Console
    - Should contain columns: Query/Keyword, Position, Impressions, Clicks
    - For historical tracking, include dates in filename (e.g., `2025-11-14` or `20251114`)
    """)

