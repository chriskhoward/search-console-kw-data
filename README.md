# Search Console Keyword Dashboard

A Streamlit dashboard to automatically analyze Google Search Console exports and display top keywords by search volume (positions 1-10).

## Features

- 📊 **Automatic Processing**: Upload or select Excel files from Search Console
- 🔝 **Top Keywords**: Filter and sort keywords in positions 1-10 by search volume
- 📈 **Interactive Dashboard**: View metrics, tables, and charts
- 📥 **Export**: Download results as CSV

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the dashboard:**
```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Usage

1. **Upload a file**: Use the file uploader in the sidebar to upload a new Search Console Excel export
2. **Or select existing**: Choose from Excel files already in the directory
3. The dashboard will automatically:
   - Filter keywords in positions 1-10
   - Sort by search volume (impressions)
   - Display the top keywords in an interactive table

## File Format

The dashboard expects Excel files (.xlsx or .xls) exported from Google Search Console with columns such as:
- Query/Keyword
- Position (or Avg. Position)
- Impressions
- Clicks

The dashboard automatically detects column names (case-insensitive), so variations in naming should work.

## Features

- **Summary Metrics**: Total keywords, impressions, clicks, and average position
- **Top Keywords Table**: Sortable table showing top keywords by search volume
- **Position Distribution**: Visual chart showing keyword distribution across positions
- **Export**: Download filtered results as CSV

## Workflow

Whenever you upload a new Search Console export to this directory:
1. The file will appear in the "select existing file" dropdown
2. Select it to automatically process and view results
3. Or upload it directly through the file uploader

