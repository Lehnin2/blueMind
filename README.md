Aquamed – Coral and Fish Classification for Marine Monitoring
Overview
Aquamed is an AI-driven marine image classification platform designed to support coral health monitoring and fish toxicity identification. It leverages deep learning models trained on augmented datasets of coral and fish images, aiming to aid marine conservation and sustainable aquatic resource management.

The app combines state-of-the-art convolutional neural networks with robust data augmentation and preprocessing to classify various coral types and fish toxicity levels from underwater imagery.

Datasets
1. Coral Classification Dataset
Source: Corals Group 4784 dataset via Coral Lifeform (Roboflow).

Classes: 7 coral types (Branching, Encrusting, Foliose, Massive, Mushroom, Submassive, Tabulate).

Images: Initially 529 annotated images, augmented to ~1,284 images using rotation, flipping, and zooming.

Splits:

Train: 1,029–1,284 images

Validation: 45–300 images

Test: 56 images

Preprocessing: Resized to 224×224 px; augmentations include ±40° rotation, shifts (0.2), shear (0.2), zoom (0.2), horizontal flip.

3. BHD Corals – Coral Pathology Classification
Classes: Bleached, Healthy, Dead corals.

Original Distribution: Bleached (500), Healthy (500), Dead (150).

Augmentation: 380 synthetic images added for Dead class to balance dataset to 500 images per class (total 1,500).

Splits: Stratified 80% train, 10% validation, 10% test.

Preprocessing: Images resized to 224×224 px, normalized.

Models and Results
Coral Pathology Classification with EfficientNetB3
Architecture: EfficientNetB3 pretrained on ImageNet, with dropout (45%) and L1/L2 regularization.

Training: Adamax optimizer, categorical cross-entropy loss, early stopping.

Performance:

Accuracy: 92.45% on test set

Strong precision and recall for Bleached and Healthy classes; lower for Dead due to fewer samples.

Coral Type Classification Models (7 classes)
Model	Train Acc	Val Acc	Test Acc	Notes
EfficientNetB0	Moderate (underfitting)	-	Not evaluated	Limited performance, struggled with complex textures.
ResNet50	51.74% (initial), 43.32% (improved)	53% (initial), 47.67% (improved)	42.86%–50%	Underfitting, affected by class imbalance.
DenseNet121	94.02%	71.11%	69.64%	Best performance, handles complex textures well, minor overfitting.
