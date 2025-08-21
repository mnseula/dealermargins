
import pandas as pd

margins_df = pd.read_csv('/Users/michaelnseula/code/dealermargins/list-53ebba158ff57891258fef1e.csv')
duplicates = margins_df[margins_df.duplicated(subset=['DealerID'], keep=False)]
print("Duplicate Dealer IDs and their corresponding rows:")
print(duplicates)
