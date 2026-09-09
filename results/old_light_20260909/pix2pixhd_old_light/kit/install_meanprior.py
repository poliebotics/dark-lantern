#!/usr/bin/env python3
"""Install the mean-prior dataset into the box's pix2pixHD checkout and add the P2P_MEANPRIOR switch (idempotent)."""
import os, pathlib, shutil
P = pathlib.Path(os.environ.get("OL_LOCAL", "oldlight_local")) / "pix2pixHD"; K = pathlib.Path(os.environ.get("OL_KIT", os.path.dirname(os.path.abspath(__file__))))
shutil.copy2(K / "meanprior_dataset.py", P / "data" / "meanprior_dataset.py")
f = P / "data" / "custom_dataset_data_loader.py"; t = f.read_text()
if "P2P_MEANPRIOR" not in t:
    old = "def CreateDataset(opt):\n    dataset = None\n    from data.aligned_dataset import AlignedDataset\n    dataset = AlignedDataset()"
    new = "def CreateDataset(opt):\n    dataset = None\n    import os\n    if os.environ.get('P2P_MEANPRIOR'):\n        from data.meanprior_dataset import MeanPriorDataset\n        dataset = MeanPriorDataset()\n    else:\n        from data.aligned_dataset import AlignedDataset\n        dataset = AlignedDataset()"
    assert old in t, "loader text not as expected"; f.write_text(t.replace(old, new))
print("meanprior dataset installed; switch present:", "P2P_MEANPRIOR" in f.read_text())
