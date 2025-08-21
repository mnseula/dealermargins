
import pandas as pd

margins_df = pd.read_csv('/Users/michaelnseula/code/dealermargins/list-53ebba158ff57891258fef1e.csv')
duplicates = margins_df[margins_df.duplicated(subset=['DealerID'], keep=False)]

# Group by DealerID and aggregate the Dealership names
conflicts = duplicates.groupby('DealerID')['Dealership'].apply(list).reset_index()

print("Here are the conflicts I found:")
for index, row in conflicts.iterrows():
    print(f"DealerID: {row['DealerID']}")
    for dealership in row['Dealership']:
        print(f"  - {dealership}")
    print("-" * 20)
