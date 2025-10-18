import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.formula.api import mixedlm
import statsmodels.api as sm
from scipy.stats import shapiro, levene
import warnings
import os
from datetime import datetime
from pathlib import Path
warnings.filterwarnings('ignore')
from typing import Optional, TextIO
INPUT_PATH = Path('data/features/feature_extraction_results.csv')
# Create output directory
OUTPUT_DIR = Path('data/statistical_analysis')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize markdown file
md_file_path = OUTPUT_DIR / 'statistical_analysis_report.md'
md_file = open(md_file_path, 'w')

def print_and_write(text: str, file: Optional[TextIO] = None) -> None:
    """
    Print to console and write to markdown file

    :param text: Text to print and write
    :param file: Optional file object to write to
    :return: None
    """
    print(text)
    if file:
        file.write(text + '\n')

# Write markdown header
md_file.write(f"""# Statistical Analysis Report: Vocal Dimorphism in Dog Breeds

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Research Question:** Are there differences in the way vocal dimorphism is modulated in different dog breeds?

**Data Source:** DogSpeak_Dataset from HuggingFace (ArlingtonCL2/DogSpeak_Dataset)

---

""")

# Load the data
df = pd.read_csv(INPUT_PATH)

# Data preprocessing
print_and_write("## Dataset Overview", md_file)
print_and_write("", md_file)
print_and_write(f"- **Total samples:** {len(df)}", md_file)
print_and_write(f"- **Breeds:** {list(df['Breed'].unique())}", md_file)
print_and_write("", md_file)
print_and_write("### Sex Distribution", md_file)
for sex, count in df['Sex'].value_counts().items():
    print_and_write(f"- {sex}: {count}", md_file)

print_and_write("", md_file)
print_and_write("### Missing Values", md_file)
missing_vals = df.isnull().sum()
if missing_vals.sum() == 0:
    print_and_write("- No missing values found", md_file)
else:
    for col, count in missing_vals.items():
        if count > 0:
            print_and_write(f"- {col}: {count}", md_file)

# Extract dog_id from filename for random effects
df['dog_id'] = df['File'].str.extract(r'_(\d+)\.wav')[0]
df['dog_id'] = df['dog_id'].fillna(df['File'].str.extract(r'_dog_(\d+)')[0])

# Handle zero values (likely measurement errors)
zero_f0_count = (df['F0_mean'] == 0).sum()
print_and_write("", md_file)
print_and_write(f"**Zero values in F0_mean:** {zero_f0_count}", md_file)
df_clean = df[df['F0_mean'] > 0].copy()  # Remove rows with F0 = 0
print_and_write(f"**Samples after removing F0=0:** {len(df_clean)}", md_file)

# Create breed size categories based on typical breed sizes
breed_sizes = {
    'chihuahua': 'small',
    'shiba inu': 'medium', 
    'husky': 'large',
    'german shepherd': 'large',
    'pitbull': 'medium-large'
}

df_clean['breed_size'] = df_clean['Breed'].map(breed_sizes)

print_and_write("", md_file)
print_and_write("### Breed Size Distribution", md_file)
for size, count in df_clean['breed_size'].value_counts().items():
    print_and_write(f"- {size}: {count}", md_file)

# Descriptive statistics by breed and sex
print_and_write("", md_file)
print_and_write("---\n", md_file)
print_and_write("## Descriptive Statistics", md_file)
print_and_write("", md_file)

desc_stats = df_clean.groupby(['Breed', 'Sex']).agg({
    'F0_mean': ['count', 'mean', 'std'],
    'F0_min': ['mean', 'std'],
    'F0_max': ['mean', 'std'],
    'F1_mean': ['mean', 'std'],
    'F2_mean': ['mean', 'std']
}).round(2)

print_and_write("### Summary Statistics by Breed and Sex", md_file)
print_and_write("", md_file)
print_and_write("```", md_file)
print_and_write(str(desc_stats), md_file)
print_and_write("```", md_file)

