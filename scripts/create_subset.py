#!/usr/bin/env python3
"""
DogSpeak Dataset Subset Creator
Creates a balanced subset by selecting random dogs and their sound files from each breed.

Selection criteria:
- 10 random males + 10 random females per breed
- 3 random sound files per selected dog
- Copies files to a new 'subset' directory
"""

import pandas as pd
import numpy as np
import os
import shutil
from pathlib import Path
import random

def create_balanced_subset(metadata_path, audio_dir, output_dir, dogs_per_sex=10, files_per_dog=3, random_seed=42):
    """
    Create a balanced subset of the DogSpeak dataset.
    
    Args:
        metadata_path (str): Path to metadata.csv
        audio_dir (str): Directory containing the audio files
        output_dir (str): Directory to save the subset
        dogs_per_sex (int): Number of dogs to select per sex per breed (default: 10)
        files_per_dog (int): Number of audio files to sample per dog (default: 3)
        random_seed (int): Random seed for reproducibility (default: 42)
    
    Returns:
        dict: Summary of the subset creation
    """
    
    # Set random seed for reproducibility
    np.random.seed(random_seed)
    random.seed(random_seed)
    
    print("🐕 Creating DogSpeak Balanced Subset")
    print("=" * 50)
    print(f"Target: {dogs_per_sex} males + {dogs_per_sex} females per breed")
    print(f"Files per dog: {files_per_dog}")
    print(f"Random seed: {random_seed}")
    
    # Load metadata
    print(f"\n📊 Loading metadata from: {metadata_path}")
    df = pd.read_csv(metadata_path)
    
    # Create output directory structure
    output_path = Path(output_dir)
    audio_output = output_path
    audio_output.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_path}")
    
    # Initialize tracking variables
    subset_data = []
    selection_summary = {}
    total_files_copied = 0
    
    # Process each breed
    breeds = df['breed'].unique()
    print(f"\n🔍 Processing {len(breeds)} breeds: {', '.join(breeds)}")
    
    for breed in breeds:
        print(f"\n🐕‍🦺 Processing {breed.upper()}...")
        breed_data = df[df['breed'] == breed]
        
        # Get unique dogs by sex
        male_dogs = breed_data[breed_data['sex'] == 'male']['dog_id'].unique()
        female_dogs = breed_data[breed_data['sex'] == 'female']['dog_id'].unique()
        
        print(f"   Available: {len(male_dogs)} male dogs, {len(female_dogs)} female dogs")
        
        # Select random dogs (or all if fewer than requested)
        selected_males = np.random.choice(
            male_dogs, 
            size=min(dogs_per_sex, len(male_dogs)), 
            replace=False
        ).tolist()
        
        selected_females = np.random.choice(
            female_dogs, 
            size=min(dogs_per_sex, len(female_dogs)), 
            replace=False
        ).tolist()
        
        print(f"   Selected: {len(selected_males)} males, {len(selected_females)} females")
        
        # Track selection for this breed
        breed_summary = {
            'available_males': len(male_dogs),
            'available_females': len(female_dogs),
            'selected_males': len(selected_males),
            'selected_females': len(selected_females),
            'files_copied': 0
        }
        
        # Process selected dogs
        all_selected_dogs = selected_males + selected_females
        
        for dog_id in all_selected_dogs:
            # Get all files for this dog
            dog_files = breed_data[breed_data['dog_id'] == dog_id]
            
            # Select random files (or all if fewer than requested)
            selected_files = dog_files.sample(
                n=min(files_per_dog, len(dog_files)), 
                random_state=random_seed
            )
            
            # Copy files and update metadata
            for _, row in selected_files.iterrows():
                # Files are organized in folders by dog_id
                source_file = Path(audio_dir) / "dogspeak_released" / row['dog_id'] / row['filename']
                
                # Create breed/sex specific folder (e.g., husky_male, chihuahua_female)
                breed_sex_folder = f"{row['breed']}_{row['sex']}"
                breed_sex_dir = audio_output / breed_sex_folder
                breed_sex_dir.mkdir(exist_ok=True)
                
                dest_file = breed_sex_dir / row['filename']
                
                # Copy file if source exists
                if source_file.exists():
                    shutil.copy2(source_file, dest_file)
                    subset_data.append(row)
                    total_files_copied += 1
                    breed_summary['files_copied'] += 1
                else:
                    print(f"   ⚠️  Warning: Source file not found: {source_file}")
        
        selection_summary[breed] = breed_summary
        print(f"   ✅ Copied {breed_summary['files_copied']} files for {breed}")
    
    # Create new metadata file for subset
    subset_df = pd.DataFrame(subset_data)
    metadata_output = Path("data/exploration/metadata_subset.csv")
    subset_df.to_csv(metadata_output, index=False)
    
    # Create summary report
    summary_output = Path("data/exploration/subset_creation_report.txt")
    
    print(f"\n📋 Creating summary report...")
    with open(summary_output, 'w') as f:
        f.write("DogSpeak Dataset Subset Creation Report\n")
        f.write("=" * 45 + "\n\n")
        f.write(f"Creation Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Random Seed: {random_seed}\n")
        f.write(f"Target: {dogs_per_sex} males + {dogs_per_sex} females per breed\n")
        f.write(f"Files per dog: {files_per_dog}\n\n")
        
        f.write("BREED SELECTION SUMMARY:\n")
        f.write("-" * 25 + "\n")
        
        total_selected_males = 0
        total_selected_females = 0
        
        for breed, stats in selection_summary.items():
            f.write(f"\n{breed.upper()}:\n")
            f.write(f"  Available dogs: {stats['available_males']} males, {stats['available_females']} females\n")
            f.write(f"  Selected dogs: {stats['selected_males']} males, {stats['selected_females']} females\n")
            f.write(f"  Files copied: {stats['files_copied']}\n")
            
            total_selected_males += stats['selected_males']
            total_selected_females += stats['selected_females']
        
        f.write(f"\nTOTAL SUMMARY:\n")
        f.write(f"  Selected dogs: {total_selected_males} males + {total_selected_females} females = {total_selected_males + total_selected_females}\n")
        f.write(f"  Total files copied: {total_files_copied}\n")
        f.write(f"  Files per dog (average): {total_files_copied / (total_selected_males + total_selected_females):.1f}\n")
    
    # Display final summary
    print(f"\n✅ Subset creation completed!")
    print(f"📊 Summary:")
    print(f"   • Total dogs selected: {sum(s['selected_males'] + s['selected_females'] for s in selection_summary.values())}")
    print(f"   • Total files copied: {total_files_copied}")
    print(f"   • Metadata file: {metadata_output}")
    print(f"   • Audio files: {audio_output}")
    print(f"   • Report: {summary_output}")
    
    return {
        'total_files': total_files_copied,
        'total_dogs': sum(s['selected_males'] + s['selected_females'] for s in selection_summary.values()),
        'breed_summary': selection_summary,
        'output_path': output_path
    }

