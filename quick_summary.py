#!/usr/bin/env python3
"""
Simple DogSpeak Dataset Summary
Provides a quick overview of dog barks by breed and sex.
"""

import pandas as pd

def quick_summary():
    """Generate a quick summary of the DogSpeak dataset."""
    
    # Load the metadata
    df = pd.read_csv("/Users/nika/Downloads/NMSML/DogSpeak_Dataset/metadata.csv")
    
    print("🐕 DogSpeak Dataset: Male vs Female Barks by Breed")
    print("=" * 60)
    
    # Group by breed and sex, count files
    summary = df.groupby(['breed', 'sex']).size().unstack(fill_value=0)
    
    # Add totals
    summary['Total'] = summary.sum(axis=1)
    
    # Format and display
    print(f"{'Breed':<15} {'Male':<8} {'Female':<8} {'Total':<8}")
    print("-" * 40)
    
    for breed in summary.index:
        male = summary.loc[breed, 'male']
        female = summary.loc[breed, 'female'] 
        total = summary.loc[breed, 'Total']
        print(f"{breed.capitalize():<15} {male:<8,} {female:<8,} {total:<8,}")
    
    # Overall totals
    total_male = summary['male'].sum()
    total_female = summary['female'].sum()
    grand_total = summary['Total'].sum()
    
    print("-" * 40)
    print(f"{'TOTAL':<15} {total_male:<8,} {total_female:<8,} {grand_total:<8,}")
    
    print(f"\n📊 Quick Stats:")
    print(f"   • {len(df['breed'].unique())} breeds")
    print(f"   • {len(df['dog_id'].unique())} individual dogs")
    print(f"   • {len(df):,} total bark recordings")
    print(f"   • {(total_male/grand_total)*100:.1f}% male, {(total_female/grand_total)*100:.1f}% female")

if __name__ == "__main__":
    quick_summary()
