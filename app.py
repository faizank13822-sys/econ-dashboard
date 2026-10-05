import pandas as pd
import streamlit as st
from fredapi import Fred
import altair as alt

st.set_page_config(page_title="US Economy Dashboard", layout="wide")

fred = Fred(api_key=st.secrets["FRED_API_KEY"])

BOOMS = pd.DataFrame(
    [
        ("1961-02-01", "1969-12-31"),
        ("1983-01-01", "1989-12-31"),
        ("1995-01-01", "2000-03-31"),
        ("2003-01-01", "2006-12-31"),
        ("2017-01-01", "2020-01-31"),
        ("2021-01-01", "2021-12-31"),
    ],
    columns=["start", "end"],
)
BOOMS["start"] = pd.to_datetime(BOOMS["start"])
BOOMS["end"] = pd.to_datetime(BOOMS["end"])


def clip_bands(bands, lo, hi):
    # keep only bands inside the chart window and trim the edges
    b = bands[(bands["end"] >= lo) & (bands["start"] <= hi)].copy()
    b["start"] = b["start"].clip(lower=lo)
    b["end"] = b["end"].clip(upper=hi)
    return b

@st.cache_data(ttl=86400)
def get_recessions():
    # USREC is 1 during a recession month and 0 otherwise
    flag = fred.get_series("USREC").dropna().astype(int)
    starts = flag.index[(flag == 1) & (flag.shift(1, fill_value=0) == 0)]
    ends = flag.index[(flag == 1) & (flag.shift(-1, fill_value=0) == 0)]
    return pd.DataFrame({"start": starts, "end": ends + pd.offsets.MonthEnd(0)})


def make_chart(series):
    df = series.reset_index()
    df.columns = ["date", "value"]
    lo, hi = df["date"].min(), df["date"].max()

    recs = clip_bands(get_recessions(), lo, hi)
    booms = clip_bands(BOOMS, lo, hi)

    red = (
        alt.Chart(recs)
        .mark_rect(color="red", opacity=0.2)
        .encode(x="start:T", x2="end:T")
    )
    green = (
        alt.Chart(booms)
        .mark_rect(color="green", opacity=0.2)
        .encode(x="start:T", x2="end:T")
    )
    line = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("value:Q", title=None, scale=alt.Scale(zero=False)),
            tooltip=["date:T", "value:Q"],
        )
    )
    return (green + red + line).properties(height=350)