def main():
    """Main function to create the subset."""
    
    # Paths
    base_dir = "/Users/nika/Downloads/NMSML"
    metadata_path = f"{base_dir}/data/raw/DogSpeak_Dataset/metadata.csv"
    audio_dir = f"{base_dir}/data/raw/DogSpeak_Dataset"
    output_dir = f"{base_dir}/data/raw/subset"
    
    # Parameters
    DOGS_PER_SEX = 10  # males and females per breed
    FILES_PER_DOG = 3  # audio files per selected dog
    RANDOM_SEED = 42   # for reproducibility
    
    try:
        # Check if source files exist
        if not os.path.exists(metadata_path):
            print(f" Error: Metadata file not found: {metadata_path}")
            return 1
            
        if not os.path.exists(audio_dir):
            print(f" Error: Audio directory not found: {audio_dir}")
            return 1
        
        # Create subset
        results = create_balanced_subset(
            metadata_path=metadata_path,
            audio_dir=audio_dir, 
            output_dir=output_dir,
            dogs_per_sex=DOGS_PER_SEX,
            files_per_dog=FILES_PER_DOG,
            random_seed=RANDOM_SEED
        )
        
        print(f"\nSuccess! Balanced subset created with {results['total_files']} files from {results['total_dogs']} dogs.")
        
    except Exception as e:
        print(f"Error during subset creation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
