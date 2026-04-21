from typing import Literal, TypedDict

class ModelRouterOutput(TypedDict):
    model: Literal["smart model", "fast model"]