# Search Console Keyword Dashboard

A comprehensive Streamlit dashboard to automatically analyze Google Search Console exports and display top keywords by search volume (positions 1-10) with advanced filtering, historical tracking, and opportunity analysis.

## Features

### Core Features
- 📊 **Automatic Processing**: Upload or select Excel files from Search Console
- 🔝 **Top Keywords**: Filter and sort keywords in positions 1-10 by search volume
- 📈 **Interactive Dashboard**: View metrics, tables, and charts
- 📥 **Export**: Download results as CSV (all data or filtered views)

### Advanced Features
- **CTR Analysis**: Automatic CTR calculation and display
- **Multiple Sort Options**: Sort by Impressions, Clicks, CTR, or Position
- **Advanced Filtering**: 
  - Filter by position ranges (1-3, 4-6, 7-10)
  - Search keywords by text
  - Filter by CTR threshold
- **Keyword Opportunities**:
  - High impressions, low clicks (optimization opportunities)
  - Quick wins (position 4-6 keywords to push to top 3)
  - High CTR keywords (what's working well)
- **Historical Tracking**:
  - Compare multiple time periods
  - Track position changes over time
  - Identify new keywords that appeared
  - Identify keywords that dropped out
  - Biggest position movers (improvements and declines)
- **Comparison Views**: Compare any two time periods side-by-side
- **Enhanced Metrics**: Average CTR, position distribution by ranges, trend charts

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

### Single File View
1. **Upload a file**: Use the file uploader in the sidebar to upload a new Search Console Excel export
2. **Or select existing**: Choose from Excel files already in the directory
3. **Filter and Sort**:
   - Select sort option (Impressions, Clicks, CTR, Position)
   - Filter by position ranges (1-3, 4-6, 7-10)
   - Search keywords by text
   - Set minimum CTR threshold
4. **View Opportunities**: Check the "Keyword Opportunities" section for actionable insights
5. **Export**: Download all data or filtered results as CSV

### Historical Comparison View
1. **Select "Historical Comparison"** from the view mode selector
2. The dashboard automatically processes all Excel files in the directory
3. **View Trends**: See how metrics change over time with trend charts
4. **Historical Insights**:
   - Biggest position movers (improvements and declines)
   - New keywords that appeared
   - Keywords that dropped out
5. **Compare Periods**: Select any two time periods to compare side-by-side
6. **Export**: Download latest data or filtered results

## File Format

The dashboard expects Excel files (.xlsx or .xls) exported from Google Search Console with columns such as:
- Query/Keyword (or "Top queries")
- Position (or Avg. Position)
- Impressions
- Clicks
- CTR (optional, will be calculated if not present)

The dashboard automatically detects column names (case-insensitive), so variations in naming should work.

**For historical tracking**: Include dates in filename (e.g., `2025-11-14` or `20251114`) to enable time-based comparisons.

## Key Features Explained

### Sorting Options
- **Impressions**: Sort by search volume (default)
- **Clicks**: Sort by total clicks
- **CTR**: Sort by click-through rate
- **Position**: Sort by average position (ascending)

### Position Filters
- **1-3**: Top 3 positions (most valuable)
- **4-6**: Quick wins (can be pushed to top 3)
- **7-10**: Lower positions (still in top 10)

### Keyword Opportunities
- **High Impressions, Low Clicks**: Keywords getting lots of visibility but few clicks - optimization opportunities
- **Quick Wins (Position 4-6)**: Keywords close to top 3 that could be pushed higher
- **High CTR Keywords**: Keywords with excellent click-through rates - learn what's working

### Historical Insights
- **Biggest Position Improvements**: Keywords that moved up in rankings
- **Biggest Position Declines**: Keywords that dropped in rankings
- **New Keywords**: Keywords that appeared in latest period
- **Dropped Keywords**: Keywords that fell out of top 10

## Workflow

Whenever you upload a new Search Console export to this directory:
1. The file will appear in the "select existing file" dropdown
2. Select it to automatically process and view results
3. Use filters and sorting to find specific insights
4. Check opportunities section for actionable recommendations
5. Export filtered results for further analysis

For historical tracking:
1. Upload multiple exports with dates in filenames
2. Switch to "Historical Comparison" view
3. Compare periods and track changes over time
4. Identify trends and opportunities

## Export Options

- **Download All**: Export complete dataset
- **Download Filtered**: Export only filtered results
- **Download Opportunities**: Export specific opportunity lists (high impressions/low clicks, quick wins, etc.)
- **Download Historical Comparison**: Export comparison data between periods
