from enum import Enum
import timeit
from typing import List, Callable
import pandas as pd
import power_consumption_profiles as pcp

# since we only simulate things right now, we dont need to accelerate tasks by 5x
# as state in the paper
TIME_FACTOR = 1

waiting_times = None
average_length = None


class TwoQueues(Enum):
    Short = 7200/TIME_FACTOR  # < 2
    Long = 86400/TIME_FACTOR


def set_average_length(av_l):
    global average_length
    average_length = av_l


def set_waiting_times(waiting_times_str: str):
    global waiting_times
    
    # convert the waiting time in hours to seconds
    waiting_times = [float(hour_string)*3600/TIME_FACTOR for hour_string in waiting_times_str.split("x")]


def get_expected_time(task_length_hours: float) -> (int, int, str):
    """Get expected time based on task length. It is used to estimate the task length upon arrival.

    Args:
        task_length_hours (float): Task length
        

    Raises:
        Exception: Wrong waiting time array

    Returns:
        int: Expected length
        int: Waiting Time
        str: Queue Name
    """    
    global average_length
    global waiting_times

    if len(waiting_times) == 1:
        return 2, waiting_times[0], 'Same'
    elif len(waiting_times) == 2:
        if task_length_hours < TwoQueues.Short.value:
            return average_length[0], waiting_times[0], TwoQueues.Short.name
        else:
            return average_length[1], waiting_times[1], TwoQueues.Long.name
    else:
        raise Exception("Not covered")


def classify_time(length):
    """Map Task length to length class

    Args:
        length (int): job length

    Returns:
        str: length class
    """    
    length = length / (3600/TIME_FACTOR)
    if length <= 2:
        return "0-2"
    elif length <= 4:
        return "2-6"
    elif length <= 8:
        return "6-12"
    elif length <= 16:
        return "12-24"
    elif length <= 48:
        return "24-48"
    else:
        return "48+"


def classify_resources(x):
    """Map Task resources to resources class

    Args:
        resources (int): job resources

    Returns:
        str: resources class
    """  
    if x == 1:
        return "1"
    elif x == 2:
        return "2"
    elif x <= 4:
        return "3-4"
    elif x <= 8:
        return "5-8"
    elif x <= 16:
        return "9-16"
    elif x <= 32:
        return "17-32"
    elif x <= 64:
        return "33-64"
    else:
        return "64+"


class Task:
    def __init__(self, id:int, arrival_time: float, task_length: float, CPUs: int, total_execution_time: int = 0, power_consumption_function: Callable[[int], float] = lambda seconds_since_start: seconds_since_start) -> None:
        """Task Class

        Args:
            id (int): task ID
            arrival_time (float): arrival time
            task_length (float): task length
            CPUs (int): number of CPUs
            power_consumption_function: function that takes (seconds since beginning of job) and returns energy usage in Wh
        """
        self.ID = id
        self.arrival_time = int(arrival_time)
        self.task_length = max(int(task_length), 1)
        self.task_length_class = classify_time(task_length)
        expected_time, waiting_time, queue = get_expected_time(
            self.task_length)
        self.expected_time = int(expected_time)
        self.CPUs = int(CPUs)
        self.CPUs_class = classify_resources(self.CPUs)
        self.queue = queue
        self.waiting_time = int(waiting_time)
        self.total_execution_time = total_execution_time
        self.power_consumption_function = power_consumption_function


def load_tasks(trace_name:str) -> List[Task]:
    """Load Task Trace

    Args:
        trace_name (str): trace name

    Returns:
        List[Task]: List of Tasks
    """
    print(f"Started Loading Tasks for {trace_name}")
    start = timeit.default_timer()
    tasks = []
    df = pd.read_csv(
        f"src/cluster_traces/{trace_name}.csv")
    df["arrival_time"]/= TIME_FACTOR
    df["length"]/= TIME_FACTOR
    av_l = [df[df["length"] <= TwoQueues.Short.value]["length"].mean(
    ), df[df["length"] >= TwoQueues.Short.value]["length"].mean()]
    set_average_length(av_l)
    print(f"{trace_name} average {av_l[1]}")
    # df = df[:10000]
    #ids = df["id"].unique()
    for id, row in df.iterrows():
        job_name: str = row.get("name", 'constant')
        power_consumption = pcp.get_power_policy(job_name)

        # currently, only jobs longer than an hour are supported because
        # the jobs are submitted to the cluster on an hour-basis
        # assert row["length"] >= 300/TIME_FACTOR, "Too short Job"
        tasks.append(Task(id, row["arrival_time"],
                          row["length"], row["cpus"], total_execution_time=0, power_consumption_function=power_consumption))
    #assert len(ids) == len(tasks)
    print(f"Loading {trace_name} tasks took {timeit.default_timer()-start}")
    return tasks