# Statistical tests for assumptions
print_and_write("", md_file)
print_and_write("---\n", md_file)
print_and_write("## Assumption Testing", md_file)
print_and_write("", md_file)

# Test for normality (Shapiro-Wilk for each group)
def test_normality_by_group(data: pd.DataFrame, variable: str, md_file: Optional[TextIO] = None) -> None:
    """
    Test normality of a variable by breed and sex using Shapiro-Wilk test.

    :param data: DataFrame containing the data
    :param variable: Name of the variable to test
    :param md_file: Optional markdown file to write results
    :return: None
    """
    print_and_write(f"### Normality Test for {variable}", md_file)
    print_and_write("", md_file)
    print_and_write("| Breed | Sex | W-statistic | p-value |", md_file)
    print_and_write("|-------|-----|-------------|---------|", md_file)
    
    for breed in data['Breed'].unique():
        for sex in data['Sex'].unique():
            group_data = data[(data['Breed'] == breed) & (data['Sex'] == sex)][variable]
            if len(group_data) > 3:  # Need at least 3 samples
                stat, p = shapiro(group_data)
                print_and_write(f"| {breed} | {sex} | {stat:.3f} | {p:.3f} |", md_file)

# Test normality for each acoustic feature
for feature in ['F0_mean', 'F0_min', 'F0_max', 'F1_mean', 'F2_mean']:
    test_normality_by_group(df_clean, feature, md_file)
    print_and_write("", md_file)

# Test for homogeneity of variance (Levene's test)
print_and_write("### Homogeneity of Variance Tests (Levene's Test)", md_file)
print_and_write("", md_file)
print_and_write("| Feature | Levene Statistic | p-value |", md_file)
print_and_write("|---------|------------------|---------|", md_file)

for feature in ['F0_mean', 'F0_min', 'F0_max', 'F1_mean', 'F2_mean']:
    groups = [df_clean[(df_clean['Breed'] == breed) & (df_clean['Sex'] == sex)][feature].values 
              for breed in df_clean['Breed'].unique() 
              for sex in df_clean['Sex'].unique()
              if len(df_clean[(df_clean['Breed'] == breed) & (df_clean['Sex'] == sex)]) > 0]
    
    stat, p = levene(*groups)
    print_and_write(f"| {feature} | {stat:.3f} | {p:.3f} |", md_file)

# Linear Mixed-Effects Models
print_and_write("", md_file)
print_and_write("---\n", md_file)
print_and_write("## Linear Mixed-Effects Models", md_file)
print_and_write("", md_file)
print_and_write("**Model Formula:** `feature ~ Sex * Breed + (1 | dog_id)`", md_file)
print_and_write("", md_file)

# Ensure proper data types
df_clean['Sex'] = df_clean['Sex'].astype('category')
df_clean['Breed'] = df_clean['Breed'].astype('category')
df_clean['dog_id'] = df_clean['dog_id'].astype('category')

