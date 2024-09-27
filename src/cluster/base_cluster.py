from abc import ABC, abstractmethod
import os

import pandas as pd
from carbon import CarbonModel
from task import Task, TIME_FACTOR
from threading import Lock

from typing import List, TypedDict

ON_DEMAND_COST_HOUR = 0.0624
SPOT_COST_HOUR = 0.01248  # 0.0341

class TaskDetails(TypedDict):
    ID: int
    arrival_time: int 
    length: int
    cpus: int
    length_class: str
    resource_class: str
    carbon_cost: float
    dollar_cost: float
    start_time: int
    waiting_time: int
    exit_time: int
    reason: str

class PhaseDetails(TypedDict):
    ID: int
    length: int
    carbon_cost: float
    dollar_cost: float
    start_time: int
    exit_time: int
    reason: str

class BaseCluster(ABC):
    def __init__(
        self,
        reserved_instances: int,
        carbon_model: CarbonModel,
        experiment_name: str,
        allow_spot: bool,
    ) -> None:
        """Common Cluster Configurations

        Args:
            reserved_instances (int): number of reserved instances
            carbon_model (CarbonModel): Carbon Intensity Model
            experiment_name (str): Hashed Configuration of tracking slurm tasks
            allow_spot (bool): Allow using Spot Instances
        """
        self.total_carbon_cost: float = 0.0
        self.total_dollar_cost: float = 0.0
        self.on_demand_cost = ON_DEMAND_COST_HOUR / (3600 / TIME_FACTOR)
        self.spot_cost = SPOT_COST_HOUR / (3600 / TIME_FACTOR)
        self.reserved_discount_rate = 0.4
        self.max_time = 0
        self.total_reserved_instances = reserved_instances
        self.available_reserved_instances = reserved_instances
        self.carbon_model = carbon_model
        self.details: List[TaskDetails] = []
        self.experiment_name = experiment_name
        self.runtime_allocation = [0] * carbon_model.df.shape[0]
        self.lock = Lock()
        self.allow_spot = allow_spot

    @abstractmethod
    def submit(self, current_time: int, task: Task) -> None:
        """Submit Tasks to the Cluster Queue

        Args:
            current_time (int): Time index
            task (Task): Submitted Task
        """
        pass

    @abstractmethod
    def refresh_data(self, current_time: int) -> None:
        """Release Allocated Resources, Only used in simulation

        Args:
            current_time (index): time index
        """
        pass

    def log_task(self, start_time: int, task: Task, dollar_cost: float, carbon: float, reason: str= "completed") -> None:
        waiting_time = start_time - task.arrival_time
        exit_time = start_time + task.task_length
        self.max_time = max(self.max_time, start_time)
        for i in range(start_time, exit_time + 1):
            self.runtime_allocation[i] += task.CPUs


        # okay lets try something crazy, instead of just logging the task, we'll also log each phase 
        for phase in task.power_consumption_function.phases:
            pass

        self.details.append(TaskDetails(
            ID = task.ID,
            arrival_time = task.arrival_time,
            length = task.task_length,
            cpus = task.CPUs,
            length_class = task.task_length_class,
            resource_class = task.CPUs_class,
            carbon_cost = carbon,
            dollar_cost = dollar_cost,
            start_time = start_time,
            waiting_time = waiting_time,
            exit_time = exit_time,
            reason = reason,
        ))

    @abstractmethod
    def save_results(
        self,
        cluster_type: str,
        scheduling_policy: str,
        carbon_policy: str,
        carbon_trace: str,
        task_trace: str,
        waiting_times_str: str,
        set_filename: str | None
    ) -> None:
        """Save Simulation Results

        Args:
            cluster_type (str): cluster Type
            scheduling_policy (str): scheduling algorithm
            carbon_policy (str): carbon waiting policy
            carbon_trace (str): carbon trace name
            task_trace (str): task trace name
            waiting_times_str (str): waiting times per queue
        """
        self.total_dollar_cost += (
            self.total_reserved_instances
            * self.reserved_discount_rate
            * self.max_time
            * self.on_demand_cost
        )
        self.details.append(TaskDetails(
            ID = -1,
            arrival_time = 0,
            length = 0,
            cpus = 0,
            length_class = '',
            resource_class = '',
            carbon_cost = 0,
            dollar_cost = self.total_reserved_instances
                * self.reserved_discount_rate
                * self.max_time
                * self.on_demand_cost,
            start_time = 0,
            waiting_time = 0,
            exit_time = 0,
            reason = '',
        ))
        df = pd.DataFrame(
            self.details,
            columns=[
                "ID",
                "arrival_time",
                "length",
                "cpus",
                "length_class",
                "resource_class",
                "carbon_cost",
                "dollar_cost",
                "start_time",
                "waiting_time",
                "exit_time",
                "reason",
            ],
        )
        # os.makedirs(f"results/{cluster_type}/{task_trace}/", exist_ok=True)

        details_filename = f"{set_filename}_details"
        # details_filename = f"{task_trace}/details-{scheduling_policy}-{self.carbon_model.carbon_start_index}-{carbon_policy}-{carbon_trace}-{self.total_reserved_instances}-{waiting_times_str}.csv"
        
        # file_name = f"results/{cluster_type}/{details_filename}"
        print(f"Saving details to {details_filename}")
        df.to_csv(details_filename, index=False)
        runtime_df = pd.DataFrame(self.runtime_allocation, columns=["cpus"])
        runtime_df["time"] = range(self.carbon_model.df.shape[0])
        runtime_df["time"] //= 60
        runtime_df = runtime_df.groupby("time").mean().reset_index()
        runtime_filename = f"{task_trace}/runtime-{scheduling_policy}-{self.carbon_model.carbon_start_index}-{carbon_policy}-{carbon_trace}-{self.total_reserved_instances}-{waiting_times_str}.csv"
        file_name = f"results/{cluster_type}/{runtime_filename}"
        print(f"Saving runtime to {file_name}")
        runtime_df.to_csv(file_name, index=False)

    # @abstractmethod
    # def sleep(self):
    #     """Sleep to allow execution, only effective in slurm clusters"""
    #     pass
 
    # @abstractmethod
    # def done(self):
    #     """Return True if cluster is idle, only effective in slurm clusters"""
    #     pass
