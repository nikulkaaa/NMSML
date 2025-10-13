#!/bin/bash

# Script to process all audio files in DogSpeak_Subset with FFmpeg
# Converts all .wav files to standardized format: PCM 16-bit, 44.1kHz

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg is not installed. Installing via Homebrew..."
    brew install ffmpeg
fi

# Base directories
INPUT_DIR="/Users/nika/Downloads/NMSML/DogSpeak_Subset/audio_files"
OUTPUT_DIR="/Users/nika/Downloads/NMSML/DogSpeak_Subset_Processed/audio_files"

# Create output directory structure
mkdir -p "$OUTPUT_DIR"

# Counter for processed files
processed_count=0
total_files=0

# First, count total files
echo "Counting files..."
for folder in "$INPUT_DIR"/*; do
    if [ -d "$folder" ]; then
        folder_name=$(basename "$folder")
        for file in "$folder"/*.wav; do
            if [ -f "$file" ]; then
                ((total_files++))
            fi
        done
    fi
done

echo "Found $total_files .wav files to process"
echo "Starting processing..."

# Process each breed/sex folder
for folder in "$INPUT_DIR"/*; do
    if [ -d "$folder" ]; then
        folder_name=$(basename "$folder")
        echo "Processing folder: $folder_name"
        
        # Create corresponding output folder
        mkdir -p "$OUTPUT_DIR/$folder_name"
        
        # Process each .wav file in the folder
        for file in "$folder"/*.wav; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                input_path="$file"
                output_path="$OUTPUT_DIR/$folder_name/$filename"
                
                # Run FFmpeg command
                echo "  Processing: $filename"
                ffmpeg -i "$input_path" -acodec pcm_s16le -ar 44100 "$output_path" -y -loglevel error
                
                if [ $? -eq 0 ]; then
                    ((processed_count++))
                    echo "    ✓ Success ($processed_count/$total_files)"
                else
                    echo "    ✗ Failed: $filename"
                fi
            fi
        done
    fi
done

echo ""
echo "Processing complete!"
echo "Processed: $processed_count/$total_files files"
echo "Output directory: $OUTPUT_DIR"

# Create a summary report
echo "Creating processing report..."
cat > "/Users/nika/Downloads/NMSML/audio_processing_report.txt" << EOF
Audio Processing Report
=======================
Date: $(date)
Input Directory: $INPUT_DIR
Output Directory: $OUTPUT_DIR
Total Files Found: $total_files
Successfully Processed: $processed_count
Failed: $((total_files - processed_count))

FFmpeg Command Used:
ffmpeg -i [input] -acodec pcm_s16le -ar 44100 [output]

This converts all audio files to:
- Codec: PCM 16-bit signed little-endian
- Sample Rate: 44,100 Hz
- Same folder structure as input
EOF

echo "Report saved to: /Users/nika/Downloads/NMSML/audio_processing_report.txt"
