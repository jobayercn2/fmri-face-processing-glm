
from pathlib import Path
import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 1. Define input and output locations
func = Path("data/derivatives/sub-01/ses-mri/func")

bold_file = func / (
    "sub-01_ses-mri_task-facerecognition_run-1_"
    "space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
)

mask_file = func / (
    "sub-01_ses-mri_task-facerecognition_run-1_"
    "space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
)

events_file = Path("data/raw/sub-01_run-01_events.tsv")

confounds_file = func / (
    "sub-01_ses-mri_task-facerecognition_run-1_"
    "desc-confounds_timeseries.tsv"
)

figures = Path("figures")
figures.mkdir(exist_ok=True)

# 2. Load imaging and tabular data
bold = nib.load(str(bold_file))
mask = nib.load(str(mask_file))
events = pd.read_csv(events_file, sep="\t")
confounds = pd.read_csv(confounds_file, sep="\t")

# 3. Inspect data characteristics
print("=== Participant 01, Run 1 ===")
print("BOLD shape:", bold.shape)
print("Voxel size (mm):", bold.header.get_zooms()[:3])
print("TR (seconds):", bold.header.get_zooms()[3])
print("Mask shape:", mask.shape)
print("Number of confound rows:", len(confounds))

print("\n=== Experimental Conditions ===")
print(events["trial_type"].value_counts().sort_index())

# 4. Visualize one functional brain slice
z = bold.shape[2] // 2

brain_slice = np.rot90(np.asarray(bold.dataobj[:, :, z, 0]))
mask_slice = np.rot90(np.asarray(mask.dataobj[:, :, z]))

plt.figure(figsize=(7, 6))
plt.imshow(brain_slice, cmap="gray")
plt.contour(mask_slice, levels=[0.5], colors="red")
plt.title("Sub-01 Run-01: BOLD Image and Brain Mask")
plt.axis("off")
plt.tight_layout()
plt.savefig(figures / "brain_slice.png", dpi=150)
plt.close()

# 5. Visualize the experimental event timing
visual_events = events[
    events["trial_type"].str.startswith(("Ini", "Imm", "Del"))
]

plt.figure(figsize=(11, 5))
plt.scatter(
    visual_events["onset"],
    visual_events["trial_type"],
    s=14
)
plt.xlabel("Time (seconds)")
plt.ylabel("Experimental condition")
plt.title("Sub-01 Run-01: Visual Stimulus Timing")
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(figures / "event_timing.png", dpi=150)
plt.close()

print("\nSaved: figures/brain_slice.png")
print("Saved: figures/event_timing.png")
print("Inspection completed successfully.")
print("BOLD and mask affines match:", np.allclose(bold.affine, mask.affine))
print("Confound rows match BOLD volumes:", len(confounds) == bold.shape[3])