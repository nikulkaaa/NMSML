# Sex Differences of vocals in dogs across breeds

This repository contains scripts and data used to answer the following question:

***"Sex-related differences in the acoustic features of dog barks across breeds: Are there differences in the way vocal dimorphism is modulated in different dog breeds?"***

The original dataset can be found at https://huggingface.co/datasets/ArlingtonCL2/DogSpeak_Dataset

Clone the repository by running the following:
```bash
git clone https://github.com/nikulkaaa/NMSML.git
```

To analyze metadata of the original dataset, download the original dataset running the following in the root of the repository: 

```bash
git clone https://huggingface.co/datasets/ArlingtonCL2/DogSpeak_Dataset
```

Then run: 

```bash
python analyze_metadata.py
```

I created a subset of 10 females and 10 males from each breed, sampling 3 voice recording per animals using his script: 

```bash
python create_subset.py
```