INDICATORS = {
    "Unemployment rate (%)": {
        "id": "UNRATE",
        "explain": "The unemployment rate measures the share of people who want a job and are looking for one but can't find it. It does not compare everyone who has a job with everyone who doesn't. It only counts people who are in the labor force at the moment. Economists use it to read the economy: a rising rate means companies are hiring less and more workers can't find jobs, while a falling rate points to growing companies and open positions. In the early 90s, unemployment peaked at about 7.8%, the third highest peak in the last 40 years. Several factors caused this, but the biggest were the Fed raising interest rates and the savings and loan crisis. Inflation was rising in the late 80s, so the Fed raised rates to bring it down. That slowed the economy right before 1990 and set the stage for a spike in unemployment. At the same time, hundreds of lenders failed after making risky real estate loans, and the surviving banks tightened lending and only served the most creditworthy businesses. When businesses can't borrow, they can't expand, and they often have to let workers go. Unemployment kept climbing and the economy stayed weak through the early years of the decade. In the late 2000s, unemployment hit 10%, the second highest peak in the last 40 years. Home prices soared, and banks gave subprime mortgages to risky borrowers, then bundled those loans into investments and sold them across the global financial system. When prices peaked around 2006 and started falling, borrowers defaulted and those investments lost value. The collapse of Lehman Brothers in 2008 made banks stop lending to each other and to businesses. Families felt poorer and cut spending, so companies laid off workers, especially in construction, manufacturing, retail, and finance. Unemployment climbed from about 5% in late 2007 to a peak of 10% in October 2009, and it stayed high for years because the housing market and consumer spending recovered slowly. Unlike the early 90s, which came mostly from Fed rate hikes and outside shocks, this crisis came from a breakdown inside the financial system itself. Unemployment spiked again in early 2020, when COVID-19 shutdowns and people's fear of getting sick emptied restaurants, hotels, airlines, and retail stores almost overnight. Those businesses laid off or furloughed workers fast, school and daycare closures pushed many parents, especially mothers, out of work, and uncertainty made companies stop hiring. The rate went from 3.5% in February 2020 to 14.8% in April, the highest since tracking began in 1948, with about 20 million jobs lost in a single month. It fell quickly because many layoffs were temporary and the CARES Act supported businesses and households. As vaccines rolled out, the rate dropped to roughly 3.9% by the end of 2021. Compared to the early 90s (Fed rate hikes and outside shocks) and 2008 (a financial system breakdown), this was a deliberate shutdown, so it was the fastest jump ever but also a much faster recovery.",
    },
    "Fed funds rate (%)": {
        "id": "FEDFUNDS",
        "explain": "The federal funds rate is the interest rate the Federal Reserve steers, and it's the rate banks charge each other for overnight loans. It matters because it sets the tone for borrowing costs across the whole economy, including car loans, mortgages, credit cards, and business loans. The Fed raises it to cool spending and fight inflation, and lowers it to encourage borrowing and spending when the economy is weak. In the late 80s, the rate climbed to a peak of nearly 10% in 1989, the highest point on the graph. Inflation was rising, so the Fed kept pushing rates up to slow the economy down. That made borrowing expensive for families and businesses, helped pop the real estate bubble behind the savings and loan crisis, and set the stage for the early 90s recession. Once unemployment started rising, the Fed reversed course and cut rates all the way down to about 3% by 1992 to get people borrowing and spending again. The rate stayed low for a couple of years, then rose back to around 6% by 1995 as the economy recovered. In the early 2000s, the Fed cut rates sharply, from about 6.5% in 2000 to around 1% by 2003, after the dot-com bust and the 2001 recession. Those very low rates made mortgages cheap and helped fuel the housing boom, so home prices soared and banks handed out risky loans. The Fed then raised rates step by step to about 5.25% by 2006, which made adjustable mortgages more expensive, pushed more borrowers into default, and helped pop the bubble. When the financial crisis hit in 2008, the Fed slashed the rate to nearly zero by the end of the year, and it stayed there until late 2015 to help the slow recovery. Unemployment peaked at 10% in 2009, and the near zero rate was the Fed's main tool for bringing it back down. After 2015, the rate slowly crept up to about 2.4% in 2019, then dropped back to nearly zero in March 2020 when COVID-19 shut down the economy. The Fed held it there through 2021 while unemployment fell from its 14.8% spike. Then inflation surged as the economy reopened, so the Fed raised rates faster than at any point since the 80s, from nearly zero in early 2022 to about 5.3% by 2023. It held there through 2024 to bring prices under control, then began cutting, and the rate now sits at roughly 3.7%. Looking at the whole graph, the pattern is the same every time: the Fed raises rates when inflation or bubbles are the danger, cuts them when unemployment and recessions are the danger, and the timing of those moves has a big effect on how many people have jobs.",
    },
    "Consumer Price Index": {
        "id": "CPIAUCSL",
        "explain": "The Consumer Price Index, or CPI, is the main measure of inflation, and it tracks how the prices of everyday things like food, gas, rent, and clothes change over time. The graph compares each month to the same month a year earlier, so a reading of 3 means prices are 3 percent higher than they were a year ago. It matters because when prices rise faster than paychecks, your money buys less, and it's the number the Fed watches when it decides whether to raise or cut interest rates. In the late 80s, inflation crept up from about 4% to over 5%, which is why the Fed was pushing rates toward 10% in 1989. Then the oil price spike from Iraq's invasion of Kuwait pushed inflation to a peak of about 6.3% in late 1990. The recession cooled demand, and inflation fell back to about 3% by 1992, which gave the Fed room to cut rates and help the economy recover. Through the rest of the 90s, inflation stayed calm at around 2 to 3%, and it dipped to about 1.5% in 1998. In the early 2000s, inflation stayed low, sinking to about 1.2% in 2002 after the dot-com bust, which is part of why the Fed felt safe holding rates near 1% and fueling the housing boom. It rose to around 4.7% in 2005 and then jumped to about 5.5% in mid 2008 as oil prices spiked. Then the financial crisis hit, spending collapsed, and prices actually fell, with inflation dropping to about negative 2% in 2009. Negative inflation, called deflation, is dangerous because people delay purchases waiting for lower prices, which hurts businesses and jobs even more, and that's a big reason the Fed held rates near zero for years. For most of the 2010s, inflation stayed low at around 1 to 2.5%, and it fell close to zero again in spring 2020 when COVID-19 shut the economy down. Then came the biggest surge on the graph. As the economy reopened, demand came roaring back while supply chains were still broken, stimulus money was in people's pockets, and energy prices jumped after Russia invaded Ukraine, so inflation climbed to about 9% in mid 2022. That is why the Fed raised rates faster than at any point since the 80s. Inflation came back down to about 3% by 2023 and has hovered around 3% since, though it ticked up to about 4.3% earlier this year and now sits at roughly 3.7%, still above the Fed's 2% goal. Put the three graphs together and you can see the full cycle: high inflation pushes the Fed to raise rates, higher rates slow the economy, and slower growth raises unemployment, while very low inflation or deflation pushes the Fed to cut rates to protect jobs.",
    },
    "Gas price ($ per gallon)": {
        "id": "GASREGW",
        "explain": "Gas prices show the weekly average price of regular gasoline in the US, and they matter because almost everyone feels them directly, since a jump of one dollar a gallon costs a typical driver hundreds of dollars a year. The graph starts at about 1.20 dollars per gallon in 1991 and ends near 4.50 dollars today, and the gray bars mark recessions, which makes it easy to see how gas and the economy move together. Through the 1990s prices were remarkably flat at around 1.00 to 1.30 dollars, which is part of why that decade felt cheap, and the small bump in 1991 came from the oil spike after Iraq invaded Kuwait. After 2000, prices began a long climb from about 1.50 dollars to over 3.00 dollars by 2006, as demand from fast-growing countries like China pushed oil higher. In mid 2008, gas peaked at about 4.10 dollars right as the recession started, which squeezed household budgets just when jobs were disappearing. Then it crashed to about 1.65 dollars by early 2009, because the recession killed demand for oil, so falling gas prices were a symptom of the weak economy rather than good news. Prices recovered to around 3.50 to 4.00 dollars in 2011 through 2014, then fell to about 2.00 dollars in 2016 when American shale drilling flooded the market with oil. The COVID-19 shutdown pushed prices down to about 1.80 dollars in 2020 because almost nobody was driving, then they shot up to a record of about 5.00 dollars in mid 2022 after Russia invaded Ukraine, which helped drive inflation to 9% that same summer. Prices settled around 3.00 to 3.50 dollars for a couple of years, but they have jumped again recently to about 4.50 dollars, which will likely push inflation back up and eat into paychecks. For a normal person, this is the price that shows up on a sign you see every day, so when it rises, you have less money left for groceries, rent, and savings, and when it falls, it works like a small raise. Put all seven graphs together and you can see the link to the rest of the economy: gas prices feed into inflation, inflation pushes the Fed to raise rates, and higher rates and costs slow hiring and raise unemployment.",
    },
    "Real GDP (billions, 2017 dollars)": {
        "id": "GDPC1",
        "explain": "The total value of everything the US produces, adjusted for inflation. It is the standard scoreboard for the whole economy.",
        "notes": "Write what you see here.",
    },
    "Jobs added (total nonfarm, thousands)": {
        "id": "PAYEMS",
        "explain": "Jobs added, officially called total nonfarm payrolls, is the total number of paid jobs in the US, not counting farms, and it comes from a survey of employers rather than households like the unemployment rate does. It matters because it shows the actual count of jobs in the economy, so you can see how many were lost in a downturn and how long it took to get them back. The graph starts at about 100 million jobs in 1987 and climbs to roughly 160 million today, so over the long run the economy keeps adding jobs, and the recessions show up as dips in the line. In the early 90s, the line flattened and slipped from about 110 million to around 108.5 million, a loss of roughly 1.5 million jobs, which is small on the graph but explains why unemployment kept rising even after the recession officially ended. After that, job growth was steady and strong through the late 90s, reaching about 130 million by September 1999. The dot-com bust and the 2001 recession caused a small dip from about 133 million to around 130 million, and it took until about 2005 to get back to the old peak. Then came the 2008 crisis, when jobs fell from about 138.8 million in early 2008 to about 130 million by 2010, roughly 8.7 million lost, and the line did not get back to its old peak until around 2014, which is why unemployment stayed so high for years. The 2020 drop is the sharpest cliff on the graph, with the line falling from about 152.5 million to about 130.5 million in just two months as COVID-19 shut down the economy. It also bounced back much faster than 2008, and total jobs passed the old peak around 2022. Looking at the right edge of the graph, the line has flattened out near 160 million since about 2024, which means hiring has slowed to a crawl even though the economy is not in a recession. Put the four graphs together and the story is clear: the Fed raises rates to fight inflation, borrowing slows, jobs get cut, and unemployment rises, and the jobs line shows that falling is fast but climbing back is slow.",
        "notes": "Write what you see here.",
    },
    "Initial jobless claims (weekly)": {
        "id": "ICSA",
        "explain": "Initial jobless claims count how many people filed for unemployment benefits for the first time in a given week, and it's one of the fastest warning signs of layoffs because it comes out every Thursday, while the unemployment rate only updates monthly. It matters because it shows trouble in real time: when companies start cutting workers, people file claims almost immediately, so a sustained rise often signals a slowdown before the other numbers catch up. For most of the graph, the line sits low and flat at roughly 200,000 to 400,000 claims per week, which is what a normal, healthy job market looks like, with companies letting some workers go and hiring others every week. In the early 90s, claims rose to around 450,000 to 500,000 in 1991, matching the recession and the rise in unemployment. They crept up again around 2001 and 2002 after the dot-com bust, then jumped in 2008 and 2009 to a peak of about 650,000 per week, which lines up with the financial crisis and the 10% unemployment rate. That peak looks small on this graph, but only because of what happened next. In March 2020, claims exploded to over 6 million in a single week, roughly ten times the worst week of the 2008 crisis, as COVID-19 shutdowns forced businesses to lay off workers almost overnight. This is the same moment the jobs graph fell off a cliff and the unemployment rate hit 14.8%. The spike also faded quickly, with claims dropping back below 1 million by late 2020 and returning to normal levels by 2022, which fits the pattern of temporary layoffs that bounced back once businesses reopened. On the right edge of the graph, claims are sitting at around 200,000 per week, which is low, so layoffs are not widespread right now even though hiring has slowed, a combination often called a low hire, low fire market. Put all five graphs together and you can see the full chain: inflation pushes the Fed to raise rates, businesses cut back, claims rise first, jobs fall next, and unemployment follows, so claims work as the early alarm for everything else.",
        "notes": "Write what you see here.",
    },
    "Core CPI (no food or energy)": {
        "id": "CPILFESL",
        "explain": "Core CPI is the same inflation measure as the earlier graph, but with food and energy stripped out, because those prices bounce around a lot from things like weather, wars, and oil markets. It matters because economists and the Fed use it to see the underlying trend in prices, the part that tends to stick around instead of disappearing next month. The graph compares each month to the same month a year earlier, and the gray bars mark recessions. In the late 80s, core inflation crept up from about 4% to nearly 5%, then peaked near 5.6% around the 1990 to 1991 recession, which fits the Fed pushing rates close to 10% back then. After that it fell steadily, reaching about 3% in the mid 90s and about 2% by 1999, which is part of why that decade felt stable. It stayed close to 2.5% through the 2001 recession, then dropped to about 1.1% in 2004, a very low reading that helped the Fed feel safe keeping rates near 1% and feeding the housing boom. It rose to about 2.9% in 2006, then sank after the 2008 crisis to about 0.6% in late 2010, which shows how weak demand pulled prices down even without gas and food in the mix. Through the 2010s it hovered around 1.5% to 2.3%, right around the Fed's 2% goal. In 2020 it dipped to about 1.2% during the COVID-19 shutdown, then exploded to about 6.6% in 2022 as demand returned, supply chains were jammed, and stimulus money was flowing. Here is the key comparison with the earlier inflation graph: headline inflation hit about 9% in 2022, but core peaked lower, which tells you gas and food were adding a lot of the pain at the time. The same thing is happening now, since core sits at about 2.8% while headline is around 3.7%, which means the recent jump in gas prices is a big reason overall inflation looks higher. For a normal person, core inflation is the better clue to whether your rent, car repairs, insurance, and everyday services will keep getting more expensive, since those prices rarely come back down once they rise. Gas and groceries can swing up and down, but core tells you whether your cost of living is steadily creeping higher. Put all eight graphs together and you can see the link: energy shocks and strong demand push prices up, core inflation shows whether that pressure is spreading into the whole economy, and that decides whether the Fed keeps rates high and slows hiring.",
        "notes": "Write what you see here.",
    },
    "10 year Treasury yield (%)": {
        "id": "DGS10",
        "explain": "The 10 year Treasury yield is the interest rate the US government pays to borrow money for 10 years, and it matters because it sets the tone for long-term borrowing costs everywhere, especially mortgage rates, and it shows what investors expect for the economy ahead. The graph starts at about 7.5% in 1987 and ends near 5.3% today, and the gray bars mark recessions. In the late 80s it climbed to a peak of about 10% in 1987 and stayed around 8 to 9% through 1989, when inflation was rising and the Fed was pushing rates toward 10%, which is why borrowing was so expensive back then. It then fell steadily through the 90s, dipping to about 5.3% in 1993 and bouncing to about 8% in 1994 when the Fed hiked rates again. Through the late 90s and early 2000s it drifted down to about 4.5% as inflation stayed calm, and it landed near 4% after the 2001 recession. It held at about 4 to 5% through 2007, then dropped to roughly 2.2% in late 2008 as scared investors piled into safe government bonds during the financial crisis, which is a pattern worth remembering: yields fall when people fear a recession. It stayed low for years, sinking to about 1.5% in 2012 and 2016 while the Fed held rates near zero. In 2020 it crashed to about 0.5%, the lowest on the graph, as COVID-19 shut down the economy. Then it shot back up as inflation hit 9%, passing 4% in 2023 and settling around 4 to 4.5% for a couple of years. It has now climbed to about 5.3%, the highest in nearly two decades, which tells you investors expect inflation to stay sticky and the government to keep borrowing heavily. For a normal person, this is the number that moves your mortgage rate, car loan, and student loan costs, so when it rises, a house costs hundreds more per month and fewer people can afford to buy, and when it falls, borrowing gets cheaper and refinancing becomes possible. It also affects savers, since higher yields mean better returns on safe things like savings accounts and bonds. Put all ten graphs together and you can see the chain: inflation pushes the Fed to raise rates, the 10 year yield rises with it, borrowing gets pricier, and hiring slows and unemployment rises.",
        "notes": "Write what you see here.",
    },
    "Yield curve (10 year minus 2 year, %)": {
        "id": "T10Y2Y",
        "explain": "The yield curve here is the 10 year Treasury yield minus the 2 year yield, and it matters because when it drops below zero, short term borrowing costs more than long term borrowing, which is unusual and has come before most recent recessions. Normally lenders want more interest for tying up money longer, so the line sits above zero, but when investors expect a weak economy ahead, they rush into long term bonds, push those yields down, and the line sinks. The graph starts at about 1.2 in 1987, and the gray bars mark recessions. It dipped below zero in 1989, bottoming near negative 0.4, right as the Fed pushed rates close to 10%, and the early 90s recession followed in 1990. After that it shot up to about 2.6 by 1992 as the Fed cut rates to rescue the economy, then slid back toward zero through the late 90s. It went negative again in 2000, dropping to about negative 0.5, and the 2001 recession arrived within the year. It then climbed to about 2.7 by 2003 and fell back to roughly zero by 2006 and 2007, just before the 2008 crisis. After that it jumped to nearly 3.0 in 2010 as the Fed held short rates near zero, then drifted down through the 2010s, hovering near zero in 2019 right before the COVID-19 recession in 2020. The most striking part is 2022 to 2024, when it fell to about negative 1.0, the deepest dip on the graph, as the Fed raised rates at the fastest pace since the 80s. That was the longest stretch below zero in the data, and the recession many people expected never clearly showed up, so the signal was not perfect this time. It has since moved back above zero and now sits around 0.3, which means the warning has cleared for now, though the curve is still flat. For a normal person, a negative yield curve is an early warning light, since banks make less money lending when short rates are high, so they tighten credit, and that makes loans harder to get and slows hiring months later. It does not mean a recession is guaranteed, but it is a good moment to build a cash cushion, avoid taking on big new debt, and keep your resume current. Put all eleven graphs together and you can see the chain: inflation pushes the Fed to raise rates, the yield curve flips as markets expect trouble, borrowing gets pricier, and hiring slows and unemployment rises.",
        "notes": "Write what you see here.",
    },
    "Home prices (Case-Shiller index)": {
        "id": "CSUSHPINSA",
        "explain": "Tracks the price of homes across the US. Look closely at 2006 to 2012 to see the housing crash.",
        "notes": "Write what you see here.",
    },
    "Housing starts (thousands)": {
        "id": "HOUST",
        "explain": "How many new homes builders began building. Builders pull back fast when borrowing gets expensive.",
        "notes": "Write what you see here.",
    },
    "Retail sales (millions $)": {
        "id": "RSAFS",
        "explain": "Total sales at stores and online. Since people's spending is most of the economy, this shows how confident shoppers are.",
        "notes": "Write what you see here.",
    },
    "Oil price (WTI, $ per barrel)": {
        "id": "DCOILWTICO",
        "explain": "Oil price per barrel shows the price of US crude oil (WTI, the benchmark traded in the US), and it matters because it is the raw ingredient behind gas, diesel, jet fuel, and plastics, so swings here ripple through almost everything you buy. The graph starts at about 15 dollars a barrel in 1987, and the gray bars mark recessions, which shows how often oil spikes show up right before or during downturns. Through most of the 1990s oil sat at a calm 15 to 25 dollars, with one brief jump to about 40 dollars in 1990 after Iraq invaded Kuwait, right before the early 90s recession. After 2000, oil began a huge climb from about 25 dollars to roughly 145 dollars in mid 2008, as demand from fast-growing countries like China outran supply. That peak landed right as the financial crisis began, which squeezed families and businesses just before the crash. Oil then collapsed to about 32 dollars by early 2009 because the recession killed demand, which matches the gas price drop you saw earlier. It recovered to around 100 dollars for most of 2011 through 2014, then fell to about 27 dollars in 2016 when American shale drilling flooded the market. The most dramatic moment is spring 2020, when oil briefly went negative, to about negative 37 dollars, because COVID-19 shutdowns left almost nobody driving or flying and storage was full, so sellers were paying buyers to take it. It then rebounded to about 120 dollars in 2022 after Russia invaded Ukraine, which drove the record gas prices and the 9% inflation of that summer. Prices settled between 60 and 90 dollars for a few years, but they have jumped again recently to around 100 dollars, which explains why gas is back near 4.50 dollars. For a normal person anywhere in the country, oil is the first domino: when it rises, gas, flights, shipping, and grocery prices follow within weeks, so your paycheck buys less, and when it falls, it works like a small raise. The effect is not the same everywhere, though, since high oil prices hurt commuters, truckers, and anyone with a long drive, while boosting jobs and income in energy states like Texas, North Dakota, and New Mexico. Put all nine graphs together and you can see the chain: oil prices push gas and inflation, inflation pushes the Fed to raise rates, and higher rates and costs slow hiring and raise unemployment.",
        "notes": "Write what you see here.",
    },
    "Personal savings rate (%)": {
        "id": "PSAVERT",
        "explain": "The share of income people keep instead of spending. It shot up in 2020 when stimulus money arrived and stores were closed.",
        "notes": "Write what you see here.",
    },
    "Average hourly earnings ($)": {
        "id": "CES0500000003",
        "explain": "Average hourly earnings is the average pay per hour for private sector workers, and it matters because it shows whether paychecks are growing, but the real test is comparing it to inflation, since a raise only helps if prices don't rise faster. The graph starts at about 20 dollars per hour in 2007 and climbs to roughly 38 dollars today, which is nearly double over about 19 years. For most of the time the line rises in a smooth, steady slope, because wages are sticky: employers rarely cut pay, so even in bad times earnings keep inching up instead of falling. Through the 2008 crisis, the line barely bends, even though unemployment hit 10%, because the workers who lost their jobs were the ones who disappeared from the data while those who stayed kept getting small raises. Growth stayed slow through the 2010s, going from about 22.50 in 2010 to about 28 dollars by 2019, roughly 2 to 3% a year, which was only a little above the low inflation of those years. The small spike in early 2020 looks like a raise, but it is actually a statistical illusion. The workers laid off in March and April were mostly low-wage jobs in restaurants, hotels, and retail, so when they dropped out of the data, the average jumped even though nobody got paid more. The line then settled back and resumed climbing as those workers returned. After 2021 the line gets a bit steeper, with earnings rising from about 30 dollars to about 38 in five years, as employers competed for workers in a tight job market. Here is the catch, though: inflation hit about 9% in 2022 while wages were growing only around 4 to 5% a year, so for a while prices rose faster than paychecks and workers lost buying power, even though the line looks like it is going up. Wage growth has since beaten inflation in some stretches, but with inflation still around 3.7%, it is worth comparing the two lines closely. Put all six graphs together and you can see how the economy fits: inflation pushes the Fed to raise rates, jobs and hiring slow, claims rise as an early warning, unemployment goes up, and wages tell you whether regular people are actually coming out ahead.",
        "notes": "Write what you see here.",
    },
    "Federal debt (% of GDP)": {
        "id": "GFDEGDQ188S",
        "explain": "How much the US government owes compared to the size of the economy. Using a percent of GDP makes it fair across decades.",
        "notes": "Write what you see here.",
    },
    "Dollar strength (broad index)": {
        "id": "DTWEXBGS",
        "explain": "How strong the US dollar is against other major currencies. A strong dollar makes imports cheaper and US exports pricier abroad.",
        "notes": "Write what you see here.",
    },
    "Texas jobs (thousands)": {
        "id": "TXNA",
        "explain": "Total jobs in Texas. Compare it to the national chart to see how Texas does in booms and busts.",
        "notes": "Write what you see here.",
    },
    "Money supply (M2, billions $)": {
        "id": "M2SL",
        "explain": "The money supply (M2) is the total amount of cash, checking deposits, savings accounts, and similar easy to access money in the economy, and the jump in 2020 and 2021 is the most unusual stretch on the graph. Over about two years, the line shot up from roughly 15.5 trillion dollars to about 21.8 trillion, growing around 40%, which is faster than anything else in the data. Several things caused it at once: stimulus checks, extra unemployment benefits, and business loans put cash directly into people's accounts, while the Fed pumped money into the financial system and cut rates to near zero to keep the economy alive during COVID-19. At the same time, shutdowns meant people could not spend on travel, restaurants, and events, so a lot of that money piled up in savings instead of being spent. When the economy reopened, all that cash chased a limited supply of goods, since supply chains were still jammed, and that is a big reason inflation climbed to about 9% in 2022. For a normal person, this is why prices jumped so fast in those years: there was suddenly much more money in the economy, so each dollar bought less, and paychecks took a while to catch up. It also explains why the Fed raised rates so aggressively afterward, which made car loans, mortgages, and credit cards much more expensive. The lesson is that when the supply of money grows much faster than the supply of things to buy, everyday costs tend to rise, and savings sitting in an account that pays less than inflation quietly lose buying power.",
        "notes": "Write what you see here.",
    },
}

