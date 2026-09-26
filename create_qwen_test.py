"""Generates Qwen_Image_Test.ipynb — a notebook that loads the local
Qwen-Image model and generates a test image.

Usage:
    python create_qwen_test.py
"""

import json

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "intro",
            "metadata": {},
            "source": [
                "# Qwen-Image Test\n",
                "\n",
                "This notebook loads the local Qwen-Image model and generates an image."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "env-check",
            "metadata": {},
            "outputs": [],
            "source": [
                "import torch\n",
                "import os\n",
                "\n",
                "print('PyTorch:', torch.__version__)\n",
                "print('CUDA available:', torch.cuda.is_available())\n",
                "print('Torch CUDA:', torch.version.cuda)\n",
                "\n",
                "if torch.cuda.is_available():\n",
                "    print('GPU:', torch.cuda.get_device_name(0))\n",
                "    print('VRAM:', round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2), 'GB')\n",
                "else:\n",
                "    print('WARNING: CUDA is not available')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "load-model",
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import torch\n",
                "from diffusers import DiffusionPipeline\n",
                "\n",
                "MODEL_PATH = '/home/24alr044/models/Qwen-Image-2.1'\n",
                "\n",
                "print('Loading model from:')\n",
                "print(MODEL_PATH)\n",
                "\n",
                "if not os.path.isdir(MODEL_PATH):\n",
                "    parent = os.path.dirname(MODEL_PATH)\n",
                "    available = os.listdir(parent) if os.path.isdir(parent) else []\n",
                "    raise FileNotFoundError(\n",
                "        f'Model path not found: {MODEL_PATH}\\n'\n",
                "        f'Directories in {parent}: {available}'\n",
                "    )\n",
                "\n",
                "if not os.path.isfile(os.path.join(MODEL_PATH, 'model_index.json')):\n",
                "    raise FileNotFoundError(\n",
                "        f\"model_index.json missing in {MODEL_PATH} - the model download \"\n",
                "        f'looks incomplete. Files present: {sorted(os.listdir(MODEL_PATH))}'\n",
                "    )\n",
                "\n",
                "pipe = DiffusionPipeline.from_pretrained(\n",
                "    MODEL_PATH,\n",
                "    torch_dtype=torch.bfloat16,\n",
                "    local_files_only=True\n",
                ")\n",
                "\n",
                "print('Model loaded successfully!')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "generate",
            "metadata": {},
            "outputs": [],
            "source": [
                "try:\n",
                "    pipe.enable_model_cpu_offload()\n",
                "except ImportError as exc:\n",
                "    raise ImportError(\n",
                "        'accelerate is required for CPU offload. '\n",
                "        'Install it with: pip install accelerate'\n",
                "    ) from exc\n",
                "\n",
                "prompt = '''\n",
                "A futuristic artificial intelligence research laboratory,\n",
                "large holographic screens showing neural networks,\n",
                "an advanced humanoid AI robot working at a computer,\n",
                "scientists analyzing data in the background,\n",
                "cinematic lighting, highly detailed, photorealistic,\n",
                "professional technology photography\n",
                "'''\n",
                "\n",
                "print('Generating image...')\n",
                "print(prompt)\n",
                "\n",
                "result = pipe(\n",
                "    prompt=prompt,\n",
                "    num_inference_steps=20,\n",
                "    width=512,\n",
                "    height=512\n",
                ")\n",
                "\n",
                "image = result.images[0]\n",
                "image.save('qwen_image_test.png')\n",
                "\n",
                "print('Image generated successfully!')\n",
                "print('Saved as qwen_image_test.png')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "display",
            "metadata": {},
            "outputs": [],
            "source": [
                "from IPython.display import display\n",
                "\n",
                "display(image)"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

with open("Qwen_Image_Test.ipynb", "w") as f:
    json.dump(notebook, f, indent=2)

print("Created: Qwen_Image_Test.ipynb")
