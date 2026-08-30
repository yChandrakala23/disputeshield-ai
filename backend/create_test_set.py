from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


df = pd.read_csv(
    DATA_DIR / "disputes.csv"
)


train_df, test_df = train_test_split(
    df,
    test_size=0.25,
    random_state=7,
    stratify=df["outcome"]
)


train_df.to_csv(
    DATA_DIR / "train.csv",
    index=False
)


test_df.to_csv(
    DATA_DIR / "test.csv",
    index=False
)


print("Dataset split complete.")
print("-----------------------")
print("Total:", len(df))
print("Training:", len(train_df))
print("Held-out test:", len(test_df))