# Function to fit and report LME model
def fit_lme_model(data: pd.DataFrame, dependent_var: str, md_file: Optional[TextIO] = None) -> None:
    """
    Fit a linear mixed-effects model and report results.
    
    :param data: DataFrame containing the data
    :param dependent_var: Name of the dependent variable
    :param md_file: Optional markdown file to write results
    :return: Fitted model result
    """
    print_and_write(f"### Model Results: {dependent_var}", md_file)
    print_and_write("", md_file)
    
    # Fit the model: feature ~ sex * breed + (1 | dog_id)
    try:
        model = mixedlm(f"{dependent_var} ~ Sex * Breed", 
                       data=data, 
                       groups=data["dog_id"])
        result = model.fit()
        
        print_and_write("#### Full Model Summary", md_file)
        print_and_write("```", md_file)
        print_and_write(str(result.summary()), md_file)
        print_and_write("```", md_file)
        
        # Extract and display key results
        print_and_write("", md_file)
        print_and_write("#### Key Results", md_file)
        print_and_write("", md_file)
        
        # Main effects
        sex_effect = result.params.get('Sex[T.male]', None)
        if sex_effect is not None:
            sex_pval = result.pvalues.get('Sex[T.male]', None)
            print_and_write(f"**Sex effect (male vs female):** {sex_effect:.3f} (p={sex_pval:.3f})", md_file)
        
        print_and_write("", md_file)
        print_and_write("**Breed Effects (vs reference breed):**", md_file)
        # Breed effects (compared to reference breed)
        for param in result.params.index:
            if 'Breed[T.' in param and 'Sex[T.male]:' not in param:
                breed_name = param.replace('Breed[T.', '').replace(']', '')
                effect = result.params[param]
                pval = result.pvalues[param]
                print_and_write(f"- {breed_name}: {effect:.3f} (p={pval:.3f})", md_file)
        
        # Interaction effects
        print_and_write("", md_file)
        print_and_write("**Interaction Effects (Sex × Breed):**", md_file)
        for param in result.params.index:
            if 'Sex[T.male]:Breed[T.' in param:
                breed_name = param.replace('Sex[T.male]:Breed[T.', '').replace(']', '')
                effect = result.params[param]
                pval = result.pvalues[param]
                print_and_write(f"- Male × {breed_name}: {effect:.3f} (p={pval:.3f})", md_file)
        
        print_and_write("", md_file)
        return result
        
    except Exception as e:
        print_and_write(f"**Error fitting model for {dependent_var}:** {e}", md_file)
        return None

# Fit models for each acoustic feature
f0_mean_model = fit_lme_model(df_clean, 'F0_mean', md_file)
f0_min_model = fit_lme_model(df_clean, 'F0_min', md_file)
f0_max_model = fit_lme_model(df_clean, 'F0_max', md_file)
f1_model = fit_lme_model(df_clean, 'F1_mean', md_file) 
f2_model = fit_lme_model(df_clean, 'F2_mean', md_file)

# Effect size calculations (Cohen's d) for sex differences within each breed
print_and_write("---\n", md_file)
print_and_write("## Effect Sizes (Cohen's d) for Sex Differences", md_file)
print_and_write("", md_file)

def cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size
    
    :param group1: First group data
    :param group2: Second group data
    :return: Cohen's d value
    """
    n1, n2 = len(group1), len(group2)
    s1, s2 = group1.std(ddof=1), group2.std(ddof=1)
    pooled_std = np.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / (n1+n2-2))
    return (group1.mean() - group2.mean()) / pooled_std

for breed in df_clean['Breed'].unique():
    print_and_write(f"### {breed.upper()}", md_file)
    print_and_write("", md_file)
    print_and_write("| Feature | Cohen's d | t-statistic | p-value |", md_file)
    print_and_write("|---------|-----------|-------------|---------|", md_file)
    
    breed_data = df_clean[df_clean['Breed'] == breed]
    
    if len(breed_data[breed_data['Sex'] == 'female']) > 0 and len(breed_data[breed_data['Sex'] == 'male']) > 0:
        for feature in ['F0_mean', 'F0_min', 'F0_max', 'F1_mean', 'F2_mean']:
            female_data = breed_data[breed_data['Sex'] == 'female'][feature]
            male_data = breed_data[breed_data['Sex'] == 'male'][feature]
            
            if len(female_data) > 1 and len(male_data) > 1:
                d = cohens_d(female_data, male_data)
                # t-test for significance
                t_stat, p_val = stats.ttest_ind(female_data, male_data)
                
                print_and_write(f"| {feature} | {d:.3f} | {t_stat:.3f} | {p_val:.3f} |", md_file)
    
    print_and_write("", md_file)

# Visualization
print_and_write("---\n", md_file)
print_and_write("## Visualizations", md_file)
print_and_write("", md_file)

# Set up the plotting style
plt.style.use('default')
sns.set_palette("husl")

# ORIGINAL FIGURE: F0_mean, F1_mean, F2_mean
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Vocal Dimorphism Across Dog Breeds - Original Analysis', fontsize=16, fontweight='bold')

features = ['F0_mean', 'F1_mean', 'F2_mean']
feature_labels = ['Fundamental Frequency (F0 Mean)', 'First Formant (F1)', 'Second Formant (F2)']

for i, (feature, label) in enumerate(zip(features, feature_labels)):
    # Box plot by breed and sex
    sns.boxplot(data=df_clean, x='Breed', y=feature, hue='Sex', ax=axes[0, i])
    axes[0, i].set_title(f'{label} by Breed and Sex')
    axes[0, i].set_xticklabels(axes[0, i].get_xticklabels(), rotation=45)
    axes[0, i].legend(title='Sex')
    
    # Violin plot showing distributions
    sns.violinplot(data=df_clean, x='Breed', y=feature, hue='Sex', ax=axes[1, i])
    axes[1, i].set_title(f'{label} Distribution by Breed and Sex')
    axes[1, i].set_xticklabels(axes[1, i].get_xticklabels(), rotation=45)
    axes[1, i].legend(title='Sex')

plt.tight_layout()
plot1_path = OUTPUT_DIR / 'vocal_dimorphism_analysis.png'
plt.savefig(plot1_path, dpi=300, bbox_inches='tight')

print_and_write(f"![Vocal Dimorphism Analysis]({os.path.basename(plot1_path)})", md_file)
print_and_write("", md_file)
print_and_write("*Figure 1: Box plots (top row) and violin plots (bottom row) showing the distribution of acoustic features by breed and sex.*", md_file)
print_and_write("", md_file)

# NEW FIGURE: F0 measures (Mean, Min, Max)
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('F0 (Fundamental Frequency) Analysis Across Dog Breeds', fontsize=16, fontweight='bold')

f0_features = ['F0_mean', 'F0_min', 'F0_max']
f0_labels = ['F0 Mean', 'F0 Minimum', 'F0 Maximum']

for i, (feature, label) in enumerate(zip(f0_features, f0_labels)):
    # Box plot by breed and sex
    sns.boxplot(data=df_clean, x='Breed', y=feature, hue='Sex', ax=axes[0, i])
    axes[0, i].set_title(f'{label} by Breed and Sex')
    axes[0, i].set_xticklabels(axes[0, i].get_xticklabels(), rotation=45)
    axes[0, i].legend(title='Sex')
    axes[0, i].set_ylabel('Frequency (Hz)')
    
    # Violin plot showing distributions
    sns.violinplot(data=df_clean, x='Breed', y=feature, hue='Sex', ax=axes[1, i])
    axes[1, i].set_title(f'{label} Distribution by Breed and Sex')
    axes[1, i].set_xticklabels(axes[1, i].get_xticklabels(), rotation=45)
    axes[1, i].legend(title='Sex')
    axes[1, i].set_ylabel('Frequency (Hz)')

plt.tight_layout()
plot3_path = OUTPUT_DIR / 'f0_analysis_complete.png'
plt.savefig(plot3_path, dpi=300, bbox_inches='tight')

print_and_write(f"![F0 Analysis Complete]({os.path.basename(plot3_path)})", md_file)
print_and_write("", md_file)
print_and_write("*Figure 3: Box plots (top row) and violin plots (bottom row) showing all F0 measures (mean, minimum, maximum) by breed and sex. This provides a comprehensive view of fundamental frequency patterns.*", md_file)
print_and_write("", md_file)

# UPDATED EFFECT SIZE HEATMAP: Include all F0 measures
fig, ax = plt.subplots(1, 1, figsize=(14, 8))

effect_sizes = []
breeds_list = []
features_list = []

for breed in df_clean['Breed'].unique():
    breed_data = df_clean[df_clean['Breed'] == breed]
    
    if len(breed_data[breed_data['Sex'] == 'female']) > 0 and len(breed_data[breed_data['Sex'] == 'male']) > 0:
        for feature in ['F0_mean', 'F0_min', 'F0_max', 'F1_mean', 'F2_mean']:
            female_data = breed_data[breed_data['Sex'] == 'female'][feature]
            male_data = breed_data[breed_data['Sex'] == 'male'][feature]
            
            if len(female_data) > 1 and len(male_data) > 1:
                d = cohens_d(female_data, male_data)
                effect_sizes.append(d)
                breeds_list.append(breed)
                features_list.append(feature)

# Create effect size dataframe
effect_df = pd.DataFrame({
    'Breed': breeds_list,
    'Feature': features_list,
    'Effect_Size': effect_sizes
})

# Pivot for heatmap
effect_pivot = effect_df.pivot(index='Breed', columns='Feature', values='Effect_Size')

# Create heatmap with better formatting for more features
sns.heatmap(effect_pivot, annot=True, cmap='RdBu_r', center=0, 
            cbar_kws={'label': "Cohen's d (Female - Male)"}, ax=ax,
            fmt='.2f', square=True)
ax.set_title("Effect Sizes for Sex Differences Across Breeds and Features", fontweight='bold')
ax.set_xlabel('Acoustic Features')
ax.set_ylabel('Dog Breeds')
plt.xticks(rotation=45)
plt.yticks(rotation=0)
plt.tight_layout()
plot2_path = OUTPUT_DIR / 'effect_sizes_heatmap_complete.png'
plt.savefig(plot2_path, dpi=300, bbox_inches='tight')

print_and_write(f"![Effect Sizes Heatmap Complete]({os.path.basename(plot2_path)})", md_file)
print_and_write("", md_file)
print_and_write("*Figure 2: Heatmap showing Cohen's d effect sizes for sex differences across breeds and all acoustic features. Positive values indicate females have higher values than males.*", md_file)
print_and_write("", md_file)

# F0 RANGE ANALYSIS: Additional insight
print_and_write("### F0 Range Analysis", md_file)
print_and_write("", md_file)
print_and_write("Understanding F0 range (F0_max - F0_min) can provide insights into vocal flexibility:", md_file)
print_and_write("", md_file)

# Calculate F0 range
df_clean['F0_range'] = df_clean['F0_max'] - df_clean['F0_min']

# F0 Range by breed and sex
print_and_write("| Breed | Sex | Mean F0 Range (Hz) | Std F0 Range |", md_file)
print_and_write("|-------|-----|-------------------|--------------|", md_file)

for breed in sorted(df_clean['Breed'].unique()):
    for sex in ['female', 'male']:
        breed_sex_data = df_clean[(df_clean['Breed'] == breed) & (df_clean['Sex'] == sex)]
        if len(breed_sex_data) > 0:
            mean_range = breed_sex_data['F0_range'].mean()
            std_range = breed_sex_data['F0_range'].std()
            print_and_write(f"| {breed} | {sex} | {mean_range:.1f} | {std_range:.1f} |", md_file)

print_and_write("", md_file)

# F0 Range visualization
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('F0 Range Analysis Across Dog Breeds', fontsize=16, fontweight='bold')

# Box plot for F0 range
sns.boxplot(data=df_clean, x='Breed', y='F0_range', hue='Sex', ax=axes[0])
axes[0].set_title('F0 Range by Breed and Sex')
axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=45)
axes[0].set_ylabel('F0 Range (Hz)')
axes[0].legend(title='Sex')

# Scatter plot: F0 mean vs F0 range
sns.scatterplot(data=df_clean, x='F0_mean', y='F0_range', hue='Sex', style='Breed', ax=axes[1], alpha=0.7)
axes[1].set_title('F0 Mean vs F0 Range')
axes[1].set_xlabel('F0 Mean (Hz)')
axes[1].set_ylabel('F0 Range (Hz)')

plt.tight_layout()
plot4_path = OUTPUT_DIR / 'f0_range_analysis.png'
plt.savefig(plot4_path, dpi=300, bbox_inches='tight')

print_and_write(f"![F0 Range Analysis]({os.path.basename(plot4_path)})", md_file)
print_and_write("", md_file)
print_and_write("*Figure 4: F0 range analysis showing vocal flexibility. Left: F0 range by breed and sex. Right: Relationship between F0 mean and range.*", md_file)
print_and_write("", md_file)

# Summary and interpretation
print_and_write("---\n", md_file)
print_and_write("## Summary and Interpretation", md_file)
print_and_write("", md_file)

print_and_write("### Research Hypotheses Testing", md_file)
print_and_write("", md_file)
print_and_write("1. **Males will show lower F0 and Formant frequencies than females:**", md_file)
print_and_write("   - Check the sign of Sex[T.male] coefficients in the models above", md_file)
print_and_write("   - Negative coefficients support this hypothesis", md_file)
print_and_write("", md_file)
print_and_write("2. **Larger breeds will show larger acoustic differences:**", md_file)
print_and_write("   - Compare effect sizes (Cohen's d) across breeds", md_file)
print_and_write("   - Larger breeds (German Shepherd, Husky) should show larger effects", md_file)
print_and_write("", md_file)
print_and_write("3. **Small breeds will show smaller or no differences:**", md_file)
print_and_write("   - Chihuahua should show smaller effect sizes", md_file)
print_and_write("   - Look for non-significant interactions in small breeds", md_file)
print_and_write("", md_file)
print_and_write("4. **F0 range may show different patterns than mean F0:**", md_file)
print_and_write("   - F0 range reflects vocal flexibility and dynamic range", md_file)
print_and_write("   - May vary independently of average F0 values", md_file)
print_and_write("", md_file)

print_and_write("### Interpretation Guidelines", md_file)
print_and_write("", md_file)
print_and_write("- **Cohen's d:** 0.2 = small, 0.5 = medium, 0.8 = large effect", md_file)
print_and_write("- **p < 0.05** indicates statistical significance", md_file)
print_and_write("- **Interaction effects** show breed-specific sex differences", md_file)
print_and_write("- **F0_min:** Lowest fundamental frequency in the vocalization", md_file)
print_and_write("- **F0_max:** Highest fundamental frequency in the vocalization", md_file)
print_and_write("- **F0_range:** F0_max - F0_min, indicates vocal flexibility", md_file)
print_and_write("", md_file)

print_and_write("### Model Specification", md_file)
print_and_write("", md_file)
print_and_write("The Linear Mixed-Effects Models account for:", md_file)
print_and_write("- **Fixed effects:** Sex, Breed, and their interaction", md_file)
print_and_write("- **Random effects:** Individual dog variation (dog_id)", md_file)
print_and_write("- **Separate models** for F0_mean, F0_min, F0_max, F1_mean, and F2_mean", md_file)
print_and_write("", md_file)

print_and_write("---", md_file)
print_and_write("", md_file)
print_and_write("**Analysis completed successfully!** All results, figures, and this report have been saved to the `data/statistical_analysis/` directory.", md_file)

# Close the markdown file
md_file.close()

print(f"\nAnalysis complete! All output saved to: {OUTPUT_DIR}")
print(f"- Markdown report: {md_file_path}")
print(f"- Figures:")
print(f"  * Original analysis: {OUTPUT_DIR / 'vocal_dimorphism_analysis.png'}")
print(f"  * Complete F0 analysis: {OUTPUT_DIR / 'f0_analysis_complete.png'}")
print(f"  * Complete effect sizes: {OUTPUT_DIR / 'effect_sizes_heatmap_complete.png'}")
print(f"  * F0 range analysis: {OUTPUT_DIR / 'f0_range_analysis.png'}")