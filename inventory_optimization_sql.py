# Inventory Optimization with SQL + Linear Programming (PuLP)
# Author: Gargi Jethe
# GitHub Project for OMP Consulting Role

import sqlite3
import pulp

# --------------------------
# Step 1: Create SQLite Database
# --------------------------
conn = sqlite3.connect("supply_chain.db")
cursor = conn.cursor()

# Drop tables if they exist (for re-runs)
cursor.execute("DROP TABLE IF EXISTS warehouses")
cursor.execute("DROP TABLE IF EXISTS customers")
cursor.execute("DROP TABLE IF EXISTS costs")

# Create tables
cursor.execute("""
CREATE TABLE warehouses (
    name TEXT PRIMARY KEY,
    supply INTEGER
)
""")

cursor.execute("""
CREATE TABLE customers (
    name TEXT PRIMARY KEY,
    demand INTEGER
)
""")

cursor.execute("""
CREATE TABLE costs (
    warehouse TEXT,
    customer TEXT,
    cost INTEGER,
    PRIMARY KEY (warehouse, customer)
)
""")

# Insert sample data
warehouses_data = [("W1", 80), ("W2", 70)]
customers_data = [("C1", 40), ("C2", 50), ("C3", 60)]
costs_data = [
    ("W1", "C1", 2), ("W1", "C2", 4), ("W1", "C3", 5),
    ("W2", "C1", 3), ("W2", "C2", 1), ("W2", "C3", 7)
]

cursor.executemany("INSERT INTO warehouses VALUES (?,?)", warehouses_data)
cursor.executemany("INSERT INTO customers VALUES (?,?)", customers_data)
cursor.executemany("INSERT INTO costs VALUES (?,?,?)", costs_data)

conn.commit()

# --------------------------
# Step 2: Load Data from SQL
# --------------------------
warehouses = [row[0] for row in cursor.execute("SELECT name FROM warehouses")]
supply = {row[0]: row[1] for row in cursor.execute("SELECT * FROM warehouses")}

customers = [row[0] for row in cursor.execute("SELECT name FROM customers")]
demand = {row[0]: row[1] for row in cursor.execute("SELECT * FROM customers")}

costs = {}
for row in cursor.execute("SELECT * FROM costs"):
    costs[(row[0], row[1])] = row[2]

# --------------------------
# Step 3: Optimization Model
# --------------------------
model = pulp.LpProblem("Inventory_Optimization_SQL", pulp.LpMinimize)

# Decision variables
x = pulp.LpVariable.dicts("ship", (warehouses, customers), lowBound=0, cat="Integer")

# Objective: Minimize total cost
model += pulp.lpSum([costs[(i, j)] * x[i][j] for i in warehouses for j in customers])

# Constraints: Supply capacity
for i in warehouses:
    model += pulp.lpSum([x[i][j] for j in customers]) <= supply[i]

# Constraints: Demand requirements
for j in customers:
    model += pulp.lpSum([x[i][j] for i in warehouses]) >= demand[j]

# Solve
model.solve(pulp.PULP_CBC_CMD(msg=0))

# --------------------------
# Step 4: Display Results
# --------------------------
print("Status:", pulp.LpStatus[model.status])
print("Total Cost = ", pulp.value(model.objective))

print("\nOptimal Shipping Plan:")
for i in warehouses:
    for j in customers:
        if x[i][j].value() > 0:
            print(f"Ship {x[i][j].value()} units from {i} to {j}")

# Close DB
conn.close()
