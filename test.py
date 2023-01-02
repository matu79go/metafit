import os
import warnings

import cv2
import numpy as np
import torch
import tqdm

import dnnlib
from training import dataset as custom_dataset
import src.legacy as legacy
import src.utils as utils
import src.generate_keypoints as generate_keypoints
import src.graphonomy.generate_parsing as generate_parsing
import src.preprocess as peroprocess


def main() -> None:
    args = utils.get_parser().parse_args()
    config = utils.load_config(args.config)
    device = torch.device("cuda")
    outdir = config["outdir"]
    testpart = config["testpart"]
    print("Preprocessing images ...")
    peroprocess.main(
        data_dir=os.path.join(config["dataroot"], config["image_dir"]),
    )
    print("Generating keypoints ...")
    generate_keypoints.main(
        data_dir=os.path.join(config["dataroot"], config["image_dir"]),
        out_dir=os.path.join(config["dataroot"], config["keypoints_dir"]),
        model_path=config["pose_model_path"],
    )

    print("Generating parsing ...")
    generate_parsing.main(
        data_dir=os.path.join(config["dataroot"], config["image_dir"]),
        out_dir=os.path.join(config["dataroot"], config["parsing_dir"]),
        model_path=config["parsing_model_path"],
    )

    print("Generating images ...")
    with dnnlib.util.open_url(config["network"]) as f:
        G = legacy.load_network_pkl(f)["G_ema"].to(device)  # type: ignore

    os.makedirs(outdir, exist_ok=True)

    if testpart == "full":
        dataset = custom_dataset.UvitonDatasetFull_512_test_full(
            path=config["dataroot"],
            test_txt=config["testtxt"],
            use_sleeve_mask=config["use_sleeve_mask"],
            max_size=None,
            xflip=False,
        )
    elif testpart == "upper":
        dataset = custom_dataset.UvitonDatasetFull_512_test_upper(
            path=config["dataroot"],
            test_txt=config["testtxt"],
            use_sleeve_mask=config["use_sleeve_mask"],
            max_size=None,
            xflip=False,
        )
    elif testpart == "lower":
        dataset = custom_dataset.UvitonDatasetFull_512_test_lower(
            path=config["dataroot"],
            test_txt=config["testtxt"],
            use_sleeve_mask=config["use_sleeve_mask"],
            max_size=None,
            xflip=False,
        )

    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=config["batchsize"],
        shuffle=False,
        pin_memory=True,
        num_workers=32,
    )

    for data in tqdm.tqdm(dataloader):
        (
            image,
            clothes,
            pose,
            _,
            norm_img,
            norm_img_lower,
            denorm_upper_clothes,
            denorm_lower_clothes,
            denorm_upper_mask,
            denorm_lower_mask,
            retain_mask,
            skin_average,
            lower_label_map,
            lower_clothes_upper_bound,
            person_name,
            clothes_name,
        ) = data

        image_tensor = image.to(device).to(torch.float32) / 127.5 - 1
        clothes_tensor = clothes.to(device).to(torch.float32) / 127.5 - 1
        pose_tensor = pose.to(device).to(torch.float32) / 127.5 - 1
        norm_img_tensor = norm_img.to(device).to(torch.float32) / 127.5 - 1
        norm_img_lower_tensor = (
            norm_img_lower.to(device).to(torch.float32) / 127.5 - 1
        )

        skin_tensor = skin_average.to(device).to(torch.float32) / 127.5 - 1
        lower_label_map_tensor = (
            lower_label_map.to(device).to(torch.float32) / 127.5 - 1
        )
        lower_clothes_upper_bound_tensor = (
            lower_clothes_upper_bound.to(device).to(torch.float32) / 127.5 - 1
        )

        parts_tensor = torch.cat(
            [norm_img_tensor, norm_img_lower_tensor], dim=1
        )

        denorm_upper_clothes_tensor = (
            denorm_upper_clothes.to(device).to(torch.float32) / 127.5 - 1
        )
        denorm_upper_mask_tensor = denorm_upper_mask.to(device).to(
            torch.float32
        )

        denorm_lower_clothes_tensor = (
            denorm_lower_clothes.to(device).to(torch.float32) / 127.5 - 1
        )
        denorm_lower_mask_tensor = denorm_lower_mask.to(device).to(
            torch.float32
        )

        retain_mask_tensor = retain_mask.to(device)
        retain_tensor = image_tensor * retain_mask_tensor - (
            1 - retain_mask_tensor
        )
        pose_tensor = torch.cat(
            [
                pose_tensor,
                lower_label_map_tensor,
                lower_clothes_upper_bound_tensor,
            ],
            dim=1,
        )
        retain_tensor = torch.cat([retain_tensor, skin_tensor], dim=1)
        gen_z = torch.randn([config["batchsize"], 0], device=device)

        with torch.no_grad():
            gen_c, cat_feat_list = G.style_encoding(
                parts_tensor, retain_tensor
            )
            pose_feat = G.const_encoding(pose_tensor)
            ws = G.mapping(gen_z, gen_c)
            cat_feats = {}
            for cat_feat in cat_feat_list:
                h = cat_feat.shape[2]
                cat_feats[str(h)] = cat_feat
            gt_parsing = None
            _, gen_imgs, _ = G.synthesis(
                ws,
                pose_feat,
                cat_feats,
                denorm_upper_clothes_tensor,
                denorm_lower_clothes_tensor,
                denorm_upper_mask_tensor,
                denorm_lower_mask_tensor,
                gt_parsing,
            )

        for ii in range(gen_imgs.size(0)):
            gen_img = gen_imgs[ii].detach().cpu().numpy()
            gen_img = (gen_img.transpose(1, 2, 0) + 1.0) * 127.5
            gen_img = np.clip(gen_img, 0, 255)
            gen_img = gen_img.astype(np.uint8)[..., [2, 1, 0]]

            image_np = image_tensor[ii].detach().cpu().numpy()
            image_np = (image_np.transpose(1, 2, 0) + 1.0) * 127.5
            image_np = image_np.astype(np.uint8)[..., [2, 1, 0]]

            clothes_np = clothes_tensor[ii].detach().cpu().numpy()
            clothes_np = (clothes_np.transpose(1, 2, 0) + 1.0) * 127.5
            clothes_np = clothes_np.astype(np.uint8)[..., [2, 1, 0]]

            result = np.concatenate(
                [
                    clothes_np[:, 96:416, :],
                    image_np[:, 96:416, :],
                    gen_img[:, 96:416, :],
                ],
                axis=1,
            )

            person_n = person_name[ii].split("/")[-1]
            clothes_n = clothes_name[ii].split("/")[-1]

            save_name = person_n[:-4] + "___" + clothes_n[:-4] + ".png"
            save_path = os.path.join(outdir, save_name)
            cv2.imwrite(save_path, result)

    print("finish")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
