
import io
import re

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Data Analytics Studio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background: #f7f8fc; }
        .block-container { padding-top: 1.5rem; max-width: 1500px; }
        .main-title { font-size: 2.3rem; font-weight: 800; letter-spacing: -1px; }
        .subtitle { color: #6b7280; margin-bottom: 1.5rem; }
        .kpi-card {
            background: white; border: 1px solid #e7e9ef; border-radius: 16px;
            padding: 20px 22px; min-height: 125px;
            box-shadow: 0 2px 8px rgba(20,25,40,.04);
        }
        .kpi-label { color: #6b7280; font-size: .85rem; font-weight: 600; }
        .kpi-value { font-size: 1.75rem; font-weight: 800; color: #111827; margin-top: 8px; }
        .kpi-subtitle { color: #9ca3af; font-size: .78rem; margin-top: 5px; }
        .section-title { font-size: 1.25rem; font-weight: 750; color: #111827; margin: 1.5rem 0 .8rem; }
        [data-testid="stFileUploader"] {
            background: white; border-radius: 16px; border: 1px dashed #cfd4df; padding: 8px;
        }
        div[data-testid="stMetric"] {
            background: white; border: 1px solid #e7e9ef; border-radius: 14px; padding: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_number(value):
    if pd.isna(value):
        return "—"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.2f}"


def card(label, value, subtitle=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def detect_columns(df):
    """
    Detect datetime, numeric, and categorical columns safely.
    Date conversion is attempted only for object columns whose names
    suggest a date/time field. This prevents datetime columns from
    being treated as numeric KPI columns.
    """
    date_keywords = [
        "date", "time", "timestamp", "year", "month", "day"
    ]

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue

        if pd.api.types.is_object_dtype(df[col]):
            normalized_name = re.sub(r"[^a-z0-9]", "", str(col).lower())
            looks_like_date = any(
                keyword in normalized_name for keyword in date_keywords
            )

            if looks_like_date:
                converted = pd.to_datetime(
                    df[col], errors="coerce"
                )
                if converted.notna().mean() >= 0.80:
                    df[col] = converted

    datetime_cols = df.select_dtypes(
        include=["datetime64[ns]", "datetime64[ns, UTC]"]
    ).columns.tolist()

    numeric_cols = df.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_cols = [
        col for col in df.columns
        if col not in datetime_cols and col not in numeric_cols
    ]

    return numeric_cols, categorical_cols, datetime_cols


def find_numeric_column(df, keywords):
    """
    Detect a business metric by name, but ONLY among genuinely
    numeric columns. Datetime columns can therefore never be selected
    for sum-based KPIs.
    """
    numeric_columns = df.select_dtypes(include=np.number).columns.tolist()

    for col in numeric_columns:
        normalized = re.sub(r"[^a-z0-9]", "", str(col).lower())
        if any(keyword in normalized for keyword in keywords):
            return col

    return None


def create_kpi_data(df):
    return {
        "sales": find_numeric_column(
            df,
            ["sales", "revenue", "amount", "turnover", "grosssales", "netsales"],
        ),
        "profit": find_numeric_column(
            df,
            ["profit", "netprofit", "grossprofit"],
        ),
        "quantity": find_numeric_column(
            df,
            ["quantity", "qty", "units", "volume"],
        ),
        "cost": find_numeric_column(
            df,
            ["cost", "expense", "cogs"],
        ),
    }


def numeric_sum(df, col):
    """Safely sum a numeric column."""
    if not col or col not in df.columns:
        return 0.0

    if not pd.api.types.is_numeric_dtype(df[col]):
        return 0.0

    return float(
        pd.to_numeric(df[col], errors="coerce").sum()
    )


st.markdown(
    '<div class="main-title">📊 Data Analytics Studio</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Upload your dataset and instantly explore, analyze and visualize your data.</div>',
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx", "xls"],
)

if uploaded_file is None:
    st.info("👆 Upload a CSV or Excel file to start your analysis.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🔍 Explore")
        st.write("Inspect rows, columns, data types, missing values and duplicates.")
    with c2:
        st.markdown("### 📈 Analyze")
        st.write("Automatically detect useful numeric business metrics.")
    with c3:
        st.markdown("### 📊 Visualize")
        st.write("Generate interactive Plotly charts from your dataset.")
    st.stop()

try:
    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Unable to read the uploaded file: {e}")
    st.stop()

df.columns = [str(col).strip() for col in df.columns]

numeric_cols, categorical_cols, datetime_cols = detect_columns(df)
kpi_columns = create_kpi_data(df)

with st.sidebar:
    st.markdown("## 🎛️ Dashboard Controls")
    st.markdown("---")
    st.markdown("### Dataset")
    st.write(uploaded_file.name)
    st.write(f"**{df.shape[0]:,} rows × {df.shape[1]:,} columns**")
    st.markdown("---")
    st.markdown("### Detected Columns")
    st.write(f"🔢 Numeric: **{len(numeric_cols)}**")
    st.write(f"🔤 Categorical: **{len(categorical_cols)}**")
    st.write(f"📅 Date: **{len(datetime_cols)}**")

st.markdown('<div class="section-title">Dataset Overview</div>', unsafe_allow_html=True)

missing_values = int(df.isna().sum().sum())
duplicate_records = int(df.duplicated().sum())

col1, col2, col3, col4 = st.columns(4)
with col1:
    card("ROWS", f"{len(df):,}", "Total records")
with col2:
    card("COLUMNS", f"{len(df.columns):,}", "Total fields")
with col3:
    card("MISSING VALUES", f"{missing_values:,}", "Across entire dataset")
with col4:
    card("DUPLICATE RECORDS", f"{duplicate_records:,}", "Exact duplicate rows")

with st.expander("📋 View column names and data types"):
    column_info = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Non-Null": df.notna().sum().values,
        "Missing": df.isna().sum().values,
        "Unique": [df[col].nunique(dropna=True) for col in df.columns],
    })
    column_info["Missing %"] = (
        column_info["Missing"] / max(len(df), 1) * 100
    ).round(2)
    st.dataframe(column_info, use_container_width=True, hide_index=True)

with st.expander("🔎 Pandas-style dataset information"):
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.code(buffer.getvalue(), language="text")

with st.expander("⚠️ Missing value analysis"):
    missing_df = df.isna().sum().reset_index()
    missing_df.columns = ["Column", "Missing Values"]
    missing_df["Missing %"] = (
        missing_df["Missing Values"] / max(len(df), 1) * 100
    ).round(2)
    missing_df = missing_df[missing_df["Missing Values"] > 0].sort_values(
        "Missing Values", ascending=False
    )
    if missing_df.empty:
        st.success("No missing values found.")
    else:
        st.dataframe(missing_df, use_container_width=True, hide_index=True)

st.markdown('<div class="section-title">🎛️ Smart Filters</div>', unsafe_allow_html=True)

filtered_df = df.copy()
filter_cols = (categorical_cols + datetime_cols + numeric_cols)[:12]

if filter_cols:
    filter_columns = st.columns(min(4, len(filter_cols)))

    for i, col in enumerate(filter_cols):
        with filter_columns[i % len(filter_columns)]:
            if col in categorical_cols:
                values = df[col].dropna().unique().tolist()
                if len(values) <= 100:
                    selected = st.multiselect(
                        col,
                        options=sorted(values, key=str),
                        key=f"filter_{col}",
                    )
                    if selected:
                        filtered_df = filtered_df[filtered_df[col].isin(selected)]

            elif col in datetime_cols:
                valid_dates = df[col].dropna()
                if not valid_dates.empty:
                    min_date = valid_dates.min().date()
                    max_date = valid_dates.max().date()
                    date_range = st.date_input(
                        col,
                        value=(min_date, max_date),
                        key=f"filter_{col}",
                    )
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        start_date, end_date = date_range
                        filtered_df = filtered_df[
                            filtered_df[col].dt.date.between(start_date, end_date)
                        ]

            elif col in numeric_cols:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                if not series.empty:
                    min_val = float(series.min())
                    max_val = float(series.max())
                    if min_val != max_val:
                        selected_range = st.slider(
                            col,
                            min_value=min_val,
                            max_value=max_val,
                            value=(min_val, max_val),
                            key=f"filter_{col}",
                        )
                        filtered_df = filtered_df[
                            pd.to_numeric(filtered_df[col], errors="coerce").between(
                                selected_range[0], selected_range[1]
                            )
                        ]

st.caption(f"Showing {len(filtered_df):,} of {len(df):,} records")

st.markdown('<div class="section-title">📌 Key Performance Indicators</div>', unsafe_allow_html=True)

sales_col = kpi_columns["sales"]
profit_col = kpi_columns["profit"]
quantity_col = kpi_columns["quantity"]

kpi_values = []

if sales_col:
    total_sales = numeric_sum(filtered_df, sales_col)
    kpi_values.append(("TOTAL SALES", format_number(total_sales), sales_col))

if profit_col:
    total_profit = numeric_sum(filtered_df, profit_col)
    kpi_values.append(("TOTAL PROFIT", format_number(total_profit), profit_col))

if quantity_col:
    total_quantity = numeric_sum(filtered_df, quantity_col)
    kpi_values.append(("TOTAL QUANTITY", format_number(total_quantity), quantity_col))

if sales_col and profit_col:
    sales = numeric_sum(filtered_df, sales_col)
    profit = numeric_sum(filtered_df, profit_col)
    margin = profit / sales * 100 if sales != 0 else 0
    kpi_values.append(("PROFIT MARGIN", f"{margin:.2f}%", "Profit / Sales"))

if kpi_values:
    cols = st.columns(len(kpi_values))
    for col, data in zip(cols, kpi_values):
        with col:
            card(data[0], data[1], data[2])
else:
    st.info("No standard sales/profit columns were detected. Use the custom KPI section below.")

with st.expander("⚙️ Customize KPI metrics"):
    if numeric_cols:
        selected_kpis = st.multiselect(
            "Select numeric columns to summarize",
            numeric_cols,
            default=numeric_cols[:4],
        )
        if selected_kpis:
            custom_cols = st.columns(min(4, len(selected_kpis)))
            for i, col in enumerate(selected_kpis):
                with custom_cols[i % len(custom_cols)]:
                    card(
                        col.upper(),
                        format_number(numeric_sum(filtered_df, col)),
                        "Sum",
                    )

st.markdown('<div class="section-title">📈 Data Visualization</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Trend", "📊 Comparison", "🔵 Distribution", "🧩 Custom Chart"]
)

with tab1:
    if datetime_cols and numeric_cols:
        date_col = st.selectbox("Date column", datetime_cols, key="trend_date")
        metric_col = st.selectbox("Metric", numeric_cols, key="trend_metric")

        trend_df = filtered_df.dropna(subset=[date_col]).copy()
        trend_df["_period"] = trend_df[date_col].dt.to_period("M").dt.to_timestamp()
        trend_df = (
            trend_df.groupby("_period", as_index=False)[metric_col]
            .sum()
            .rename(columns={"_period": date_col})
        )

        fig = px.line(
            trend_df,
            x=date_col,
            y=metric_col,
            markers=True,
            title=f"{metric_col} Over Time",
        )
        fig.update_layout(template="plotly_white", hovermode="x unified", height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("A date column and numeric column are needed for a trend chart.")

with tab2:
    if categorical_cols and numeric_cols:
        category_col = st.selectbox(
            "Category", categorical_cols, key="comparison_category"
        )
        metric_col = st.selectbox(
            "Metric", numeric_cols, key="comparison_metric"
        )
        max_categories = st.slider(
            "Number of categories", 5, 30, 10, key="comparison_n"
        )

        comparison_df = (
            filtered_df.groupby(category_col)[metric_col]
            .sum()
            .sort_values(ascending=False)
            .head(max_categories)
            .reset_index()
        )

        fig = px.bar(
            comparison_df,
            x=category_col,
            y=metric_col,
            text_auto=".2s",
            title=f"{metric_col} by {category_col}",
        )
        fig.update_layout(
            template="plotly_white",
            height=450,
            xaxis_title="",
            yaxis_title=metric_col,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("A categorical column and numeric column are needed for comparison analysis.")

with tab3:
    if numeric_cols:
        metric_col = st.selectbox(
            "Numeric column", numeric_cols, key="distribution_metric"
        )
        chart_type = st.radio(
            "Chart type", ["Histogram", "Box Plot"], horizontal=True
        )

        if chart_type == "Histogram":
            fig = px.histogram(
                filtered_df, x=metric_col, nbins=40,
                title=f"Distribution of {metric_col}"
            )
        else:
            fig = px.box(
                filtered_df, y=metric_col, points="outliers",
                title=f"Box Plot — {metric_col}"
            )

        fig.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No numeric columns detected.")

with tab4:
    chart_type = st.selectbox(
        "Chart type",
        ["Bar", "Line", "Scatter", "Area", "Pie"],
        key="custom_chart_type",
    )
    x_col = st.selectbox(
        "X axis", df.columns.tolist(), key="custom_x"
    )

    y_options = [col for col in numeric_cols if col != x_col]
    y_col = None

    if chart_type != "Pie":
        if y_options:
            y_col = st.selectbox("Y axis", y_options, key="custom_y")
        else:
            st.warning("Select a dataset with numeric columns for the Y axis.")

    if st.button("Generate Chart", type="primary"):
        if chart_type == "Bar":
            fig = px.bar(filtered_df, x=x_col, y=y_col)
        elif chart_type == "Line":
            fig = px.line(filtered_df, x=x_col, y=y_col)
        elif chart_type == "Scatter":
            fig = px.scatter(filtered_df, x=x_col, y=y_col)
        elif chart_type == "Area":
            fig = px.area(filtered_df, x=x_col, y=y_col)
        else:
            pie_df = filtered_df[x_col].value_counts().head(15).reset_index()
            pie_df.columns = [x_col, "Count"]
            fig = px.pie(pie_df, names=x_col, values="Count")

        fig.update_layout(template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)

if len(numeric_cols) >= 2:
    st.markdown('<div class="section-title">🔗 Correlation Analysis</div>', unsafe_allow_html=True)
    corr = filtered_df[numeric_cols].corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        title="Numeric Feature Correlation",
    )
    fig.update_layout(height=600, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">🗂️ Data Explorer</div>', unsafe_allow_html=True)
st.dataframe(filtered_df, use_container_width=True, height=500)

csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Filtered Dataset",
    data=csv_data,
    file_name="filtered_dataset.csv",
    mime="text/csv",
)

st.markdown("---")
st.caption("Data Analytics Studio • Streamlit + Pandas + NumPy + Plotly")
