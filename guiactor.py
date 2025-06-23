import torch
from transformers import AutoProcessor

from gui_actor.modeling_qwen25vl import Qwen2_5_VLForConditionalGenerationWithPointer
from gui_actor.inference import inference

class GUIActor:
    def __init__(self, model = "microsoft/GUI-Actor-3B-Qwen2.5-VL"):
        self.__data_processor = data_processor = AutoProcessor.from_pretrained(model, max_pixels=768*768, use_fast=True)
        self.__tokenizer = data_processor.tokenizer
        __max_memory = {0: "7800MiB", "cpu": "26GiB"}

        self.__model = Qwen2_5_VLForConditionalGenerationWithPointer.from_pretrained(
            model,
            device_map={"": 0},
            max_memory=__max_memory,
            attn_implementation="flash_attention_2",
            torch_dtype=torch.bfloat16
        ).eval()

    def parse_image(self, image_path: str, object: str) -> tuple[float, float]:
        conversation = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a GUI agent. You are given an object and a screenshot of the screen. Identify the object on the given screen and return its coordinates.",
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image_path
                    },
                    {
                        "type": "text",
                        "text": object
                    },
                ],
            },
        ]

        with torch.inference_mode():
            pred = inference(
                conversation,
                self.__model,
                self.__tokenizer,
                self.__data_processor,
                use_placeholder=True,
                topk=3,
            )
        
        px, py = pred["topk_points"][0]
        return round(px, 4), round(py, 4)