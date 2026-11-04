
from pathlib import Path
import numpy as np
import nibabel as nib
import matplotlib

matplotlib.use("Agg")

from nilearn.glm import threshold_stats_img
from nilearn import plotting

# 1. Define input and output files
z_file = Path("results/face_contrast_z.nii.gz")

mask_file = Path(
    "data/derivatives/sub-01/ses-mri/func/"
    "sub-01_ses-mri_task-facerecognition_run-1_"
    "space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
)

results = Path("results")
figures = Path("figures")

# 2. Load the statistical map and brain mask
z_map = nib.load(str(z_file))
mask = nib.load(str(mask_file))

# 3. Apply two-sided voxelwise FDR correction
corrected_map, threshold = threshold_stats_img(
    stat_img=z_map,
    mask_img=mask,
    alpha=0.05,
    height_control="fdr",
    two_sided=True,
    cluster_threshold=0,
)

# 4. Count surviving positive and negative voxels
brain = mask.get_fdata() > 0
values = corrected_map.get_fdata()[brain]

positive = int(np.sum(values > 0))
negative = int(np.sum(values < 0))

print("=== Run 1: Statistical Results ===")
print("Voxels tested:", int(brain.sum()))
print(f"FDR Z threshold: {threshold:.3f}")
print("Positive surviving voxels:", positive)
print("Negative surviving voxels:", negative)

# 5. Save the corrected statistical map
corrected_map.to_filename(
    str(results / "face_contrast_FDR05_z.nii.gz")
)

# 6. Generate an anatomical activation figure
if positive + negative > 0 and np.isfinite(threshold):
    display = plotting.plot_stat_map(
        corrected_map,
        threshold=threshold,
        display_mode="z",
        cut_coords=[-24, -16, -8, 0, 8],
        cmap="cold_hot",
        colorbar=True,
        title="Sub-01 Run-01: Faces vs Scrambled (FDR q=0.05)",
    )
else:
    display = plotting.plot_anat(
        display_mode="z",
        cut_coords=[-24, -16, -8, 0, 8],
        title="Sub-01 Run-01: No voxels survive FDR q=0.05",
    )

display.savefig(
    str(figures / "activation_map.png"),
    dpi=150,
)
display.close()

print("Saved: figures/activation_map.png")
print("Step 03 completed successfully.")
