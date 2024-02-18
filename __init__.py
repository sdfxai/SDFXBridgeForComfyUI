from functools import reduce
from .libs.prompt_parser import get_learned_conditioning_prompt_schedules,conditioning_set_timeset_range_prompt_mapper
from .sdfx_path import load_sdfx_extra_path_config

load_sdfx_extra_path_config()

from .server import add_sdfx_routes
add_sdfx_routes()

class SDFXClipTextEncode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"text": ("STRING", {"multiline": True}), "clip": ("CLIP", )}}
    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"

    CATEGORY = "conditioning"

    def encode(self, clip, text):
        mapped_conditionings = list(map(conditioning_set_timeset_range_prompt_mapper(clip), (lambda p: get_learned_conditioning_prompt_schedules([text])[0])(text)))
        return (reduce(lambda a,b: a+b, mapped_conditionings), )

from nodes import SaveImage

def INPUT_TYPES(s):
    return {"required":
                {"images": ("IMAGE", ),
                "filename_prefix": ("STRING", {"default": "SDFX"})},
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
            }

SaveImage.INPUT_TYPES = classmethod(INPUT_TYPES)

# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "SDFXClipTextEncode": SDFXClipTextEncode
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "SDFXClipTextEncode": "SDFX Clip TextEncode (Prompt)"
}