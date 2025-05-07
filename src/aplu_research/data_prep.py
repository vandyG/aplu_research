# %%
import polars as pl

# %%
# NSF
nsf_raw = pl.read_csv(
    "/home/vandy/work/aplu_research/data/nsf_herd.csv",
    schema_overrides={"IPEDS UnitID": pl.Utf8},
).with_columns(
    pl.col("IPEDS UnitID").cast(
        pl.Int64,
        strict=False,
    ),
)

nsf_missing = pl.read_csv("/home/vandy/work/aplu_research/data/nsf_herd_mising_ipeds.csv").drop_nulls()

nsf_upserted = nsf_raw.join(
    nsf_missing,
    on="Institution Name",
    how="left",
    suffix="_miss",
).with_columns(
    pl.coalesce(
        [
            pl.col("IPEDS UnitID_miss"),
            pl.col("IPEDS UnitID"),
        ],
    ).alias("IPEDS UnitID"),
)

nsf_clean = nsf_upserted.filter(~pl.col("IPEDS UnitID").is_null())

nsf = nsf_clean.pivot(
    on="Federal Agency",
    values="R&D Expenditures by Detailed Field and Detailed Funding Source (Standard Form Only)",
    index=["Fiscal Year", "Institution Name", "IPEDS UnitID"],
)

nsf_clubbed = nsf.group_by(["IPEDS UnitID", "Fiscal Year"]).agg(
    [pl.col("Institution Name").first()]
    + [
        pl.col(nsf_col).sum()
        for nsf_col in nsf.columns
        if nsf_col not in ["IPEDS UnitID", "Fiscal Year", "Institution Name"]
    ],
)

# IPEDS
ipeds = pl.read_csv("/home/vandy/work/aplu_research/data/ipeds_inst_info.csv")

# CARNEIGI CLASSIFICATION
carn = pl.read_csv("/home/vandy/work/aplu_research/data/carneigi.csv")

# %%
aau_list = [
    "Arizona State U.",
    "Boston U.",
    "Brandeis U.",
    "Brown U.",
    "California Institute of Technology",
    "Carnegie Mellon U.",
    "Case Western Reserve U.",
    "Columbia U. in the City of New York",
    "Dartmouth C. and Dartmouth Hitchcock Medical Center",
    "Duke U.",
    "Emory U.",
    "George Washington U.",
    "Georgia Institute of Technology",
    "Harvard U.",
    "Indiana U., Bloomington",
    "Johns Hopkins U.",
    "Massachusetts Institute of Technology",
    "Michigan State U.",
    "New York U.",
    "Northwestern U.",
    "Ohio State U.",
    "Pennsylvania State U., University Park and Hershey Medical Center",
    "Princeton U.",
    "Purdue U., West Lafayette",
    "Rice U.",
    "Rutgers, State U. New Jersey, New Brunswick",
    "Stanford U.",
    "SUNY, Stony Brook U.",
    "SUNY, U. Buffalo",
    "Texas A&M U., College Station and Health Science Center",
    "Tufts U.",
    "Tulane U.",
    "U. Arizona",
    "U. California, Berkeley",
    "U. California, Davis",
    "U. California, Irvine",
    "U. California, Los Angeles",
    "U. California, Riverside",
    "U. California, San Diego",
    "U. California, Santa Barbara",
    "U. California, Santa Cruz",
    "U. Chicago",
    "U. Colorado Boulder",
    "U. Florida",
    "U. Illinois, Urbana-Champaign",
    "U. Iowa",
    "U. Kansas",
    "U. Maryland",
    "U. Miami",
    "U. Michigan, Ann Arbor",
    "U. Minnesota, Twin Cities",
    "U. Missouri, Columbia",
    "U. North Carolina, Chapel Hill",
    "U. Notre Dame",
    "U. Oregon",
    "U. Pennsylvania",
    "U. Pittsburgh, Pittsburgh",
    "U. Rochester",
    "U. South Florida",
    "U. Southern California",
    "U. Texas, Austin",
    "U. Utah",
    "U. Virginia, Charlottesville",
    "U. Washington, Seattle",
    "U. Wisconsin-Madison",
    "Vanderbilt U. and Vanderbilt U. Medical Center",
    "Washington U., Saint Louis",
    "Yale U.",
    "Cornell U.",
]
aau_id = nsf_clubbed.filter(pl.col("Institution Name").is_in(aau_list)).select("IPEDS UnitID").unique().to_series()

nsf_aau = nsf_clubbed.with_columns(
    pl.when(pl.col("IPEDS UnitID").is_in(aau_id.to_list()))
    .then(statement=True)
    .otherwise(statement=False)
    .alias("AAU"),
)
# %%
# Define static columns that won't be pivoted
static_cols = ["UnitID", "Institution Name"]

# Get list of all year suffixes present in the data (HD2013 to HD2023)
year_suffixes = [col.split("(")[-1].strip(")") for col in ipeds.columns if "(" in col]
year_suffixes = sorted(set(year_suffixes), key=lambda x: int(x[2:]), reverse=True)

# Prepare list of DataFrames for each year
dfs = []
for suffix in year_suffixes:
    year = suffix[2:]  # Extract the year from suffix (e.g., "2023" from "HD2023")

    # Select columns for this year and rename them to remove the year suffix
    year_cols = [col for col in ipeds.columns if col.endswith(f"({suffix})")]
    renamed_cols = {col: col.split(f" ({suffix})")[0] for col in year_cols}

    # Create year-specific DataFrame
    year_df = (
        ipeds.select([*static_cols, *year_cols]).rename(renamed_cols).with_columns(pl.lit(int(year)).alias("Year"))
    )
    dfs.append(year_df)

# Combine all year-specific DataFrames
final_df = pl.concat(dfs, how="diagonal")  # Diagonal fills missing columns with null

# Optionally: Reorder columns
main_cols = ["UnitID", "Institution Name", "Year"]
other_cols = [col for col in final_df.columns if col not in main_cols]
final_df: pl.DataFrame = final_df.select([*main_cols, *other_cols])

# %%
# Calculate unique counts per institution
unique_counts = final_df.group_by(["UnitID", "Institution Name"]).agg(
    *[
        pl.col(col).drop_nulls().n_unique().alias(f"{col}_unique_count")
        for col in final_df.columns
        if col not in ["UnitID", "Institution Name", "Year"]
    ],
)

# Sort columns logically
column_order = ["UnitID", "Institution Name"] + [
    f"{col}_unique_count"
    for col in final_df.columns
    if col
    not in [
        "UnitID",
        "Institution Name",
        "Year",
    ]
]

unique_counts = unique_counts.select(column_order)

# %%
inst_data = final_df.join(
    carn.drop(["name", "city", "state"]),
    left_on="UnitID",
    right_on="unitid",
    how="left",
)

ipeds_nsf = inst_data.join(
    nsf_aau,
    left_on=["UnitID", "Year"],
    right_on=["IPEDS UnitID", "Fiscal Year"],
    how="inner",
).sort("UnitID", "Year")

# %%
# Write IPEDS+CARN and NSF

ipeds_nsf.write_csv("data/ipeds_nsf.csv")
