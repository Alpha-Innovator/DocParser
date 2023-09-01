import argparse
import os
import glob
from PIL import Image
from typing import List, Tuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from collections import namedtuple

from boungding_box.info2json import write_json

from logger import logger

# log = logger.get_logger(__name__)
log = logger.setup_app_level_logger(file_name="app_debug.log")

BoundingBox = namedtuple('BoundingBox', ['position', 'width', 'height'])


def show_annotation(image, bounding_boxes: List, color='red'):
    plt.imshow(image)

    # Add rectangles to the plot
    for rectangle in bounding_boxes:
        # TODO: fix this

        rect = patches.Rectangle(rectangle['position'], rectangle['width'], rectangle['height'],
                                 linewidth=2, 
                                 edgecolor=color, 
                                 facecolor='none')
        plt.gca().add_patch(rect)

    # Create a Figure and render the plot onto a canvas
    fig = plt.gcf()
    canvas = FigureCanvas(fig)
    canvas.draw()

    # Convert the canvas to a NumPy array
    plot_image = np.array(canvas.renderer.buffer_rgba())

    # Close the plot to free up resources
    plt.close()

    return plot_image


def show_difference(img1_rgb, img2_rgb):
    image_array1 = np.asarray(img1_rgb)
    image_array2 = np.asarray(img2_rgb)

    image_array_difference = np.absolute(image_array1 - image_array2)
    difference_image = Image.fromarray(image_array_difference)
    difference_image.show() 



