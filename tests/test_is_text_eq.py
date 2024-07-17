import unittest

from DocParser.vrdu.renderer import is_text_eq


class TestTextEq(unittest.TestCase):
    def test_text1(self):
        content = r"For this experiment, we employed 5 different models: 2 segmentation models and 3 classification models. For image segmentation, we employed MaskRCNN ResNet50 FPN model~\cite{He_2017_ICCV}, pre-trained on MS COCO dataset~\cite{mscoco_2014} and evaluated on a subset of 24,237 images of MS COCO train2017, containing 80 distinct classes, and FCN ResNet50 model~\cite{Long_2015_CVPR}, pre-trained on MS COCO, and evaluated on a subset of MS COCO val2017, limited to the 20 categories found in the Pascal VOC dataset~\cite{Everingham10}. For classification models we employed ImageNet pre-trained ResNet18~\cite{he2016deep} DenseNet161~\cite{huang2017densely}, and GoogleNet~\cite{Szegedy_2015_CVPR}, with 1,000 output neurons, each neuron corresponding to the individual class in the ImageNet dataset."
        self.assertFalse(is_text_eq(content))

    def test_text2(self):
        content = r"For this experiment, test 5\$ we employed 5 different models: 2 segmentation models and 3 classification models. For image segmentation, we employed MaskRCNN ResNet50 FPN model~\cite{He_2017_ICCV}, pre-trained on MS COCO dataset~\cite{mscoco_2014} and evaluated on a subset of 24,237 images of MS COCO train2017, containing 80 distinct classes, and FCN ResNet50 model~\cite{Long_2015_CVPR}, pre-trained on MS COCO, and evaluated on a subset of MS COCO val2017, limited to the 20 categories found in the Pascal VOC dataset~\cite{Everingham10}. For classification models we employed ImageNet pre-trained ResNet18~\cite{he2016deep} DenseNet161~\cite{huang2017densely}, and GoogleNet~\cite{Szegedy_2015_CVPR}, with 1,000 output neurons, each neuron corresponding to the individual class in the ImageNet dataset."
        self.assertFalse(is_text_eq(content))

    def test_text_eq1(self):
        content = r"In physics, the mass-energy equivalence is stated by the equation $E=mc^2$, discovered in 1905 by Albert Einstein."
        self.assertTrue(is_text_eq(content))

    def test_text_eq2(self):
        content = r"In physics, the mass-energy equivalence is stated by the equation \(E=mc^2\), discovered in 1905 by Albert Einstein."
        self.assertTrue(is_text_eq(content))

    def test_text_eq3(self):
        content = r"In physics, the mass-energy equivalence is stated by the equation \begin{math}E=mc^2\end{math}, discovered in 1905 by Albert Einstein."
        self.assertTrue(is_text_eq(content))

    def test_text_eq4(self):
        content = r"In physics, the mass-energy equivalence is stated by the equation \begin{math}E=mc^2\end{math}, discovered in 1905 by Albert Einstein, test 5\$."
        self.assertTrue(is_text_eq(content))