CATEGORIES = {
    "Jobs and wages": ["UNRATE", "PAYEMS", "ICSA", "CES0500000003"],
    "Prices and inflation": ["CPIAUCSL", "CPILFESL", "GASREGW", "DCOILWTICO"],
    "Interest rates and money": ["FEDFUNDS", "DGS10", "T10Y2Y", "MORTGAGE30US", "M2SL"],
    "Growth and spending": ["GDPC1", "RSAFS", "UMCSENT", "PSAVERT"],
    "Housing": ["CSUSHPINSA", "HOUST"],
    "Government and trade": ["GFDEGDQ188S", "DTWEXBGS"],
    "Texas": ["TXUR", "TXNA"],
}


@st.cache_data(ttl=86400)
def load(series_id):
    return fred.get_series(series_id).dropna()


st.title("US Economy Dashboard")
st.write("Real data from the Federal Reserve Bank of St. Louis (FRED).")

category = st.selectbox("Category", list(CATEGORIES))
options = [name for name, v in INDICATORS.items() if v["id"] in CATEGORIES[category]]
choice = st.selectbox("Pick an indicator", options)
years = st.slider("Years of history", 1, 40, 10)

info = INDICATORS[choice]
full = load(info["id"])
cutoff = full.index.max() - pd.DateOffset(years=years)
data = full[full.index >= cutoff]

st.subheader(choice)
latest = full.iloc[-1]
last_date = full.index[-1]
past = full[full.index <= last_date - pd.DateOffset(years=1)]

c1, c2, c3 = st.columns(3)
c1.metric("Latest value", f"{latest:,.2f}")
c2.metric("As of", last_date.strftime("%b %d, %Y"))
if len(past) > 0:
    c3.metric("Change vs 1 year ago", f"{latest - past.iloc[-1]:+,.2f}")
st.altair_chart(make_chart(data), use_container_width=True)
st.caption("Red bars are US recessions (dated by the NBER). Green bars are periods commonly called booms. The green ones are my own unofficial picks, not an official list.")
st.write(info["explain"])

if info["id"] in ("CPIAUCSL", "CPILFESL"):
    inflation = (full.pct_change(12) * 100).dropna()
    inflation = inflation[inflation.index >= cutoff]
    st.subheader("Inflation rate (year over year, %)")
    st.altair_chart(make_chart(inflation), use_container_width=True)
    st.write("This compares each month to the same month one year earlier. If it says 3, prices are 3 percent higher than a year ago.")