def isDiff(img1_rgb, img2_rgb):
    width, height = img1_rgb.size
    div_mat = np.zeros((width, height))
    unit_px = 5
    def imgdiv(x1,x2,y1,y2):
        log.debug(f"x1:{x1} x2:{x2} y1:{y1} y2:{y2}")
        div = np.absolute(np.asarray(img1_rgb)[x1:x2,y1:y2] - np.asarray(img2_rgb)[x1:x2,y1:y2])   
        if np.sum(div)/np.size(div) <= 0:
            return 
        
        if x2-x1 <= unit_px and y2-y1 <= unit_px:
            div_mat[x1:x2,y1:y2] = np.ones([x2-x1, y2-y1])
        elif x2 - x1 > y2 - y1: 
            half = (x1 + (x2-x1)//2)//5*5
            imgdiv(x1,half,y1,y2)
            imgdiv(half,x2,y1,y2)
        else:
            half = (y1 + (y2-y1)//2)//5*5
            imgdiv(x1,x2,y1,half)
            imgdiv(x1,x2,half,y2)
    imgdiv(0,width,0,height)
    return div_mat


def minX(points):
    return min(points, key=lambda x: x[0])[0]

def minY(points):
    return min(points, key=lambda x: x[1])[1]

def maxX(points):
    return max(points, key=lambda x: x[0])[0]

def maxY(points):
    return max(points, key=lambda x: x[1])[1]

def point2box(point, box):
    min_x, min_y, max_x, max_y = box[0][0], box[0][1], box[2][0], box[2][1]
    if point[0] >= min_x-5 and point[0] <= max_x+5 and \
       point[1] >= min_y-5 and point[1] <= max_y+5:
        return True
    return False


def isMergeCluster(c1, c2):
    box1 = [(minX(c1), minY(c1)), (maxX(c1), minY(c1)), 
            (maxX(c1), maxY(c1)), (minX(c1), maxY(c1))]
    box2 = [(minX(c2), minY(c2)), (maxX(c2), minY(c2)), 
            (maxX(c2), maxY(c2)), (minX(c2), maxY(c2))]
    for point in box1:
        if point2box(point, box2):
            return True
    for point in box2:
        if point2box(point, box1):
            return True
    return False


def get_cluster(img_binary, unit_px = 5):    
    width, height = img_binary.shape
    c = 0
    class_mat = np.zeros((width, height))
    for x in range(0, width-unit_px, unit_px):
        for y in range(0, height-unit_px, unit_px):
            if np.sum(img_binary[x:x+5,y:y+5]) > 0:  
                if x == 0 and y == 0:
                    c += 1  
                    class_mat[x:x+5,y:y+5] = np.ones([5,5]) * c
                elif x == 0 and y > 0:     
                    if np.sum(class_mat[x:x+5,y-5:y]) > 0:           
                        class_mat[x:x+5,y:y+5] = class_mat[x:x+5,y-5:y]
                    else:
                        c += 1  
                        class_mat[x:x+5,y:y+5] = np.ones([5,5]) * c
                elif x > 0 and y == 0:
                    if np.sum(class_mat[x-5:x,y:y+5]) > 0:            
                        class_mat[x:x+5,y:y+5] = class_mat[x-5:x,y:y+5]
                    else:
                        c += 1  
                        class_mat[x:x+5,y:y+5] = np.ones([5,5]) * c
                else:
                    if np.sum(class_mat[x:x+5,y-5:y]) > 0:           
                        class_mat[x:x+5,y:y+5] = class_mat[x:x+5,y-5:y]
                    elif np.sum(class_mat[x-5:x,y:y+5]) > 0:           
                        class_mat[x:x+5,y:y+5] = class_mat[x-5:x,y:y+5]
                    else:
                        c += 1  
                        class_mat[x:x+5,y:y+5] = np.ones([5,5]) * c
        
    
    clusters = {}
    for i in range(1,c+1):
        clusters[i] = (np.where(class_mat == i))
    clusters_edge = {}
    for c in clusters.keys():
        clusters_edge[c] = []
        xs, ys = clusters[c][0], clusters[c][1]  
        x_dic = {}      
        for j in range(len(ys)):
            x, y = xs[j], ys[j]
            if x not in x_dic:
                x_dic[x] = [y]
            else:
                x_dic[x].append(y)
        for x in x_dic:
            clusters_edge[c].append((x, min(x_dic[x])))
            clusters_edge[c].append((x, max(x_dic[x]))) 
        y_dic = {}    
        for j in range(len(xs)):
            x, y = xs[j], ys[j]
            if y not in y_dic:
                y_dic[y] = [x]
            else:
                y_dic[y].append(x)
        for y in y_dic:
            clusters_edge[c].append((min(y_dic[y]), y))
            clusters_edge[c].append((max(y_dic[y]), y)) 
    connection = {} 
    for i in range(1,c+1):
        connection[i] = i
    for c1 in clusters_edge.keys():
        for c2 in clusters_edge.keys():       
            if isMergeCluster(clusters_edge[c1], clusters_edge[c2]):
                c = min(connection[c1], connection[c2])
                connection[c1], connection[c2], class_mat[class_mat == c2] = c, c, c
    c_va = 1 
    for i in range(1, c + 1):
        if np.sum(np.where(class_mat == i)) > 0:
            class_mat[class_mat == i] = c_va
            c_va += 1

    return class_mat


def get_bounding_box(color_mat, img_original, img_rendered) -> List[List[Tuple[float, float, float, float]]]:
    """
    Calculates the bounding box coordinates of color regions in an image.

    Args:
        color_mat (ndarray): A matrix representing the color regions in the image.
        img_original (ndarray): The original image.
        img_rendered (ndarray): The rendered image.

    Returns:
        List[List[Tuple[float, float, float, float]]]: 
        A list of bounding box coordinates for each color region in the image.
    """
    div_mat_ori = np.sum(np.absolute(img_original - img_rendered), axis=2)
    div_mat_ori[np.where(div_mat_ori < 10)] = 0
    div_mat_ori[np.where(div_mat_ori >= 10)] = 1
    color_mat = color_mat * div_mat_ori
    ret = []
    for c in range(1, round(np.max(color_mat))+1):
        p1_x = minX(np.argwhere(color_mat == c))
        p1_y = minY(np.argwhere(color_mat == c))
        p2_x = maxX(np.argwhere(color_mat == c))
        p2_y = maxY(np.argwhere(color_mat == c))           
        ret.append([p1_y, p1_x, p2_y, p2_x])
    return ret



def generate_bounding_boxes(img_original, img_rendered) -> List[List[Tuple[float, float, float, float]]]:
    div_mat = isDiff(img_original, img_rendered)
    color_mat = get_cluster(div_mat)
    bbox_points = get_bounding_box(color_mat, img_original, img_rendered)
    return bbox_points


def generate_annotation(file, img_original, bbox_points):
    path = 'img_out/'
    output_image = img_original
    output_image = show_annotation(output_image, bbox_points)
    anno_path = path + 'anno/' + file
    rgb_image = Image.fromarray(output_image)
    rgb_image.save(anno_path)

    return output_image

def get_image_info(page_index, output_image):
    file_name = "output/result/page_" + str(page_index) + ".jpg" 
    return {
        "width": output_image.shape[0],
        "height": output_image.shape[1],
        "id": page_index,
        "file_name": file_name}

def get_anno_info(bounding_boxes: List, page_index: int):
    anno_info = []
    for index, bounding_box in enumerate(bounding_boxes):
        anno = {"id": index,
            "image_id": page_index,
            "category_id": 0, # TODO: modify this
            "segmentation": [],
            "bbox": bounding_box, # TODO: modify this
            "ignore": 0,
            "iscrowd": 0,
            "area": -1 # TODO: modify this
            }
        anno_info.append(anno)
            
    return anno_info


def main() -> None:
    # 1. get the image path
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_path', type=str, required=True)
    args = parser.parse_args()
    image_path = args.image_path
    log.debug(f"image_path: {image_path}")

    # 2. read the image
    original_path = os.path.join(image_path, 'output/original')
    rendered_path = os.path.join(image_path, 'output/rendered')
    original_images = sorted(glob.glob(original_path + '/*.jpg'))
    rendered_images = sorted(glob.glob(rendered_path + '/*.jpg'))
    log.debug(f"original_images: {original_images}")
    log.debug(f"rendered_images: {rendered_images}")

    image_pairs = zip(original_images, rendered_images)

    image_infos = []
    annotation_infos = []

    for page_index, image_pair in enumerate(image_pairs):
        # get the file name
        original_image_file, rendered_image_file = image_pair
        log.debug(f"page_index: {page_index}, original_image_file: {original_image_file}")
        log.debug(f"page_index: {page_index}, rendered_image_file: {rendered_image_file}")
        original_image = Image.open(original_image_file).convert('RGB')
        rendered_image = Image.open(rendered_image_file).convert('RGB')

        show_difference(original_image, rendered_image)
        break

        # 3. compute the box
        # bounding_boxes = generate_bounding_boxes(original_image,
        #                                          rendered_image)
        # log.debug("bounding boxes generated")

        # # 4.1 output the annotation image
        # generate_annotation(original_image_file, original_image, bounding_boxes)
        # log.debug("annotation image generated")

        # # 4.2 save the info
        # image_infos.append(get_image_info(page_index, original_image))
        # annotation_infos.append(get_anno_info(bounding_boxes, page_index))
        # log.debug("info saved")
    
    # 5. output the bounding box in COCO format
    # write_json(image_infos, annotation_infos, file_name='annotation.json')


if __name__ == '__main__':
    main()
