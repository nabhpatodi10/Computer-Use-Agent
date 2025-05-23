from typing import Union
from pydantic import BaseModel, Field

class Step(BaseModel):
    step: str = Field(description="A very simple step to be performed as a part of the plan")

class Plan(BaseModel):
    plan: list[Step] = Field(description="The detailed step by step plan to be followed to perform the task")

    @property
    def as_str(self) -> str:
        return "\n".join([f"{i+1}. {step.step}" for i, step in enumerate(self.plan)])
    
class Replan(BaseModel):
    replan: Union[bool, Plan] = Field(description="If replanning required, it will be a new detailed step by step plan, else it will be false to denote that the entire plan has been followed or true if there are steps left to be followed.")