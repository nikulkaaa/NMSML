################################################################################
# Praat script: Extract F0, F1, F2 from all .wav files in a folder
# Author: Nikola Bátová (simple version for debugging)
################################################################################

# Set paths directly (no form dialog to avoid path issues)
input_directory$ = "/Users/nika/Downloads/NMSML/DogSpeak_Subset/audio_files"
output_file$ = "/Users/nika/Downloads/NMSML/formant_analysis_results.csv"

# Create or overwrite CSV header
filedelete 'output_file$'
fileappend 'output_file$' Folder,File,Breed,Sex,F0_mean,F0_min,F0_max,F1_mean,F2_mean'newline$'

# List of folders (hardcoded to avoid path issues)
folder1$ = "chihuahua_female"
folder2$ = "chihuahua_male" 
folder3$ = "german shepherd_female"
folder4$ = "german shepherd_male"
folder5$ = "husky_female"
folder6$ = "husky_male"
folder7$ = "pitbull_female"
folder8$ = "pitbull_male"
folder9$ = "shiba inu_female"
folder10$ = "shiba inu_male"

# Process each folder
for folderNum from 1 to 10
    if folderNum = 1
        folderName$ = folder1$
    elsif folderNum = 2
        folderName$ = folder2$
    elsif folderNum = 3
        folderName$ = folder3$
    elsif folderNum = 4
        folderName$ = folder4$
    elsif folderNum = 5
        folderName$ = folder5$
    elsif folderNum = 6
        folderName$ = folder6$
    elsif folderNum = 7
        folderName$ = folder7$
    elsif folderNum = 8
        folderName$ = folder8$
    elsif folderNum = 9
        folderName$ = folder9$
    elsif folderNum = 10
        folderName$ = folder10$
    endif
    
    printline Processing folder: 'folderName$'
    
    # Extract breed and sex from folder name
    underscorePos = rindex(folderName$, "_")
    if underscorePos > 0
        breed$ = left$(folderName$, underscorePos - 1)
        sex$ = right$(folderName$, length(folderName$) - underscorePos)
    else
        breed$ = folderName$
        sex$ = "unknown"
    endif
    
    # Process files in this folder
    folderPath$ = input_directory$ + "/" + folderName$
    Create Strings as file list: "fileList", folderPath$ + "/*.wav"
    numberOfFiles = Get number of strings
    
    printline Found 'numberOfFiles' files in 'folderName$'
    
    for i from 1 to numberOfFiles
        select Strings fileList
        fileName$ = Get string: i
        filePath$ = folderPath$ + "/" + fileName$
        
        # Read the sound file
        Read from file: filePath$
        soundName$ = selected$("Sound")
        
        # Extract F0
        select Sound 'soundName$'
        To Pitch (ac): 0.0, 75, 15, "no", 0.03, 0.45, 0.01, 0.35, 0.14, 500
        f0_mean = Get mean: 0, 0, "Hertz"
        f0_min = Get minimum: 0, 0, "Hertz", "Parabolic"
        f0_max = Get maximum: 0, 0, "Hertz", "Parabolic"
        
        # Extract formants
        select Sound 'soundName$'
        To Formant (burg): 0.0, 5, 5500, 0.025, 50
        f1_mean = Get mean: 1, 0, 0, "Hertz"
        f2_mean = Get mean: 2, 0, 0, "Hertz"
        
        # Handle undefined values
        if f0_mean = undefined
            f0_mean = 0
        endif
        if f0_min = undefined
            f0_min = 0
        endif
        if f0_max = undefined
            f0_max = 0
        endif
        if f1_mean = undefined
            f1_mean = 0
        endif
        if f2_mean = undefined
            f2_mean = 0
        endif
        
        # Write to CSV
        fileappend 'output_file$' 'folderName$','fileName$','breed$','sex$','f0_mean:1','f0_min:1','f0_max:1','f1_mean:1','f2_mean:1''newline$'
        
        # Clean up
        select all
        minus Strings fileList
        Remove
        
        printline Processed: 'fileName$'
    endfor
    
    # Clean up file list
    select Strings fileList
    Remove
endfor

printline Finished! Results saved to: 'output_file$'