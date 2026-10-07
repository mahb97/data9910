# Q1
from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine("postgresql+psycopg2://postgres:admin@localhost:5432/telecommunications")
conn = engine.connect()

pd.read_sql(text("SELECT COUNT(*) AS n_customers FROM customers"), conn)

# Q2
from sqlalchemy import inspect
insp = inspect(engine)
for t in insp.get_table_names():
    print(t, [(c['name'], str(c['type'])) for c in insp.get_columns(t)])

# The database has four tables in the public schema.

# The first one is **customers** (phonenumber PK, contractstartdate, dob) which holds one row per customer, identified by phone number. It stores the contract start dob. 
# The second one is **calls** (connectionid PK, phonenumber FK, calltime, duration, callrate FK), which holds one row per call. Each call belongs to one customer through 
# phonenumber and has one rate through callrate. Duration is stored as a decimal, and calltime is stored as text ('VARCHAR(16)). The third one is **call_rates** (callrate PK, 
# isinternational, isroaming, costperminute), which is a lookup table of four rates, one for each combination of international and roaming. Each rate has a cost per minute. 
# The last one is **customer_service** (connectionid PK and FK), this one only holds connection IDs. It marks which calls were made to customer service and its primary key is also 
# a foreign key to calls, so each call appears at most once, which makes it an optional one-to-one extension of calls.

# Relationships:
# One customer has many calls (customers 1 to many calls)
# One call rate applies to many calls (call_rates 1 to many calls)
# A call may be flagged as a customer service call (calls 1 to 0 or 1 customer_service)

# Q3
# a)
pd.read_sql(text("SELECT COUNT(*) AS n_customers FROM customers"), conn)

# b)
customeryears = pd.read_sql(text("""
    SELECT EXTRACT(YEAR FROM dob)::int AS birth_year,
           COUNT(*) AS n_customers
    FROM customers
    GROUP BY birth_year
    ORDER BY birth_year DESC
"""), conn)
customeryears

customeryears["n_customers"].sum()

pip install matplotlib

customeryears.sort_values("birth_year").plot(x="birth_year", y="n_customers", kind="bar", figsize=(12,4), legend=False, title="Customers by birth year")

# Q3 d)
# test
pd.read_sql(text("SELECT MIN(duration), MAX(duration), AVG(duration) FROM calls"), conn)
# duration is stored in seconds while the rate is per minute, and thus duration was divided by 60.

repaired_sql = """
    SELECT c.phonenumber,
           ROUND(SUM(r.costperminute * c.duration / 60.0), 2) AS total_amount_spent
    FROM calls c
    JOIN call_rates r ON c.callrate = r.callrate
    WHERE c.connectionid NOT IN (SELECT connectionid FROM customer_service)
    GROUP BY c.phonenumber
    ORDER BY c.phonenumber
"""
repair = pd.read_sql(text(repaired_sql), conn)
repair["total_amount_spent"] = repair["total_amount_spent"].astype(float)
repair.head(10)

# e)
repair["total_amount_spent"].agg(["min", "max", "mean"]).round(2)
repair.style.format({"total_amount_spent": "€{:.2f}"})

# Q4
len(numofcalls)    
numofcalls["support_calls"].sum()  
numofcalls.head(3)

numofcalls_all = pd.read_sql(text("""
    SELECT cu.phonenumber,
           COUNT(cs.connectionid) AS support_calls
    FROM customers cu
    LEFT JOIN calls c ON c.phonenumber = cu.phonenumber
    LEFT JOIN customer_service cs ON cs.connectionid = c.connectionid
    GROUP BY cu.phonenumber
    ORDER BY support_calls DESC, cu.phonenumber
"""), conn)
len(numofcalls_all)

# e)
callsbyrate = pd.read_sql(text("""
    SELECT c.callrate,
           r.isinternational,
           r.isroaming,
           r.costperminute,
           COUNT(*) AS n_calls
    FROM calls c
    JOIN call_rates r ON c.callrate = r.callrate
    GROUP BY c.callrate, r.isinternational, r.isroaming, r.costperminute
    ORDER BY c.callrate
"""), conn)
callsbyrate["costperminute"] = callsbyrate["costperminute"].astype(float)
callsbyrate

# report
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False})

# headline table
total_customers = pd.read_sql(text("SELECT COUNT(*) FROM customers"), conn).iloc[0, 0]
total_calls = pd.read_sql(text("SELECT COUNT(*) FROM calls"), conn).iloc[0, 0]
support_calls = pd.read_sql(text("SELECT COUNT(*) FROM customer_service"), conn).iloc[0, 0]

summary = pd.DataFrame({
    "Metric": ["Customers", "Total calls", "Calls to customer service", "Share of calls to customer service",
               "Numbers with non-support calls", "Revenue per number: min", "Revenue per number: median",
               "Revenue per number: mean", "Revenue per number: max", "Total revenue (excl. support calls)"],
    "Value": [f"{total_customers:,}", f"{total_calls:,}", f"{support_calls:,}", f"{support_calls/total_calls:.1%}",
              f"{len(repair):,}", f"{repair.total_amount_spent.min():.2f}", f"{repair.total_amount_spent.median():.2f}",
              f"{repair.total_amount_spent.mean():.2f}", f"{repair.total_amount_spent.max():.2f}",
              f"{repair.total_amount_spent.sum():,.2f}"]
})
summary

# revenue concentration
s = repair.total_amount_spent.sort_values(ascending=False)
top10 = s.head(len(s) // 10).sum() / s.sum()
top1 = s.head(len(s) // 100).sum() / s.sum()
print(f"Top 10% of numbers generate {top10:.1%} of revenue; top 1% generate {top1:.1%}")

# figs
fig, ax = plt.subplots(2, 3, figsize=(16, 8))

customeryears.sort_values("birth_year").plot(x="birth_year", y="n_customers", kind="bar", ax=ax[0, 0], legend=False, width=0.9)
ax[0, 0].set(title="Customers by birth year", xlabel="Birth year", ylabel="Customers")
ax[0, 0].set_xticks(range(0, len(customeryears), 5)); ax[0, 0].set_xticklabels(sorted(customeryears.birth_year)[::5], rotation=45)

ax[0, 1].hist(repair.total_amount_spent, bins=40)
ax[0, 1].axvline(repair.total_amount_spent.mean(), color="k", ls="--", label="mean")
ax[0, 1].set(title="Revenue per phone number", xlabel="Total spent", ylabel="Phone numbers"); ax[0, 1].legend()

ax[0, 2].hist(moreinfo.avg_duration_minutes, bins=40)
ax[0, 2].set(title="Average call duration per number", xlabel="Minutes", ylabel="Phone numbers")

ax[1, 0].bar(by_rate.callrate.astype(str), by_rate.n_calls)
ax[1, 0].set(title="Calls by call rate", xlabel="Call rate", ylabel="Calls")

ax[1, 1].bar(by_rate.callrate.astype(str), by_rate.revenue, color="tab:green")
ax[1, 1].set(title="Revenue by call rate", xlabel="Call rate", ylabel="Revenue")

ax[1, 2].hist(numofcalls.support_calls, bins=range(1, numofcalls.support_calls.max() + 2), align="left")
ax[1, 2].set(title="Customer service calls per number", xlabel="Support calls", ylabel="Phone numbers")

plt.tight_layout()
plt.savefig("report_figures.png", dpi=150)
plt.show()
