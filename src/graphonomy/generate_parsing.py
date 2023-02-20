import os

import torch

# import tqdm

from src.graphonomy.infer import inference
from src.graphonomy.networks import deeplab_xception_transfer


def main(data_dir: str, out_dir: str, model_path: str) -> None:
    net = (
        deeplab_xception_transfer.deeplab_xception_transfer_projection_savemem(
            n_classes=20,
            hidden_layers=128,
            source_classes=7,
        )
    )
    x = torch.load(model_path)
    net.load_source_model(x)
    net.cuda()
    print("load model:", model_path)
    os.makedirs(out_dir, exist_ok=True)
    images = os.listdir(data_dir)
    for image in images:
        inference(
            net=net,
            img_path=os.path.join(data_dir, image),
            output_path=out_dir,
            output_name=image.split(".")[0],
            use_gpu=True,
        )


if __name__ == "__main__":
    main()
