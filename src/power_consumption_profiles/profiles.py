from typing import Dict, Callable
import pandas as pd

StagesDefinition = Dict[int, Callable[[int], float]]

class Staged:
    def __init__(self, stages: StagesDefinition):
        self.set_stages(stages)
        
    def __call__(self, time) -> float:
        index = self.stages[self.stages["start_time"] <= time].index[-1]
        stage = self.stages.loc[index]
        return stage["function"](time)

    def set_stages(self, stages: StagesDefinition) -> None:
        self.stages = pd.DataFrame(list(stages.items()), columns=["start_time", "function"]).sort_values(by="start_time")
        assert self.stages.iloc[0]["start_time"] == 0, "Power Profiles should start at 0"


