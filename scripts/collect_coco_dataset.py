
import os
import re
import cv2
import time
import json
import shutil
import random
import argparse
from tqdm import tqdm


def extract_tex_files(path, target_pattern):
    tex_files = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith(".tex"):
                continue
            if file.startswith("paper_"):
                continue

            tex_file = os.path.join(root, file)

            try:
                with open(tex_file) as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue

            if "\\begin{document}" not in content:
                continue

            if not any(re.match(pattern, root.split('/')[-2]) for pattern in target_pattern):
                continue

            if os.path.exists(f'{root}/output/result/layout_annotation.json'):
                tex_files.append(tex_file)
    return tex_files


def main(path, target_pattern, ratio):
    now_time = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime(time.time()))
    coco_dataset_name = f'COCO_datasets/Multi-modal_COCO_dataset_{now_time}'

    target_images_folder = f'{coco_dataset_name}/images'
    os.makedirs(coco_dataset_name, exist_ok=True)
    os.makedirs(target_images_folder, exist_ok=True)

    tex_files = sorted(extract_tex_files(path, target_pattern))
    tex_files_length = len(tex_files)

    random.seed(0)
    random.shuffle(tex_files)
    train_list = tex_files[:int(tex_files_length * ratio)]
    val_list = tex_files[int(tex_files_length * ratio):]
    dataset_dict = {
        "train": train_list,
        "val": val_list
    }

    info = {
        "year": 2023,
        "version": "1.0",
        "description": "COCO format dataset converted form document genome",
        "contributor": "ADLab",
        "url": "",
        "date_created": f"{time.ctime()}"
    }
    licenses = [
        {
            "url": "http://creativecommons.org/licenses/by/2.0/",
            "id": 4,
            "name": "Attribution License"
        }
    ]
    images = []
    annotations = []
    categories = [
        {"id": 0, "name": "Algorithm", "supercategory": "Algorithm"},
        {"id": 1, "name": "Caption", "supercategory": "Caption"},
        {"id": 2, "name": "Equation", "supercategory": "Equation"},
        {"id": 3, "name": "Figure", "supercategory": "Figure"},
        {"id": 4, "name": "Footnote", "supercategory": "Footnote"},
        {"id": 5, "name": "List", "supercategory": "List"},
        {"id": 6, "name": "Others", "supercategory": "Others"},
        {"id": 7, "name": "Table", "supercategory": "Table"},
        {"id": 8, "name": "Text", "supercategory": "Text"},
        {"id": 9, "name": "Text-EQ", "supercategory": "Text"},
        {"id": 10, "name": "Title", "supercategory": "Title"},
        {"id": 11, "name": "Reference", "supercategory": "Reference"},
        {"id": 12, "name": "PaperTitle", "supercategory": "Title"},
        {"id": 13, "name": "Code", "supercategory": "Algorithm"},
        {"id": 14, "name": "Abstract", "supercategory": "Text"}
    ]

    anno_id = 0
    image_id = 0
    pattern = r'\d+\.\d+(v\d+)?'
    for key, tex_files in dataset_dict.items():
        print(f"Processing {key} set...")
        
        images = []
        annotations = []
        
        for tex_file in tqdm(tex_files):
            coco_annotation_file = f'{os.path.dirname(tex_file)}/output/result/layout_annotation.json'
            images_path = f'{os.path.dirname(tex_file)}/output/colored'

            if not re.search(pattern, tex_file): raise NotImplementedError
            arxiv_paper_id = re.search(pattern, tex_file).group()

            with open(coco_annotation_file, 'r') as fp:
                coco_annotation = json.load(fp)
                sub_images = coco_annotation['images']
                sub_annotations_list = coco_annotation['annotations']

            grouped_annotations = {}
            for annotation in sub_annotations_list:
                anno_image_id = annotation['image_id']
                # 检查image_id是否已经在字典中
                if anno_image_id not in grouped_annotations:
                    # 如果不在，创建一个新的列表
                    grouped_annotations[anno_image_id] = []
                # 将注释添加到相应的列表中
                grouped_annotations[anno_image_id].append(annotation)

            grouped_annotations_key_list = sorted(grouped_annotations.keys())
            for idx in grouped_annotations_key_list:
                file_name = arxiv_paper_id.replace('.', '_') + f'-page_{idx:04d}.png'
                page_image = cv2.imread(f'{images_path}/{idx}.png')
                H, W, _ = page_image.shape
                page_annotations = grouped_annotations[idx]

                images.append(
                    {
                        "id": image_id,
                        "width": W,
                        "height": H,
                        "file_name": file_name,
                        "coco_url": "https://github.com/MaoSong2022/vrdu_data_process",
                        "date_captured": now_time,
                        "flickr_url": "",
                        "licenses": 4
                    }
                )
                shutil.copyfile(f'{images_path}/{idx}.png', f'{target_images_folder}/{file_name}')

                for anno in page_annotations:
                    annotations.append(
                        {
                            "id": anno_id,
                            "image_id": image_id,
                            "category_id": anno["category_id"],
                            "segmentation": anno["segmentation"],
                            "bbox": anno["bbox"],
                            "area": anno["area"],
                            "iscrowd": anno["iscrowd"]
                        }

                    )
                    anno_id += 1
                image_id += 1

        coco_json_content = {
            "info": info,
            "licenses": licenses,
            "images": images,
            "annotations": annotations,
            "categories": categories,
        }

        with open(f'{coco_dataset_name}/{key}.json', 'w') as fp:
            json.dump(coco_json_content, fp, indent=4)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-p", "--path", type=str, required=True)
    # parser.add_argument("-r", "--ratio", type=float, default=0.8)
    # args = parser.parse_args()
    # path = args.path

    target_pattern = [r'^cs\.\w+$']
    path = os.path.expanduser("/cpfs01/user/penghaoyang/code/vrdu_data_process/vrdu_arxiv")
    ratio = 0.8
    main(path, target_pattern, ratio)
