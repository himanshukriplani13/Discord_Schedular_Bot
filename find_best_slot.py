import pandas as pd
from collections import Counter

# Load CSV
df = pd.read_csv("availability_submissions.csv")

# Debug: Show raw headers
print("\n🧪 Raw headers:", df.columns.tolist())

# Clean & force rename
df.columns = df.columns.str.strip().str.lower()
print("🧼 Cleaned headers:", df.columns.tolist())

# Make sure 'time' exists
if "time" not in df.columns:
    raise ValueError("⚠️ No 'time' column found in CSV after cleanup.")

# Count times
time_counts = Counter(df["time"])

# Output
print("\n📊 Time Slot Popularity:")
for time, count in time_counts.most_common():
    print(f"{time}: {count} votes")

# Best time
if time_counts:
    best_time = time_counts.most_common(1)[0][0]
    print(f"\n✅ Best time slot is: {best_time}")
else:
    print("⚠️ No data available.")
