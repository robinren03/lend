import os
import sys
sys.path.append(os.environ["PROJECT_DIR"])

from PIL import Image
from PIL import ImageFile
from torch.utils.data import Dataset, DataLoader
import pickle
import numpy as np
import clip
import torch
from tqdm import tqdm

ImageFile.LOAD_TRUNCATED_IMAGES = True

class ClipSearchDataset(Dataset):
    def __init__(self, img_dir, img_ext_list=['.jpg', '.png', '.jpeg', '.tiff'], preprocess=None):
        self.preprocess = preprocess
        self.img_path_list = self.walk_dir(img_dir, img_ext_list)

    def walk_dir(self, dir_path, img_ext_list):
        img_paths = []
        for root, dirs, files in os.walk(dir_path):
            img_paths.extend(
                os.path.join(root, file) for file in files
                if os.path.splitext(file)[1].lower() in img_ext_list
            )

            for dir in dirs:
                full_dir_path = os.path.join(root, dir)
                if os.path.islink(full_dir_path):
                    img_paths.extend(self.walk_dir(full_dir_path, img_ext_list))
        return img_paths

    def __len__(self):
        return len(self.img_path_list)

    def __getitem__(self, idx):
        img_path = self.img_path_list[idx]
        img = Image.open(img_path).convert('RGB')
        img = self.preprocess(img)
        return img, img_path

def create_dataloader(img_dir, preprocess, batch_size=256, num_workers=4):
    dataset = ClipSearchDataset(img_dir=img_dir, preprocess=preprocess)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return dataloader

def load_clip_model(device):
    model, preprocess = clip.load('ViT-B/32', device)
    return model, preprocess

def main(img_dir, output_dir, device="cuda"):
    model, preprocess = load_clip_model(device)
    dataloader = create_dataloader(img_dir, preprocess)
    img_path_list, embedding_list = [], []

    for img, img_path in tqdm(dataloader):
        with torch.no_grad():
            features = model.encode_image(img.to(device))
            features /= features.norm(dim=-1, keepdim=True)
            embedding_list.extend(features.detach().cpu().numpy())
            img_path_list.extend(img_path)

    embedding_list = np.array(embedding_list, dtype=np.float32)
    img_path_list = [path.split('/')[-2].upper() for path in img_path_list]
    from analyse.object import DeviceType, ALIAS
    classes = list(DeviceType.__members__.keys())
    classes.remove("FAILED")
    classes.remove("BLOCK")
    classes.remove("SUBNET")
    classes.remove("DEVICE_BLOCK")
    classes_gpu = [f"a {c.lower() + ' icon' if c.lower() != 'link' else 'line symbol'}" for c in classes if c != "FAILED"]
    classes_gpu = clip.tokenize(classes_gpu).to(device)
    class_list = {}
    features = model.encode_text(classes_gpu)
    features /= features.norm(dim=-1, keepdim=True)
    features = features.detach().cpu().numpy()
    class_list = {classes[i]:[features[i]] for i in range(len(classes))}
    for key, value in ALIAS.items():
        value = [f"a {v.lower() + ' icon' if key != 'link' else v.lower()}" for v in value]
        val = clip.tokenize(value).to(device)
        features = model.encode_text(val)
        features /= features.norm(dim=-1, keepdim=True)
        features = features.detach().cpu().numpy()
        class_list[key].extend(features)
        
    with open(os.path.join(output_dir, "embedding_list.pkl"), "wb") as f:
        pickle.dump(embedding_list, f)

    with open(os.path.join(output_dir, "img_path_list.pkl"), "wb") as f:
        pickle.dump(img_path_list, f)
    
    with open (os.path.join(output_dir, "class_list.pkl"), "wb") as f:
        pickle.dump(class_list, f)

if __name__=="__main__":
    main(img_dir=os.path.join(os.environ["PROJECT_DIR"], "feature_db/icon_simplified"), output_dir=os.path.join(os.environ["PROJECT_DIR"], "models"))