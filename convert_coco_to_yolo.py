import os
import json
import argparse
from shutil import copyfile


# parser = argparse.ArgumentParser(description='Test yolo data.')
# parser.add_argument('-j', help='JSON file', dest='json', required=True)
# parser.add_argument('-o', help='path to output folder', dest='out', required=True)
#
# args = parser.parse_args()
#
# json_file = args.json
# output = args.out

class COCO2YOLO:
    def __init__(self, json_file, output_path):
        self.json_file = json_file
        self.output_path = output_path
        self.output_image_path = output_path.replace('labels', 'images')
        self.output_folder = os.path.dirname(os.path.dirname(self.output_path))
        self._check_file_and_dir()
        self.labels = json.load(open(json_file, 'r', encoding='utf-8'))
        self.coco_id_name_map = self._categories()
        self.coco_name_list = list(self.coco_id_name_map.values())
        print("total images", len(self.labels['images']))
        print("total categories", len(self.labels['categories']))
        print("total labels", len(self.labels['annotations']))

    def _check_file_and_dir(self):
        if not os.path.exists(self.json_file):
            raise ValueError("file not found")
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(self.output_image_path, exist_ok=True)

    def _categories(self):
        categories = {}
        for cls in self.labels['categories']:
            categories[cls['id']] = cls['name']
        return categories

    def _load_images_info(self):
        images_info = {}
        for image in self.labels['images']:
            id = image['id']
            file_name = image['file_name']
            if file_name.find('\\') > -1:
                file_name = file_name[file_name.index('\\') + 1:]
            w = image['width']
            h = image['height']
            images_info[id] = (file_name, w, h)

        return images_info

    def _bbox_2_yolo(self, bbox, img_w, img_h):
        x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
        centerx = bbox[0] + w / 2
        centery = bbox[1] + h / 2
        dw = 1 / img_w
        dh = 1 / img_h
        centerx *= dw
        w *= dw
        centery *= dh
        h *= dh
        return centerx, centery, w, h

    def _convert_anno(self, images_info):
        anno_dict = dict()
        for anno in self.labels['annotations']:
            bbox = anno['bbox']
            image_id = anno['image_id']
            category_id = anno['category_id']

            image_info = images_info.get(image_id)
            image_name = image_info[0]
            img_w = image_info[1]
            img_h = image_info[2]
            yolo_box = self._bbox_2_yolo(bbox, img_w, img_h)

            anno_info = (image_name, category_id, yolo_box)
            anno_infos = anno_dict.get(image_id)
            if not anno_infos:
                anno_dict[image_id] = [anno_info]
            else:
                anno_infos.append(anno_info)
                anno_dict[image_id] = anno_infos
        return anno_dict

    def save_classes(self):
        sorted_classes = list(map(lambda x: x['name'], sorted(self.labels['categories'], key=lambda x: x['id'])))
        print('coco names', sorted_classes)
        with open(f'{self.output_folder}/classes.txt', 'w', encoding='utf-8') as f:
            for cls in sorted_classes:
                f.write(cls + '\n')
        f.close()

    def coco2yolo(self):
        print("loading image info...")
        images_info = self._load_images_info()
        print("loading done, total images", len(images_info))

        print("start converting...")
        anno_dict = self._convert_anno(images_info)
        print("converting done, total labels", len(anno_dict))

        self.save_classes()

        print("saving txt file...")
        self._save_txt(anno_dict)
        print("saving done")        

    def _save_txt(self, anno_dict):
        raw_images_path = os.path.join(os.path.dirname(self.json_file), 'images')
        for k, v in anno_dict.items():
            file_name = os.path.splitext(v[0][0])[0] + ".txt"
            image_name = os.path.splitext(v[0][0])[0] + ".png"
            copyfile(f'{raw_images_path}/{image_name}', f'{self.output_image_path}/{image_name}')
            with open(os.path.join(self.output_path, file_name), 'w', encoding='utf-8') as f:
                # print(k, v)
                for obj in v:
                    cat_name = self.coco_id_name_map.get(obj[1])
                    category_id = self.coco_name_list.index(cat_name)
                    box = ['{:.6f}'.format(x) for x in obj[2]]
                    box = ' '.join(box)
                    line = str(category_id) + ' ' + box
                    f.write(line + '\n')


if __name__ == '__main__':
    mode = 'val'
    json_file = f'COCO_datasets/Multi-modal_COCO_dataset_2023-12-14-13_52_07/{mode}.json'
    output = f'YOLO_datasets/Multi-modal_COCO_dataset_2023-12-14-13_52_07/labels/{mode}'
    c2y = COCO2YOLO(json_file, output)
    c2y.coco2yolo()
