from __future__ import annotations
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame


class CarbonModel():

    def __init__(self, name: str, df: DataFrame, carbon_start_index: int, carbon_error: str) -> None:
        self.name = name
        self.df = df
        self.carbon_start_index = carbon_start_index
        self.carbon_error = carbon_error
        self.mean = self.df["carbon_intensity_avg"].mean()
        self.std = self.df["carbon_intensity_avg"].std()

    def reindex(self, index: int) -> CarbonModel:
        df = self.df[index:].copy().reset_index()
        model = CarbonModel(self.name, df, self.carbon_start_index, self.carbon_error)
        return model

    def subtrace(self, start_index: int, end_index: int) -> CarbonModel:
        df = self.df[start_index: end_index].copy().reset_index()
        model = CarbonModel(self.name, df,self.carbon_start_index, self.carbon_error)
        return model
    
    def extend(self, factor: int) -> CarbonModel:
        # right now this is not interpolated between sample points, perhaps
        # chaning this could be cool.
        df = pd.DataFrame(np.repeat(self.df.values, factor, axis=0), columns=["carbon_intensity_avg"])
        df["carbon_intensity_avg"] /= factor
        model = CarbonModel(self.name, df,self.carbon_start_index, self.carbon_error)
        return model     
        
    def __getitem__(self, index: int) -> np.Series:
        return self.df.iloc[index]['carbon_intensity_avg']


def get_carbon_model(carbon_trace: str, carbon_start_index: int, carbon_error:str = "ORACLE") -> CarbonModel:
    df = pd.read_csv(f"src/traces/{carbon_trace}.csv")

    # 17544 is 2 years
    # 720 is 24 * 30, so a whole month

    # change this to 720 * 2 for two months, as some traces are longer than a month

    df = df[17544+carbon_start_index:17544+carbon_start_index+(720*2)]
    #df = pd.concat([df.copy(), df[:1000].copy()]).reset_index()
    df = df[["carbon_intensity_avg"]]
    df["carbon_intensity_avg"] /= 1000
    c = CarbonModel(carbon_trace, df, carbon_start_index, carbon_error)
    return c
