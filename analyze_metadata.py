#!/usr/bin/env python3
"""
DogSpeak Dataset Metadata Analysis
Analyzes the metadata.csv file to provide statistics on dog barks by breed and sex.
"""

import pandas as pd
import os
from collections import defaultdict

def analyze_dogspeak_metadata(csv_path):
    """
    Analyze the DogSpeak dataset metadata and provide comprehensive statistics.
    
    Args:
        csv_path (str): Path to the metadata.csv file
    
    Returns:
        dict: Analysis results
    """
    
    # Check if file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Metadata file not found: {csv_path}")
    
    print("🐕 DogSpeak Dataset Analysis")
    print("=" * 50)
    
    # Load the metadata
    print("Loading metadata...")
    df = pd.read_csv(csv_path)
    
    # Basic dataset info
    print(f"\n📊 Dataset Overview:")
    print(f"   Total audio files: {len(df):,}")
    print(f"   Columns: {', '.join(df.columns.tolist())}")
    
    # Breed analysis
    print(f"\n🐕‍🦺 Breed Distribution:")
    breed_counts = df['breed'].value_counts()
    for breed, count in breed_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {breed.capitalize()}: {count:,} files ({percentage:.1f}%)")
    
    # Sex analysis
    print(f"\n♂️♀️ Sex Distribution:")
    sex_counts = df['sex'].value_counts()
    for sex, count in sex_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {sex.capitalize()}: {count:,} files ({percentage:.1f}%)")
    
    # Breed x Sex cross-tabulation
    print(f"\n📈 Breed × Sex Breakdown:")
    breed_sex_crosstab = pd.crosstab(df['breed'], df['sex'], margins=True)
    print(breed_sex_crosstab)
    
    # Individual dog analysis
    print(f"\n🐕 Individual Dogs:")
    dog_counts = df['dog_id'].value_counts()
    print(f"   Total unique dogs: {len(dog_counts)}")
    print(f"   Files per dog (min/max/avg): {dog_counts.min()}/{dog_counts.max()}/{dog_counts.mean():.1f}")
    
    # Detailed breed and sex analysis
    print(f"\n🔍 Detailed Breed × Sex Analysis:")
    results = {}
    
    for breed in df['breed'].unique():
        breed_data = df[df['breed'] == breed]
        male_count = len(breed_data[breed_data['sex'] == 'male'])
        female_count = len(breed_data[breed_data['sex'] == 'female'])
        
        # Count unique dogs
        male_dogs = len(breed_data[breed_data['sex'] == 'male']['dog_id'].unique())
        female_dogs = len(breed_data[breed_data['sex'] == 'female']['dog_id'].unique())
        
        results[breed] = {
            'male_files': male_count,
            'female_files': female_count,
            'male_dogs': male_dogs,
            'female_dogs': female_dogs,
            'total_files': male_count + female_count,
            'total_dogs': male_dogs + female_dogs
        }
        
        print(f"\n   {breed.upper()}:")
        print(f"   ├─ Male: {male_count:,} files from {male_dogs} dogs")
        print(f"   ├─ Female: {female_count:,} files from {female_dogs} dogs")
        print(f"   └─ Total: {male_count + female_count:,} files from {male_dogs + female_dogs} dogs")
    
    # File naming pattern analysis
    print(f"\n📁 File Naming Patterns:")
    sample_files = df['filename'].head(5).tolist()
    print(f"   Sample filenames:")
    for filename in sample_files:
        print(f"   • {filename}")
    
    # Summary statistics
    print(f"\n📋 Summary Statistics:")
    total_dogs = len(df['dog_id'].unique())
    total_male_dogs = len(df[df['sex'] == 'male']['dog_id'].unique())
    total_female_dogs = len(df[df['sex'] == 'female']['dog_id'].unique())
    
    print(f"   • Total recordings: {len(df):,}")
    print(f"   • Total dogs: {total_dogs}")
    print(f"   • Male dogs: {total_male_dogs}")
    print(f"   • Female dogs: {total_female_dogs}")
    print(f"   • Breeds: {len(df['breed'].unique())} ({', '.join(sorted(df['breed'].unique()))})")
    print(f"   • Average recordings per dog: {len(df) / total_dogs:.1f}")
    
    return results

def main():
    """Main function to run the analysis."""
    
    # Path to metadata file
    metadata_path = "/Users/nika/Downloads/NMSML/DogSpeak_Dataset/metadata.csv"
    
    try:
        # Run analysis
        results = analyze_dogspeak_metadata(metadata_path)
        
        print(f"\n✅ Analysis completed successfully!")
        print(f"📈 Results saved in analysis results dictionary")
        
        # Optional: Save results to a summary file
        summary_path = "/Users/nika/Downloads/NMSML/dataset_summary.txt"
        print(f"\n💾 Saving summary to: {summary_path}")
        
        with open(summary_path, 'w') as f:
            f.write("DogSpeak Dataset Analysis Summary\n")
            f.write("=" * 40 + "\n\n")
            
            for breed, stats in results.items():
                f.write(f"{breed.upper()}:\n")
                f.write(f"  Male: {stats['male_files']:,} files from {stats['male_dogs']} dogs\n")
                f.write(f"  Female: {stats['female_files']:,} files from {stats['female_dogs']} dogs\n")
                f.write(f"  Total: {stats['total_files']:,} files from {stats['total_dogs']} dogs\n\n")
        
        print(f"📄 Summary saved to {summary_path}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
