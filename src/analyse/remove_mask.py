import os
import sys
import numpy as np
import torch
import yaml
from PIL import Image
from omegaconf import OmegaConf
from pathlib import Path
import cv2

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

sys.path.insert(0, str(Path(__file__).resolve().parent / "lama"))
from analyse.lama.saicinpainting.evaluation.utils import move_to_device
from analyse.lama.saicinpainting.training.trainers import load_checkpoint
from analyse.lama.saicinpainting.evaluation.data import pad_tensor_to_modulo

class LamaOperator:
    def __init__(self, 
            config_p: str,
            ckpt_p: str,
            device="cuda"):
        
        self.predict_config = OmegaConf.load(config_p)
        self.predict_config.model.path = ckpt_p
        # device = torch.device(predict_config.device)
        self.device = torch.device(device)

        train_config_path = os.path.join(
            self.predict_config.model.path, 'config.yaml')

        with open(train_config_path, 'r') as f:
            train_config = OmegaConf.create(yaml.safe_load(f))

        train_config.training_model.predict_only = True
        train_config.visualizer.kind = 'noop'

        checkpoint_path = os.path.join(
            self.predict_config.model.path, 'models',
            self.predict_config.model.checkpoint
        )
        self.model = load_checkpoint(
            train_config, checkpoint_path, strict=False, map_location='cpu')
        self.model.freeze()
        if not self.predict_config.get('refine', False):
            self.model.to(device)

        
        
    def load_img_to_array(self, img_p):
        img = Image.open(img_p)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        return np.array(img)


    def save_array_to_img(self, img_arr, img_p):
        Image.fromarray(img_arr.astype(np.uint8)).save(img_p)

    @torch.no_grad()
    def inpaint_img_with_lama(self,
            img_path: str,
            mask: np.ndarray,
            mod=8,
            times_try=2
    ):
        assert len(mask.shape) == 2
        if np.max(mask) == 1:
            mask = mask * 255
        img = cv2.imread(img_path)
        img = np.array(img)
        img = torch.from_numpy(img).float().div(255.)
        mask = torch.from_numpy(mask).float()
        
        batch = {}
        batch['image'] = img.permute(2, 0, 1).unsqueeze(0)
        batch['mask'] = mask[None, None]
        unpad_to_size = [batch['image'].shape[2], batch['image'].shape[3]]
        batch['image'] = pad_tensor_to_modulo(batch['image'], mod)
        batch['mask'] = pad_tensor_to_modulo(batch['mask'], mod)
        batch = move_to_device(batch, self.device)
        batch['mask'] = (batch['mask'] > 0) * 1
        
        for _ in range(times_try):
            batch = self.model(batch)
        cur_res = batch[self.predict_config.out_key][0].permute(1, 2, 0)
        cur_res = cur_res.detach().cpu().numpy()

        if unpad_to_size is not None:
            orig_height, orig_width = unpad_to_size
            cur_res = cur_res[:orig_height, :orig_width]

        cur_res = np.clip(cur_res * 255, 0, 255).astype('uint8')
        return cur_res

base_dir = os.path.join(os.environ['PROJECT_DIR'],"analyse/lama")

if (not "lama_config_p" in os.environ):
    config_p = os.path.join(base_dir, "configs/prediction/default.yaml")
else:
    config_p = os.environ["lama_config_p"]

if (not "lama_ckpt_p" in os.environ):
    ckpt_p = os.path.join(base_dir, "big-lama")
else:
    ckpt_p = os.environ["lama_ckpt_p"]

lama_operator = LamaOperator(config_p, ckpt_p, device="cpu")