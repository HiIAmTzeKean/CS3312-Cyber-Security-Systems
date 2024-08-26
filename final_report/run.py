import argparse
import os
import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
import torchvision.models as models

from attack_utils import extract_salmap, psnr
from attacks import only_in_roi, variable_noise
from dataset import ImageDataset
from imutils import paths
from pytorch_grad_cam import GradCAM
from skimage.metrics import structural_similarity as ssim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.transforms import transforms

np.random.seed(42)
torch.manual_seed(42)

parser = argparse.ArgumentParser()
parser.add_argument(
    "-e",
    "--epsilons",
    nargs="+",
    type=float,
    help="Set of epsilons to run attack with",
    default=[0.005,0.006,0.007]
)
parser.add_argument(
    "-m", "--mean", nargs="+", type=float, help="Mean of the dataset", default=[0.485, 0.456, 0.406]
)
parser.add_argument(
    "-s",
    "--std",
    nargs="+",
    type=float,
    help="Standard Devation of the dataset",
    default=[0.229, 0.224, 0.225],
)
parser.add_argument("-g", "--logs", type=str, help="Path to log file", default="logs.txt")
parser.add_argument(
    "-d", "--data", type=str, help="Path to the caltech dataset",  default="101_ObjectCategories/"
)
parser.add_argument(
    "-t",
    "--type_attack",
    type=str,
    choices=["fgsm", "variable_noise", "only_in_roi", "intense_in_roi"],
    default="only_in_roi",
    help="Type of attack to be launched",
)
parser.add_argument(
    "-l", "--thresh_lambda", type=float, help="Value of Lambda", default=0.3
)
parser.add_argument(
    "-z", "--z", type=int, default=0, help="Value of Z for variable noise attack", required=False
)
args = parser.parse_args()

data_path = args.data
mean = tuple(args.mean)
std = tuple(args.std)
model_arch = "alexnet"
epsilons = args.epsilons
attack = args.type_attack
thresh_lambda = args.thresh_lambda
Z = args.z
log_file = open(args.logs, "w")

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

image_paths = list(paths.list_images(data_path))
data = []
labels = []
for image_path in image_paths:
    label = image_path.split(os.path.sep)[-2]
    image = cv2.imread(image_path)
    if image is None:
        continue
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    data.append(image)
    labels.append(label)
labels = np.array(labels)
# data = np.array(data)

lb = LabelBinarizer()
labels = lb.fit_transform(labels)
print(f"Total number of classes: {len(lb.classes_)}")

train_transform = transforms.Compose(
    [
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ]
)

val_transform = transforms.Compose(
    [
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ]
)

(X, x_val, Y, y_val) = train_test_split(
    data, labels, test_size=0.2, stratify=labels, random_state=42
)
(x_train, x_test, y_train, y_test) = train_test_split(
    X, Y, test_size=0.25, random_state=42
)

train_data = ImageDataset(x_train, y_train, train_transform)
val_data = ImageDataset(x_val, y_val, val_transform)
test_data = ImageDataset(x_test, y_test, val_transform)

train_loader = DataLoader(train_data, batch_size=1, shuffle=True)
val_loader = DataLoader(val_data, batch_size=1, shuffle=True)
test_loader = DataLoader(test_data, batch_size=1, shuffle=True)

print(
    "Training data:",
    len(train_loader),
    "Validation data:",
    len(val_loader),
    "Test data: ",
    len(test_loader),
)

use_cuda = True
device = torch.device("cuda" if (use_cuda and torch.cuda.is_available()) else "cpu")
print("Device: ", device)
model = models.alexnet(weights='DEFAULT')
target_layers = [model.features[11]]
print(model)


