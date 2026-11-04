
from pathlib import Path

import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from nilearn.glm.first_level import (
    FirstLevelModel,
    make_first_level_design_matrix,
)
from nilearn.plotting import plot_design_matrix

# Input files: participant 01, Run 1
func = Path("data/derivatives/sub-01/ses-mri/func")
prefix = "sub-01_ses-mri_task-facerecognition_run-1_"

bold_file = func / (
    prefix +
    "space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
)
mask_file = func / (
    prefix +
    "space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
)
events_file = Path("data/raw/sub-01_run-01_events.tsv")
confounds_file = func / (prefix + "desc-confounds_timeseries.tsv")

figures = Path("figures")
results = Path("results")
figures.mkdir(exist_ok=True)
results.mkdir(exist_ok=True)

# 1. Read experimental events and motion parameters
events = pd.read_csv(events_file, sep="\t")
confounds = pd.read_csv(confounds_file, sep="\t")
bold = nib.load(str(bold_file))

motion_columns = [
    "trans_x", "trans_y", "trans_z",
    "rot_x", "rot_y", "rot_z",
]

motion = confounds[motion_columns].fillna(0.0)

n_volumes = bold.shape[3]
tr = float(bold.header.get_zooms()[3])
frame_times = np.arange(n_volumes) * tr

if len(events) == 0 or len(confounds) != n_volumes:
    raise ValueError("Events or confound data are inconsistent.")

# 2. Build our GLM design matrix
design = make_first_level_design_matrix(
    frame_times,
    events=events[["onset", "duration", "trial_type"]],
    hrf_model="spm",
    drift_model="cosine",
    high_pass=1 / 128,
    add_regs=motion.to_numpy(),
    add_reg_names=["motion_" + c for c in motion_columns],
)

rank = np.linalg.matrix_rank(design.to_numpy())
print("Design matrix:", design.shape)
print("Matrix rank:", rank)

if rank != design.shape[1]:
    raise ValueError("Design matrix is not full rank.")

ax = plot_design_matrix(design)
ax.figure.savefig(figures / "design_matrix.png",
                  dpi=150, bbox_inches="tight")
plt.close(ax.figure)

# 3. Plot framewise displacement
fd = confounds["framewise_displacement"].fillna(0.0)

plt.figure(figsize=(9, 3))
plt.plot(frame_times, fd)
plt.axhline(0.5, color="red", linestyle="--",
            label="FD = 0.5 mm")
plt.xlabel("Time (seconds)")
plt.ylabel("Framewise displacement (mm)")
plt.title("Sub-01 Run-01: Head Motion")
plt.legend()
plt.tight_layout()
plt.savefig(figures / "motion_qc.png", dpi=150)
plt.close()

print("Volumes with FD > 0.5 mm:", int((fd > 0.5).sum()))

# 4. Fit the first-level GLM
model = FirstLevelModel(
    mask_img=str(mask_file),
    smoothing_fwhm=5.0,
    noise_model="ar1",
    n_jobs=1,
    minimize_memory=True,
)

print("Fitting first-level GLM...", flush=True)
model.fit(str(bold_file), design_matrices=design)

# 5. Estimate our predefined primary contrast
contrast = np.zeros(design.shape[1])
contrast[design.columns.get_loc("IniFF")] = 0.5
contrast[design.columns.get_loc("IniUF")] = 0.5
contrast[design.columns.get_loc("IniSF")] = -1.0

z_map = model.compute_contrast(
    contrast, output_type="z_score"
)
z_map.to_filename(str(results / "face_contrast_z.nii.gz"))

print("Contrast Z-map saved.")
print("Step 02 completed successfully.")
