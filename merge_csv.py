
import pandas as pd

# Load the CSV files into pandas DataFrames
cpq_df = pd.read_csv('/Users/michaelnseula/code/dealermargins/enterprisequoting-C_GD_DealerMargin_Entity-1 (1).csv')
margins_df = pd.read_csv('/Users/michaelnseula/code/dealermargins/list-53ebba158ff57891258fef1e.csv')

# Drop duplicate DealerIDs, keeping the first one
margins_df.drop_duplicates(subset=['DealerID'], keep='first', inplace=True)

# Create a dictionary for faster lookup of margins
margins_dict = margins_df.set_index('DealerID').to_dict('index')

# Define the mapping between the columns
column_mapping = {
    'C_BaseBoat': 'BASE_BOAT',
    'C_Engine': 'ENGINE',
    'C_Options': 'OPTIONS',
    'C_Freight': 'FREIGHT',
    'C_Prep': 'PREP',
    'C_Volume': 'VOL_DISC'
}

# Iterate over the rows of the cpq_df DataFrame and update the columns
for index, row in cpq_df.iterrows():
    dealer_id = row['C_DealerId']
    series = row['C_Series']

    if dealer_id in margins_dict:
        dealer_margins = margins_dict[dealer_id]
        for cpq_col, margin_col_suffix in column_mapping.items():
            margin_col_name = f"{series}_{margin_col_suffix}"
            if margin_col_name in dealer_margins:
                cpq_df.loc[index, cpq_col] = dealer_margins[margin_col_name]

# Save the updated DataFrame to a new CSV file
cpq_df.to_csv('/Users/michaelnseula/code/dealermargins/enterprisequoting_updated.csv', index=False)

print('Successfully updated the file and saved it as enterprisequoting_updated.csv')
