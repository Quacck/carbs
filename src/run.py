#!/usr/bin/env python3
import argparse
from typing import List
import pandas as pd
from carbon import get_carbon_model, CarbonModel
from task import Task, set_waiting_times, load_tasks, TIME_FACTOR
from scheduling import create_scheduler
from cluster import create_cluster
import hashlib
import time
import os


def run_experiment(
    carbon_start_index: int,
    carbon_model: CarbonModel,
    tasks: List[Task],
    scheduling_policy: str,
    carbon_policy: str,
    reserved_instances: int,
    task_trace: str,
    waiting_times_str: str,
    cluster_partition: str,
) -> List[float]:
    """Run Experiments

    Args:
        carbon_start_index (int): carbon trace start time
        scheduling_policy (str): scheduling algorithm
        carbon_policy (str): carbon waiting policy
        reserved_instances (int): number of reserved instances
        waiting_times_str (str): waiting times per queue
        task_trace (str): Task Trace
        waiting_times_str (str): waiting times per queue
        cluster_partition (str): used cluster partition (queue), only for slurm experiment.

    Returns:
        List: Results
    """
    experiment_name = hashlib.md5(
        f"{carbon_model.name}-{carbon_start_index}-{scheduling_policy}-{carbon_policy}-{waiting_times_str}-{reserved_instances}-{task_trace}-{cluster_partition}".encode()
    ).hexdigest()[:10]
    cluster = create_cluster(
        scheduling_policy,
        carbon_model,
        reserved_instances,
        experiment_name,
        waiting_times_str,
        cluster_partition,
    )
    scheduler = create_scheduler(
        cluster, scheduling_policy, carbon_policy, carbon_model
    )

    for task in tasks:
        current_time = task.arrival_time
        print(current_time)
        scheduler.submit(current_time, task)

        with cluster.lock:
            scheduler.execute(current_time)
        cluster.sleep()    

    # previous implementation of submitting all jobs?
    #for i in range(0, carbon_model.df.shape[0]):
    #    print(i)
    #    current_time = i
    #    while len(tasks) > 0:
    #        if tasks[0].arrival_time <= current_time:
    #            if tasks[0].task_length > 0:
    #                scheduler.submit(current_time, tasks[0])
    #            del tasks[0]
    #        else:
    #            break
    #    with cluster.lock:
    #        scheduler.execute(current_time)
    #    cluster.sleep()
    #    if len(tasks) == 0 and scheduler.queue.empty() and cluster.done():
    #        break

    cluster.save_results(
        "simulation",
        scheduling_policy,
        carbon_policy,
        carbon_model.name,
        task_trace,
        waiting_times_str,
    )
    return [cluster.total_carbon_cost, cluster.total_dollar_cost]


