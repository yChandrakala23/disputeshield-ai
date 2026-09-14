from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

from backend.config import DATA_DIR


def split_data():
    disputes_path = DATA_DIR / "disputes.csv"
    if not disputes_path.exists():
        from backend.data_gen import generate_all_datasets
        generate_all_datasets()
        
    df = pd.read_csv(disputes_path)
    
    # 1. Strict 3-Way Stratified Split: Train (60%), Validation (20%), Held-Out Test (20%)
    train_df, temp_df = train_test_split(
        df,
        test_size=0.40,
        random_state=42,
        stratify=df["outcome"]
    )
    
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=42,
        stratify=temp_df["outcome"]
    )
    
    train_df.to_csv(DATA_DIR / "train.csv", index=False)
    val_df.to_csv(DATA_DIR / "val.csv", index=False)
    test_df.to_csv(DATA_DIR / "test.csv", index=False)
    
    # 2. Temporal Time-Based Split (Train on oldest 75%, Test on newest 25%)
    if "created_at" in df.columns:
        df_sorted = df.sort_values(by="created_at").reset_index(drop=True)
        split_idx = int(len(df_sorted) * 0.75)
        train_temp = df_sorted.iloc[:split_idx]
        test_temp = df_sorted.iloc[split_idx:]
        
        train_temp.to_csv(DATA_DIR / "train_temporal.csv", index=False)
        test_temp.to_csv(DATA_DIR / "test_temporal.csv", index=False)

    print("Strict 3-Way Dataset splitting complete.")
    print(f"Total: {len(df)} | Train (60%): {len(train_df)} | Validation (20%): {len(val_df)} | Held-Out Test (20%): {len(test_df)}")


if __name__ == "__main__":
    split_data()