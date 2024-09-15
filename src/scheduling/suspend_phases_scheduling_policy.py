from __future__ import annotations
from carbon import CarbonModel
from power_consumption_profiles import PowerFunction
from task import TIME_FACTOR, Task
from queue import PriorityQueue
from cluster import BaseCluster
from typing import Dict, List

import pulp
from functools import reduce



class QueueObject:
    def __init__(self, task: Task, max_start_time: int, priority: int):
        self.task = task
        self.max_start_time = max_start_time
        self.priority = priority

    def __lt__(self, other: QueueObject) -> bool:
        return self.priority < other.priority

class SuspendSchedulingDynamicPowerPolicy:
    """Scheduling policy that takes into account that jobs may have a startup phase on resuming,
    jobs now also have (multiple) phases that each have a different power draw.

    This uses a linear programming approach to optimize the emitted carbon.
    """

    def __init__(self, cluster: BaseCluster, carbon_model: CarbonModel) -> None:
        self.cluster: BaseCluster = cluster
        self.carbon_model: CarbonModel = carbon_model
        self.queue: PriorityQueue[QueueObject] = PriorityQueue()

    def submit(self, current_time: int, task: Task) -> None:
        """Split Task to multiple jobs (suspend-resume) and submit them to GAIA Queue

        Args:
            current_time (int): time index
            task (Task): Task
        """

        sub_tasks = []
        start_times = []
        tasks = 0
        i = 0
        total_execution_time = 0

        schedule = self.find_execution_times(self.carbon_model, task.waiting_time, task.power_consumption_function)

        while i < len(schedule):
            if schedule[i] == 0:
                i += 1
                continue
            start = i
            while i < len(schedule) and schedule[i] == 1:
                i = i + 1
            
            task_length = i - start
            subtask = Task(task.ID, current_time, task_length, task.CPUs, total_execution_time, task.power_consumption_function)
            
            # we need to keep track of how long each task has run so far, so we can properly call the power consumption
            total_execution_time += task_length
            subtask.task_length_class = task.task_length_class
            sub_tasks.append(subtask)
            start_times.append(start)
            tasks += 1
            
        assert tasks >= 1 and tasks == len(sub_tasks)
        if tasks == 1:
            self.queue.put(
                QueueObject(task, current_time + start_times[0], task.arrival_time)
            )
        else:
            for i, subtask in enumerate(sub_tasks):
                self.queue.put(
                    QueueObject(
                        subtask, current_time + start_times[i], task.arrival_time
                    )
                )

    def execute(self, current_time: int) -> None:
        """Submit ready job/subjob to the simulated or real cluster queue

        Args:
            current_time (int): time index
        """
        queue: PriorityQueue[QueueObject] = PriorityQueue()
        while not self.queue.empty():
            queue_object = self.queue.get()
            if current_time >= queue_object.max_start_time:
                self.cluster.submit(current_time, queue_object.task)
            else:
                queue.put(queue_object)
        self.queue = queue
        self.cluster.refresh_data(current_time)

    def find_execution_times(self, carbon_trace: CarbonModel, DEADLINE: int, model: PowerFunction) -> List[int]:
        # Define the problem
        prob = pulp.LpProblem("StopResumeCarbonAwareScheduling", pulp.LpMinimize)

        # The carbon trace is given in hours
        seconds_carbon_trace = carbon_trace.extend(1)
        seconds_carbon_trace.df = seconds_carbon_trace.df.head(DEADLINE)

        # Example data
        WORK_LENGTH = int(model.duration_work)  # Processing time for the job
        STARTUP_LENGTH = int(model.duration_startup) # Startup time for the job

        # This just needs to be a big number that otherwise won't occur during the LP process
        # basically just an occult LP-Hack
        M = DEADLINE * 2 

        carbon_cost_at_time = seconds_carbon_trace.df['carbon_intensity_avg'].to_dict()

        starting = pulp.LpVariable.dicts("starting", (t for t in range(DEADLINE)), cat="Binary")
        startup_finished = pulp.LpVariable.dicts("start", (t for t in range(DEADLINE)), cat="Binary")
        work = pulp.LpVariable.dicts("work", (t for t in range(DEADLINE)), cat="Binary")

        # This one will count up the seconds since each start, so we can calculate how which phase we are in
        work_time_progressed = pulp.LpVariable.dict("work_time_progressed", (t for t in range(DEADLINE)), lowBound=0, upBound=WORK_LENGTH, cat=pulp.LpInteger)

        # This one will count up the seconds since each start, so we can calculate how which phase we are in
        startup_time_progressed = pulp.LpVariable.dict("startup_time_progressed", (t for t in range(DEADLINE)), lowBound=0, upBound=STARTUP_LENGTH, cat=pulp.LpInteger)

        # set time_progressed to 0, whenever we start
        for t in range(DEADLINE-1):
            #https://download.aimms.com/aimms/download/manuals/AIMMS3OM_IntegerProgrammingTricks.pdf 
            if (t>0):
                # be bigger than the previous value IF starting
                prob += startup_time_progressed[t] >= startup_time_progressed[t-1] + 1 - (1 - starting[t]) * M
                prob += startup_time_progressed[t] <= startup_time_progressed[t-1] + 1 + (1 - starting[t]) * M

            # IF not starting, be 0
            prob += startup_time_progressed[t] <= starting[t] * M 

            prob += work_time_progressed[0] == 0
            if (t > 0):
                prob += work_time_progressed[t] == work_time_progressed[t-1] + work[t]

        # we need to linearize our phases.
        # we do that by creating a boolean dict which will be true for each time the phase is active
        phases = model.phases

        # avert your eyes, for this is cringe
        lin_function_dicts: Dict[str, Dict[str, Dict[str, pulp.LpVariable | float]]] = { }

        running_index = 0

        for phase_key, phases_of_key in phases.items():
            duration = 0
            if len(phases_of_key) == 0:
                continue

            lin_function_dicts[phase_key] = { }

            progress_variable = startup_time_progressed if phase_key == 'startup' else work_time_progressed
            state_variable = starting if phase_key == 'startup' else work

            for phase in phases_of_key:

                phase_name = phase['name'] + str(running_index)
                running_index += 1
                phase_variable_lower = pulp.LpVariable.dict(phase_name + "_lower", (t for t in range(DEADLINE)), cat="Binary")
                phase_variable_upper = pulp.LpVariable.dict(phase_name + "_upper", (t for t in range(DEADLINE)), cat="Binary")
                phase_variable = pulp.LpVariable.dict(phase_name, (t for t in range(DEADLINE)), cat="Binary")
                lin_function_dicts[phase_key][phase_name] = { }
                lin_function_dicts[phase_key][phase_name]['variable'] = phase_variable
                lin_function_dicts[phase_key][phase_name]['upper'] = phase_variable_upper
                lin_function_dicts[phase_key][phase_name]['lower'] = phase_variable_lower
                lin_function_dicts[phase_key][phase_name]['power'] = phase['power']

                # bounds are [lower, upper) for each phase
                lower_bound = max(duration, 0) 
                upper_bound = duration + 1 + int(phase["duration"])

                print(f'{phase_name} must be between {lower_bound} and {upper_bound}')

                for t in range(DEADLINE):

                    #https://math.stackexchange.com/a/3260529 this is basically magic
                    # this activates the phase_variable within (lower, upper)

                    prob += progress_variable[t] - lower_bound <= M*phase_variable_lower[t]
                    prob += lower_bound - progress_variable[t] <= M*(1-phase_variable_lower[t])

                    prob += upper_bound - progress_variable[t] <= M*phase_variable_upper[t]
                    prob += progress_variable[t] - upper_bound <= M*(1-phase_variable_upper[t])

                    prob += phase_variable[t] >= phase_variable_lower[t] + phase_variable_upper[t] + state_variable[t] - 2
                    prob += phase_variable[t] <= phase_variable_lower[t]
                    prob += phase_variable[t] <= phase_variable_upper[t]
                    prob += phase_variable[t] <= state_variable[t]
                
                duration += int(phase["duration"])

        # our carbon cost is equal to each phase being active * its power * the amount of carbon per timeslot
        all_phase_variables_with_power = []

        for overarching_phase in lin_function_dicts.values():
            for phase_entry in overarching_phase.values():
                all_phase_variables_with_power.append((phase_entry['variable'], phase_entry['power']))

        def carbon_cost_at_timeslot(t: int) -> pulp.LpProblem:
            return reduce(lambda problem, phase_tuple: problem + phase_tuple[0][t] * phase_tuple[1] * carbon_cost_at_time[t], all_phase_variables_with_power, pulp.LpAffineExpression())

        prob += pulp.lpSum([carbon_cost_at_timeslot(t) for t in range(DEADLINE)]) 
        # prob += pulp.lpSum([starting[t] * carbon_cost_at_time[t] + work[t] * carbon_cost_at_time[t] for t in range(DEADLINE)]) 


        # spend enough time processing
        prob += pulp.lpSum(work[t] for t in range(STARTUP_LENGTH, DEADLINE)) == WORK_LENGTH
        prob += pulp.lpSum(work[t] for t in range(STARTUP_LENGTH)) == 0

        for t in range(DEADLINE - 1):
            # Ensure the job undergoes the startup phase whenever it resumes
            # if [0 , 1], this will be 1
            # t1   t2
            # 0     0 => 0
            # 0     1 => 1 
            # 1     0 => -1 / 0
            prob += startup_finished[t] >= work[t + 1] - work[t]

            # we can not be in startup and work at the same time
            prob += startup_finished[t] + work[t] <= 1
            prob += starting[t] + work[t] <= 1


        for i in range(STARTUP_LENGTH - 1, DEADLINE):
            prob += pulp.lpSum([starting[i - j] for j in range(STARTUP_LENGTH)]) >= STARTUP_LENGTH * startup_finished[i], f"Contiguity_{i}"


        # The solution so far seems to take a really long time, let's also add a maximum amount of startups to hopefully reduce the search space
        prob += pulp.lpSum([startup_finished[j] for j in range(DEADLINE)]) <= 5, f"Max_starts"

        solver = pulp.GUROBI_CMD(timeLimit=60 * 20)

        prob.solve(solver)

        print(f"Status: {pulp.LpStatus[prob.status]}")

        schedule = [0] * DEADLINE

        for t in range(DEADLINE):
            is_in_startup = pulp.value(starting[t]) is not None and pulp.value(starting[t])  > 0
            is_working = pulp.value(work[t]) is not None and pulp.value(work[t])  > 0

            if (is_in_startup or is_working):
                schedule[t] = 1

        return schedule
