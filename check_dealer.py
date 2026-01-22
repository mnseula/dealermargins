import mysql.connector

# Database connection
conn = mysql.connector.connect(
    host="ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com",
    user="awsmaster",
    password="VWvHG9vfG23g7gD",
    database="warrantyparts"
)

cursor = conn.cursor()

# Search for Nichols
print("Searching for dealers matching 'Nichols'...")
cursor.execute("SELECT DealerID, Dealership FROM DealerMargins WHERE Dealership LIKE %s", ('%Nichols%',))
results = cursor.fetchall()

if results:
    print(f"\nFound {len(results)} dealer(s):")
    for dealer_id, dealership in results:
        print(f"  Dealer ID: {dealer_id} | Name: {dealership}")
else:
    print("\nNo dealers found matching 'Nichols'")
    print("\nShowing first 10 dealers in database:")
    cursor.execute("SELECT DealerID, Dealership FROM DealerMargins LIMIT 10")
    results = cursor.fetchall()
    for dealer_id, dealership in results:
        print(f"  {dealer_id} - {dealership}")

cursor.close()
conn.close()
