# %%
import polars as pl
import plotly.graph_objects as go
import pandas as pd

# %%
nsf_ipeds = pl.read_csv("data/ipeds_nsf.csv")

# %%
id_uta = 228769
uta = nsf_ipeds.filter(pl.col("UnitID") == id_uta)
aau = nsf_ipeds.filter(pl.col("AAU"))

aau_average = aau.group_by("UnitID").agg(
    pl.col("Institution Name").first(),
    pl.col("Year").first(),
    pl.col("State abbreviation").first(),
    pl.col("Historically Black College or University").first(),
    pl.col("Land Grant Institution").first(),
    pl.col("Sector of institution").first(),
    pl.col("FIPS state code").first(),
    pl.col("Degree of urbanization (Urban-centric locale)").first(),
    pl.col("Institution grants a medical degree").first(),
    pl.col("Carnegie Classification 2021: Basic").first(),
    pl.col("control").first(),
    pl.col("Institutional Classification").first(),
    pl.col("Student Access and Earnings Classification").first(),
    pl.col("Research Activity Designation").first(),
    pl.col("Award Level Focus").first(),
    pl.col("Academic Mix").first(),
    pl.col("Graduate Academic Program Mix").first(),
    pl.col("Size").first(),
    pl.col("Campus Setting").first(),
    pl.col("Highest Degree Awarded").first(),
    pl.col("Community Engagement").first(),
    pl.col("Leadership for Public Practice").first(),
    pl.col("Department of Energy").mean(),
    pl.col("National Aeronautics and Space Administration").mean(),
    pl.col("Other federal agency").mean(),
    pl.col("Nonfederal").mean(),
    pl.col("Department of Defense").mean(),
    pl.col("National Science Foundation").mean(),
    pl.col("Department of Agriculture").mean(),
    pl.col("Department of Health and Human Services").mean(),
)
uta_average = uta.group_by("UnitID").agg(
    pl.col("Institution Name").first(),
    pl.col("Year").first(),
    pl.col("State abbreviation").first(),
    pl.col("Historically Black College or University").first(),
    pl.col("Land Grant Institution").first(),
    pl.col("Sector of institution").first(),
    pl.col("FIPS state code").first(),
    pl.col("Degree of urbanization (Urban-centric locale)").first(),
    pl.col("Institution grants a medical degree").first(),
    pl.col("Carnegie Classification 2021: Basic").first(),
    pl.col("control").first(),
    pl.col("Institutional Classification").first(),
    pl.col("Student Access and Earnings Classification").first(),
    pl.col("Research Activity Designation").first(),
    pl.col("Award Level Focus").first(),
    pl.col("Academic Mix").first(),
    pl.col("Graduate Academic Program Mix").first(),
    pl.col("Size").first(),
    pl.col("Campus Setting").first(),
    pl.col("Highest Degree Awarded").first(),
    pl.col("Community Engagement").first(),
    pl.col("Leadership for Public Practice").first(),
    pl.col("Department of Energy").mean(),
    pl.col("National Aeronautics and Space Administration").mean(),
    pl.col("Other federal agency").mean(),
    pl.col("Nonfederal").mean(),
    pl.col("Department of Defense").mean(),
    pl.col("National Science Foundation").mean(),
    pl.col("Department of Agriculture").mean(),
    pl.col("Department of Health and Human Services").mean(),
)
# %%
# Prepare data
funding_cols = [
    "Department of Energy",
    "National Aeronautics and Space Administration",
    "Other federal agency",
    "Nonfederal",
    "Department of Defense",
    "National Science Foundation",
    "Department of Agriculture",
    "Department of Health and Human Services",
]

# Convert to pandas for easier manipulation with plotly
aau_df = aau_average.to_pandas()
uta_df = uta_average.to_pandas()

# Create figure
fig = go.Figure()

# Add box plots for each funding source
for col in funding_cols:
    fig.add_trace(
        go.Box(
            y=aau_df[col], name=col.split(" of ")[-1] if " of " in col else col, boxmean=True, marker_color="lightblue"
        )
    )

    # Add UTA points as markers
    fig.add_trace(
        go.Scatter(
            x=[col.split(" of ")[-1] if " of " in col else col],
            y=[uta_df[col].iloc[0]],
            mode="markers",
            name="UTA" if col == funding_cols[0] else None,
            marker=dict(color="red", size=10),
            showlegend=(col == funding_cols[0]),
        )
    )

# Update layout
fig.update_layout(
    title="Research Funding Comparison: UTA vs AAU Institutions",
    yaxis_title="Funding Amount",
    boxmode="group",
    legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    height=600,
    width=900,
    template="plotly_white",
)

# Improve formatting of axis labels
fig.update_xaxes(tickangle=45)

fig.show()
