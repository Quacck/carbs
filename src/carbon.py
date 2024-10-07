from __future__ import annotations
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
import os


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
    
    def extend(self, factor: int, extra_columns: bool = False) -> CarbonModel:
        # right now this is not interpolated between sample points, perhaps
        # chaning this could be cool.
        df = self.df.loc[self.df.index.repeat(factor)].reset_index(drop=True)
        df["carbon_intensity_avg"] /= factor
        model = CarbonModel(self.name, df,self.carbon_start_index, self.carbon_error)
        return model     
        
    def __getitem__(self, index: int) -> np.Series:
        return self.df.iloc[index]['carbon_intensity_avg']


def get_carbon_model(carbon_trace: str, carbon_start_index: int, carbon_error:str = "ORACLE", extra_columns: bool = False) -> CarbonModel:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    relative_path = f"traces/{carbon_trace}.csv"
    absolute_path = os.path.join(script_dir, relative_path)
    df = pd.read_csv(absolute_path)

    # 17544 is 2 years
    # 720 is 24 * 30, so a whole month

    # change this to 720 * 2 for two months, as some traces are longer than a month

    # TODO: this does not quite work well yet.
    # the first implementation did an implicit +2 years on the start index,
    # which doesn't work for the DE trace

    # df = df[17544+carbon_start_index:17544+carbon_start_index+(720*2)]
    df = df[carbon_start_index:carbon_start_index+(720*2)]
    #df = pd.concat([df.copy(), df[:1000].copy()]).reset_index()
    df = df[["carbon_intensity_avg", *(["datetime", "timestamp"] if extra_columns else [])]]
    df["carbon_intensity_avg"] /= 1000
    c = CarbonModel(carbon_trace, df, carbon_start_index, carbon_error)
    return c
