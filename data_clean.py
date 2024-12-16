import pandas as pd

# Load the dataset
dataset_path = r"C:\Users\shahr\Documents\GitHub\MDB-FinalProject\dataset\jobs_filtered_sampled.csv"
df = pd.read_csv(dataset_path)

# Randomly sample 10,000 records
print("Randomly sampling 10,00 records...")
sampled_df = df.sample(n=1000, random_state=42).reset_index(drop=True)

# Save the reduced dataset to a new CSV file
output_path = r"C:\Users\shahr\Documents\GitHub\MDB-FinalProject\dataset\jobs_1k.csv"
sampled_df.to_csv(output_path, index=False)

print(f"Reduced dataset saved to: {output_path}")
