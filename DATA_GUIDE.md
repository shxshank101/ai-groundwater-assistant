# Data Guide - getting the real data

The app never creates measurements. These steps put **official** files into the app.

## 1. Reports (PDF) → RAG chatbot
1. Open the CGWB publications portal: https://cgwb.gov.in/cgwbpnm/
2. Search for and download, for example:
   - *National Compilation on Dynamic Ground Water Resources of India* (2024 edition was issued Dec 2024; check if a newer one exists)
   - State reports such as *Dynamic Ground Water Resources of <State>, 2024*
   - Ground Water Year Book and Ground Water Quality reports
3. In the app: **Document Library → Upload**. Fill in the source URL (the page you downloaded from), organization (CGWB) and publication year. This is stored and shown with the document.

Or run `python download_official_data.py` after writing `data/metadata/sources.json` with direct file links you copied:
```json
[{"url": "https://.../file.pdf", "type": "pdf", "organization": "CGWB", "publication_year": "2024"}]
```

## 2. Groundwater levels (CSV) → analytics dashboard
1. Open India-WRIS: https://indiawris.gov.in/ → Ground Water Level section (also see https://cgwb.gov.in/hi/ground-water-level-monitoring and https://nwdp.nwic.gov.in/).
2. Download the groundwater level data as CSV (state/district-wise exports are available).
3. The loader needs these columns (common alternative names are mapped automatically):
   `date, state_name, district_name, station_name, currentlevel` - optional: `latitude, longitude, level_diff, unit`.
   If the export has different names, rename the header row in a spreadsheet.
4. In the app: **Data Sources → Add a groundwater-level CSV**. Fill the metadata form. The app validates the file and records the measurement period and coverage **from the data itself**.

Note: copies of India-WRIS data also appear on the India Data Portal (indiadataportal.com). That is a
mirror, not a primary source - always cite the original official URL, and check the "last updated" date.

## 3. Metadata recorded for every dataset
dataset name · source URL · source organization · measurement period · publication date · geographic
coverage · measurement units · download date · limitations. Unknown fields are stored as `unknown`, never guessed.

## 4. Data integrity rules the code follows
- No random/synthetic data in the app. Test fixtures exist only inside `tests/` (temporary folders).
- Missing values stay missing; rows without a date or depth are dropped, **not** filled.
- Only exact duplicate rows are removed (counted and reported).
- Odd values (e.g. depth > 400 m) are flagged, not deleted.
- Depth unit = m bgl. A larger value means a deeper water table. Mixed units are rejected.
- Means and trend slopes are labelled **derived**; nothing is labelled as a prediction.