def prepare_experiment(
    carbon_start_index: int,
    carbon_trace: str,
    task_trace: str,
    scheduling_policy: str,
    carbon_policy: str,
    reserved_instances: int,
    waiting_times_str: str,
    cluster_partition: str,
    repeat: bool,
    dynamic_power: bool,
) -> None:
    """Prepare and Run Experiment

    Args:
        carbon_start_index (int): carbon trace start time
        carbon_trace (str): carbon trace name
        task_trace (str): task trace name
        scheduling_policy (str): scheduling algorithm
        carbon_policy (str): carbon waiting policy
        reserved_instances (int): number of reserved instances
        waiting_times_str (str): waiting times per queue
        cluster_partition (str): used cluster partition (queue), only for slurm experiment.
        dynamic_power (bool): wether jobs use constant or dynamic power over their execution
    """

    file_name = f"results/simulation/{task_trace}/{scheduling_policy}-{carbon_start_index}-{carbon_policy}-{carbon_trace}-{reserved_instances}-{waiting_times_str}.csv"

    if os.path.exists(file_name) and repeat == False:
        print(f"Skipping Experiments {task_trace} - {carbon_trace}-{scheduling_policy}-{carbon_policy}-{waiting_times_str}, and {reserved_instances} reserved because the results already exists and repeat parameter not set")
        return
    

    print(
        f"Start Experiments {task_trace} - {carbon_trace}-{scheduling_policy}-{carbon_policy}-{waiting_times_str}, and {reserved_instances} reserved"
    )
    set_waiting_times(waiting_times_str)
    carbon_model = get_carbon_model(carbon_trace, carbon_start_index)
    tasks = load_tasks(task_trace, dynamic_power)
    carbon_model = carbon_model.extend(int(3600 / TIME_FACTOR))
    results = []
    result = run_experiment(
        carbon_start_index,
        carbon_model,
        tasks,
        scheduling_policy,
        carbon_policy,
        reserved_instances,
        task_trace,
        waiting_times_str,
        cluster_partition,
    )
    results.append(result)

    results_df = pd.DataFrame(results, columns=["carbon_cost", "dollar_cost"])
    print(
        f"Saving Results to {file_name}"
    )
    results_df.to_csv(file_name, index=False)
    print(
        f"Finish Experiments {task_trace} - {carbon_trace}-{scheduling_policy}-{carbon_policy}-{waiting_times_str}, and {reserved_instances} reserved"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GAIA: Carbon Aware Scheduling Policies"
    )
    parser.add_argument(
        "-c",
        "--carbon-trace",
        default="AU-SA",
        type=str,
        dest="carbon_trace",
        help="Carbon Trace",
    )
    parser.add_argument(
        "-t",
        "--task-trace",
        default="scorelab",
        type=str,
        dest="task_trace",
        help="Task Trace",
    )
    parser.add_argument(
        "-r",
        "--reserved-instances",
        type=int,
        default=0,
        dest="reserved_instances",
        help="Reserved Instances",
    )
    parser.add_argument(
        "-w",
        "--waiting-times",
        type=str,
        default="6x24",
        dest="waiting_times_str",
        help="Waiting times per queue `x` separated",
    )
    parser.add_argument(
        "--scheduling-policy",
        default="suspend-resume-threshold",
        dest="scheduling_policy",
        choices=[
            "carbon",
            # "carbon-spot",
            "carbon-cost",
            # "carbon-cost-spot",
            "cost",
            "suspend-resume",
            # "suspend-resume-spot",
            "suspend-resume-threshold",
            # "suspend-resume-spot-threshold",
        ],
    )

    # it'd probably be nicer if this wasn't some abstract index but maybe an iso date or something like that
    parser.add_argument(
        "-i",
        "--start-index",
        type=int,
        default=7000,
        dest="start_index",
        help="carbon start index",
    )

    parser.add_argument(
        "--dynamic-power-draw",
        default=False,
        dest="dynamic_power_draw",
        action=argparse.BooleanOptionalAction, 
        help="If executed jobs have a power draw depending on time. The default of False means that all jobs have a constant draw (this is the GAIA default)."
    )

    parser.add_argument(
        "--carbon-policy",
        default="oracle",
        dest="carbon_policy",
        choices=["waiting", "lowest", "oracle", "cst_oracle", "cst_average"],
    )
    parser.add_argument(
        "-p", "--cluster-partition", default="queue1", dest="cluster_partition"
    )
    parser.add_argument(
        '--repeat', 
        default=True,
        dest="repeat",
        action=argparse.BooleanOptionalAction, 
        help='Repeat experiments that are saved already')


    args = parser.parse_args()
    carbon_start_index = []
    if args.start_index == -1:
        carbon_starts = range(0, 8500, 500)
    else:
        carbon_starts = [args.start_index]
    for carbon_start_index in carbon_starts:
        prepare_experiment(
            carbon_start_index,
            args.carbon_trace,
            args.task_trace,
            args.scheduling_policy,
            args.carbon_policy,
            args.reserved_instances,
            args.waiting_times_str,
            args.cluster_partition,
            args.repeat,
            args.dynamic_power_draw
        )


if __name__ == "__main__":
    main()
