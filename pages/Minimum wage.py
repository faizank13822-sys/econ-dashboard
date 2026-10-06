import altair as alt
import pandas as pd
import streamlit as st
from fredapi import Fred

st.set_page_config(page_title="Minimum Wage Test", layout="wide")
fred = Fred(api_key=st.secrets["FRED_API_KEY"])

MEASURES = {
    "Total jobs": ("ARNA", "LANA"),
    "Leisure and hospitality jobs": ("ARLEIH", "LALEIH"),
}


@st.cache_data(ttl=86400)
def load(series_id):
    return fred.get_series(
        series_id, observation_start="2015-01-01", observation_end="2019-12-31"
    ).dropna()


def avg_change(frame, before, after):
    # percent change in the average level from one year to the next
    return (frame.loc[after].mean() / frame.loc[before].mean() - 1) * 100


st.title("Does a higher minimum wage cost jobs?")
st.write(
    "Arkansas raised its minimum wage from 8.50 dollars to 9.25 on January 1, 2019. "
    "Louisiana stayed at the federal $7.25. I compare job growth in the two neighboring "
    "states to see if the raise made a visible difference. I stop at 2019 because "
    "COVID in 2020 would ruin the comparison."
)

measure = st.selectbox("Pick a measure", list(MEASURES))
ar_id, la_id = MEASURES[measure]

df = pd.concat(
    [load(ar_id).rename("Arkansas"), load(la_id).rename("Louisiana")], axis=1
).dropna()
df.index.name = "date"

# Set both states to 100 in December 2018 so they are easy to compare
base = df.loc[pd.Timestamp("2018-12-01")]
indexed = df / base * 100
long = indexed.reset_index().melt("date", var_name="State", value_name="Index")

line = (
    alt.Chart(long)
    .mark_line()
    .encode(
        x=alt.X("date:T", title=None),
        y=alt.Y("Index:Q", title="Index (Dec 2018 = 100)", scale=alt.Scale(zero=False)),
        color="State:N",
        tooltip=["date:T", "State:N", "Index:Q"],
    )
)
rule = (
    alt.Chart(pd.DataFrame({"date": [pd.Timestamp("2019-01-01")]}))
    .mark_rule(strokeDash=[5, 5], color="gray")
    .encode(x="date:T")
)
st.altair_chart((line + rule).properties(height=400), use_container_width=True)
st.caption("The dashed line marks when Arkansas's raise took effect.")

# The math
change_2019 = avg_change(df, "2018", "2019")
change_2018 = avg_change(df, "2017", "2018")
did_real = change_2019["Arkansas"] - change_2019["Louisiana"]
did_placebo = change_2018["Arkansas"] - change_2018["Louisiana"]

st.subheader("The numbers")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Arkansas growth, 2018 to 2019", f"{change_2019['Arkansas']:.2f}%")
c2.metric("Louisiana growth, 2018 to 2019", f"{change_2019['Louisiana']:.2f}%")
c3.metric("Difference in differences", f"{did_real:+.2f} pts")
c4.metric("Same test one year earlier", f"{did_placebo:+.2f} pts")

st.subheader("How to read this")
st.write(
    "The difference in differences is Arkansas's job growth minus Louisiana's. "
    "A negative number would suggest the raise cost jobs. A positive number would suggest it did not. "
    "The last box is a placebo test: I run the exact same math on 2017 to 2018, when nothing changed in either state. "
    "If that number is about as big as the real one, then the gap I found is probably normal noise between the two states and not an effect of the raise."
)

st.subheader("What this can and cannot show")
st.write(
    "- The raise was small, about 9 percent, so any effect would be small too.\n"
    "- Two states is a tiny sample. Any other difference between them could explain the gap.\n"
    "- Total jobs is a blunt measure. Leisure and hospitality is where low wage work is concentrated, so switch to it above.\n"
    "- Employers may respond with hours or prices instead of layoffs, and this test cannot see that.\n"
    "- A real study would repeat this across many state pairs."
)
st.write("Write your own conclusion here after you look at the results.")