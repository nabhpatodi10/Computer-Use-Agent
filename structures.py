from pydantic import BaseModel, Field

class Step(BaseModel):
    step: str = Field(description="A very simple step to be performed as a part of the plan")

class Plan(BaseModel):
    plan: list[Step] = Field(description="The detailed step by step plan to be followed to perform the task")

    @property
    def as_str(self) -> str:
        return "\n".join([f"{i+1}. {step.step}" for i, step in enumerate(self.plan)])
    
class Replan(BaseModel):
    replan: bool = Field(description="True if the task was completed, False if the task was not completed")

class ObjectName(BaseModel):
    name: str = Field(description="The name of the object or icon found in the screen")