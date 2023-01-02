import json
import os
from pathlib import Path

import cv2
from tqdm import tqdm

from src.body import Body


def generate_keypoints(img_path: str, dir_save: str, body_estimation):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pose_keypoints_2d = []
    candidate, subset = body_estimation(img)

    for peak in candidate[:18]:
        for item in peak[:3]:
            pose_keypoints_2d.append(item)

    if len(candidate) < 18:
        for _ in range(18 - len(candidate)):
            pose_keypoints_2d.append(0)
            pose_keypoints_2d.append(0)
            pose_keypoints_2d.append(0)

    json_data = {
        "version": 1.3,
        "people": [
            {
                "person_id": [-1],
                "pose_keypoints_2d": pose_keypoints_2d,
                "face_keypoints_2d": [],
                "hand_left_keypoints_2d": [],
                "hand_right_keypoints_2d": [],
                "pose_keypoints_3d": [],
                "face_keypoints_3d": [],
                "hand_left_keypoints_3d": [],
                "hand_right_keypoints_3d": [],
            }
        ],
    }

    filename = Path(img_path).stem
    with open(
        os.path.join(dir_save, f"{filename}_keypoints.json"), "w"
    ) as outfile:
        json.dump(json_data, outfile)


def main(data_dir: str, out_dir: str, model_path: str) -> None:
    images = os.listdir(data_dir)
    body_estimation = Body(model_path)
    os.makedirs(out_dir, exist_ok=True)
    for image in tqdm(images):
        generate_keypoints(
            os.path.join(data_dir, image), out_dir, body_estimation
        )


if __name__ == "__main__":
    main()
