"""Mean-prior pix2pixHD dataset: the generator sees (E_t, mean training capture) and predicts B_t.

A 6-channel input for pix2pixHD with --label_nc 0 --input_nc 6. The mean training capture (pairs/<...>/mean_train_B.png, or
P2P_MEAN_IMAGE) is a fixed image, the same for every frame, so the network need only learn how the emission modulates the known
scene; the emission alone carries no positional information, which is why the plain crop and full-frame recipes render no scene.
The same transform (crop or scale) is applied to the emission, the mean image and the target, so the three stay aligned.
Selected with P2P_MEANPRIOR=1 (data/custom_dataset_data_loader.py switch)."""
import os
import torch
from PIL import Image
from data.aligned_dataset import AlignedDataset
from data.base_dataset import get_params, get_transform


class MeanPriorDataset(AlignedDataset):
    def initialize(self, opt):
        super().initialize(opt)
        p = os.environ.get("P2P_MEAN_IMAGE") or os.path.join(opt.dataroot, "mean_train_B.png")
        self.mean_img = Image.open(p).convert("RGB"); self.mean_path = p

    def __getitem__(self, index):
        A_path = self.A_paths[index]
        A = Image.open(A_path).convert("RGB")
        params = get_params(self.opt, A.size)
        tf = get_transform(self.opt, params)
        M = self.mean_img if self.mean_img.size == A.size else self.mean_img.resize(A.size, Image.LANCZOS)
        A_t = tf(A); M_t = tf(M)
        B_t = 0
        if self.opt.isTrain or self.opt.use_encoded_image:
            B_t = tf(Image.open(self.B_paths[index]).convert("RGB"))
        return {"label": torch.cat([A_t, M_t], 0), "inst": 0, "image": B_t, "feat": 0, "path": A_path}

    def name(self):
        return "MeanPriorDataset"
