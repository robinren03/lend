### Install Instructions
The requirements.txt now is short and brief, may not contain every package you need.  Install the required package as the code requires.

Note that version of certain package like Pytorch is very important, because some tools we use require the version of Pytorch in a certain range of version.

```bash
pip install -r requirements.txt
```

Besides the models we download, you need to download the pre-trained directory of LaMa, namely big-lama and pre-trained model of ViT-H for SAM, namely sam_vit_h_4b8939.pth.

### Running Instructions
Note that the input source and output directory is currently a hard path, change it before use it.
```bash
cd lend 
export PROJECT_DIR=`pwd`
python run.py --img_path <the path to your image> --output_dir <the place to put your outputs>
```

Other parameters for LEND please run `python run.py --help` for reference.
