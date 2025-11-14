import streamlit as st
import pandas as pd
import os
from pathlib import Path
import glob

# Page configuration
st.set_page_config(
    page_title="Search Console Keyword Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Search Console Keyword Dashboard")
st.markdown("**Top Keywords by Search Volume (Positions 1-10)**")

# Function to process Excel file
def process_search_console_file(file_path):
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
            col_lower = str(col).lower()
            if 'position' in col_lower or 'avg. position' in col_lower:
                position_col = col
            if 'impressions' in col_lower:
                impressions_col = col
            if 'clicks' in col_lower:
                clicks_col = col
            if 'query' in col_lower or 'keyword' in col_lower or 'search query' in col_lower:
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
        
        return result_df, df_filtered
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

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

# Process file if available
if file_to_process is not None:
    with st.spinner(f"Processing {file_name}..."):
        result = process_search_console_file(file_to_process)
    
    if result is not None:
        result_df, full_df = result
        
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
    1. **Upload a file**: Use the file uploader in the sidebar to upload a new Search Console export
    2. **Or select existing**: Choose from files already in the directory
    3. The dashboard will automatically:
       - Filter keywords in positions 1-10
       - Sort by search volume (impressions)
       - Display the top keywords in an interactive table
    
    ### Expected file format:
    - Excel file (.xlsx or .xls) exported from Google Search Console
    - Should contain columns: Query/Keyword, Position, Impressions, Clicks
    """)

