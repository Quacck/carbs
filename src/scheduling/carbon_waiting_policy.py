from typing import List
from task import Task, TIME_FACTOR
from carbon import CarbonModel
import numpy as np

class Schedule:
    def __init__(self, start_time: int, finish_time: int, carbon_cost: float) -> None:
        assert type(start_time) == int
        assert type(finish_time) == int

        self.start_time = start_time
        self.finish_time = finish_time
        self.carbon_cost = carbon_cost

    def actual_start_time(self, current_time: int) -> int:
        return current_time + self.start_time

    def actual_finish_time(self, current_time: int) -> int:
        return current_time + self.finish_time


def compute_carbon_consumption(task: Task, start_time: int, carbon_trace: CarbonModel) -> Schedule:
    """Compute Carbon Consumption

    Args:
        task (Task): Task
        start_time (int): start time index
        carbon_trace (CarbonModel):  Carbon Sub-trace of the permissible execution period

    Returns:
        Schedule: Execution Schedule
    """

    # the unit of the carbon_intensity is gCO₂eq/kWh
    execution_carbon = carbon_trace.df["carbon_intensity_avg"][start_time : start_time + task.task_length]
    assert len(execution_carbon) == task.task_length, "Trace is shorter than task"

    # in comparison to base GAIA, our jobs now cost a variable amount of energy over
    # their execution, the amount of energy required at a time is calculated by
    # the power consumption function.


    carbon_times_power_draw = np.empty_like(execution_carbon)
    for i in range (execution_carbon.shape[0]):
        time_in_job = task.total_execution_time + i
        # should check wether we need the task.CPUs or if they should go into the function anyway
        carbon_times_power_draw[i] = task.power_consumption_function(time_in_job) * execution_carbon.iloc[i] * task.CPUs

    carbon = carbon_times_power_draw.sum()
    return Schedule(start_time, start_time + task.task_length, carbon)


def lowest_carbon_slot(task: Task, carbon_trace: CarbonModel) -> Schedule:
    """Lowest Carbon Slot Policy that picks the carbon slot with the lowest carbon intensity

    Args:
        task (Task): current Task
        carbon_trace (CarbonModel): Carbon Sub-trace of the permissible execution period

    Returns:
        Schedule: Execution Schedule
    """
    if task.waiting_time != 0:
        start_time = int(carbon_trace.df[:task.waiting_time + 1]["carbon_intensity_avg"].idxmin())
    else:
        start_time = 0
    return compute_carbon_consumption(task, start_time, carbon_trace)


def oracle_carbon_slot(task: Task, carbon_trace: CarbonModel) -> Schedule:
    """Oracle Best Execution slot that uses the actual job length

    Args:
        task (Task): current Task
        carbon_trace (CarbonModel): Carbon Sub-trace of the permissible execution period

    Returns:
        Schedule: Execution Schedule
    """
    schedules: List[Schedule] = [compute_carbon_consumption(task, i, carbon_trace) for i in range(0, task.waiting_time + 1, 3600//TIME_FACTOR)]

    best_schedule = min(schedules, key=lambda x: x.carbon_cost)
    return best_schedule

def oracle_carbon_slot_waiting(task: Task, carbon_trace: CarbonModel) -> Schedule:
    """Oracle Carbon Saving per waiting time policy that uses the actual job length

    Args:
        task (Task): current Task
        carbon_trace (CarbonModel): Carbon Sub-trace of the permissible execution period

    Returns:
        Schedule: Execution Schedule
    """
    schedules = []
    CA = None
    for i in range(0, task.waiting_time + 1, 3600//TIME_FACTOR):
        s = compute_carbon_consumption(task, i, carbon_trace)
        schedules.append(s)            
        if i == 0:
            CA = s.carbon_cost

    if CA is None:
        raise BaseException('No CA')
    schedule = max(schedules, key=lambda x: (CA - x.carbon_cost)/(x.start_time+ task.task_length))
    return schedule

def average_carbon_slot_waiting(task: Task, carbon_trace: CarbonModel) -> Schedule:
    """Carbon Saving per waiting time policy that uses the average job length

    Args:
        task (Task): current Task
        carbon_trace (CarbonModel): Carbon Sub-trace of the permissible execution period

    Returns:
        Schedule: Execution Schedule
    """
    common_task = Task(task.ID, task.arrival_time,
                       task.expected_time, task.CPUs, 0, task.power_consumption_function)
    common_schedule = oracle_carbon_slot_waiting(common_task, carbon_trace)
    schedule = compute_carbon_consumption(
        task, common_schedule.start_time, carbon_trace)
    return schedule


def best_waiting_time(task: Task, carbon_trace: CarbonModel) -> Schedule:
    """Oracle Best Execution slot that uses the average job length

    Args:
        task (Task): current Task
        carbon_trace (CarbonModel): Carbon Sub-trace of the permissible execution period

    Returns:
        Schedule: Execution Schedule
    """
    common_task = Task(task.ID, task.arrival_time,
                       task.expected_time, task.CPUs, 0, task.power_consumption_function)
    common_schedule = oracle_carbon_slot(common_task, carbon_trace)
    schedule = compute_carbon_consumption(
        task, common_schedule.start_time, carbon_trace)
    return schedule