def start_attack(model, device, test_loader, epsilon, attack, thresh_lambda, Z):
    correct = 0
    tot_psnr = 0
    count = 0
    tot_ssim = 0
    adv_examples = []
    for data, target in test_loader:
        data, target = data.to(device), target.to(device)
        data.requires_grad = True
        data_og = data.detach().clone()
        output = model(data)
        init_pred = output.max(1, keepdim=True)[1]
        target = (target[0] == 1).nonzero()
        target = target[0]
        if init_pred.item() != target.item():
            pass
        loss = F.nll_loss(output, target)
        model.zero_grad()
        loss.backward()
        data_grad = data.grad.data
        img = data_og.cpu().detach().numpy()
        target.cpu().numpy()[0]
        print(img.shape)
        img = img.astype(np.float32)
        print(img.dtype)
        input_tensor = torch.from_numpy(img)
        cam = GradCAM(model=model, target_layers=target_layers)
        targets = None
        grayscale_cam = cam(input_tensor=input_tensor, targets=targets)

        grayscale_cam = grayscale_cam[0, :]

        cam = grayscale_cam
        cam = torch.tensor(cam)
        print(cam.shape)

        pixels_in_roi, other_pixels = extract_salmap(cam, thresh_lambda)

        if attack == "variable_noise":
            assert Z > 0
            perturbed_data = variable_noise(
                data, epsilon, data_grad, pixels_in_roi, other_pixels, Z
            )
        elif attack == "only_in_roi":
            perturbed_data = only_in_roi(data, epsilon, data_grad, pixels_in_roi)

        pdata = perturbed_data[0, :, :, :]
        pdata = pdata.detach().clone()

        pdata = pdata.permute(1, 2, 0)
        data_og = data_og[0, :, :, :]
        data_og = data_og.permute(1, 2, 0)

        psnr_val = psnr(data_og, pdata)
        tot_psnr += psnr_val
        
        s = ssim(
            data_og.detach().cpu().numpy(),
            pdata.detach().cpu().numpy(),
            multichannel=True,
            channel_axis=2,
            data_range=1
        )
        print("SSIM:", s)
        
        tot_ssim += s
        count+=1

    final_acc = correct / float(len(test_loader))
    avg_psnr = tot_psnr / count
    print(
        "Epsilon: {}\tTest Accuracy = {} / {} = {}".format(
            epsilon, correct, len(test_loader), final_acc
        )
    )
    print("Avg PSNR Ratio: ", avg_psnr)
    print("Avg SSIm: ", tot_ssim / count)
    res = (
        "Epsilon:"
        + str(epsilon)
        + " Test Accuracy = "
        + str(correct / len(test_loader))
        + " Final Accuracy = "
        + str(final_acc)
        + "\n"
    )
    log_file.write(res)
    psnr_str = "Avg PSNR Ratio: " + str(avg_psnr) + "\n"
    log_file.write(psnr_str)
    ssim_str = "Avg SSIM: " + str(tot_ssim / count) + "\n"
    log_file.write(ssim_str)
    return final_acc, adv_examples


print("Attack in Progress")
accuracies = []
examples = []
for eps in epsilons:
    acc, ex = start_attack(model, device, train_loader, eps, attack, thresh_lambda, Z)
    print("Accuracy = ", acc)
    accuracies.append(acc)
    examples.append(ex)
plt.figure(figsize=(5, 5))
plt.plot(epsilons, accuracies, "*-")
plt.title(attack)
plt.xlabel("Epsilon")
plt.ylabel("Accuracy")
plt.show()
fname = str(attack) + "_" + str(thresh_lambda) + ".png"
plt.savefig(fname)
cnt = 0
for i in range(len(epsilons)):
    for j in range(len(examples[i])):
        cnt += 1
        plt.subplot(len(epsilons), len(examples[0]), cnt)
        plt.xticks([], [])
        plt.yticks([], [])
        if j == 0:
            plt.ylabel("Eps: {}".format(epsilons[i]), fontsize=14)
        orig, adv, ex = examples[i][j]
        exx = torch.from_numpy(ex)
        plt.title("{} -> {}".format(orig, adv))
        plt.imshow(exx.permute(1, 2, 0))
plt.tight_layout()
plt.show()
fname = str(attack) + "_" + str(thresh_lambda) + "_output" + ".png"
plt.savefig(fname)