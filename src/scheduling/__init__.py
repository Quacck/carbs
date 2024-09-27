from carbon import CarbonModel
from cluster import BaseCluster
from scheduling.suspend_phases_scheduling_policy import SuspendSchedulingDynamicPowerPolicy
from .scheduling_policy import SchedulingPolicy
from .suspend_scheduling_policy import SuspendSchedulingPolicy
from .carbon_waiting_policy import best_waiting_time, lowest_carbon_slot, oracle_carbon_slot,oracle_carbon_slot_waiting,average_carbon_slot_waiting


def create_scheduler(cluster: BaseCluster, scheduling_policy: str, carbon_policy: str, carbon_model: CarbonModel, dynamic_power: bool) -> SchedulingPolicy | SuspendSchedulingPolicy | SuspendSchedulingDynamicPowerPolicy:
    if (dynamic_power and carbon_policy != 'oracle' and (scheduling_policy != 'carbon' or scheduling_policy != "suspend-resume")):
        raise ValueError("Dynamic power profile not supported for {carbon_policy} and {scheduling_policy}")
    
    print(f"Finding scheduler for {carbon_policy} {scheduling_policy} {'with' if dynamic_power else 'without'} dynamic power")

    if carbon_policy == "waiting":
        start_time_policy = best_waiting_time
    elif carbon_policy == "lowest":
        start_time_policy = lowest_carbon_slot
    elif carbon_policy == "oracle":
        start_time_policy = oracle_carbon_slot
    elif carbon_policy == "cst_oracle":
        start_time_policy = oracle_carbon_slot_waiting
    elif carbon_policy == "cst_average":
        start_time_policy = average_carbon_slot_waiting
    else:
        raise Exception("Unknown Carbon Policy")

    # perhaps a completly unaware option that neiter optimizies for carbon or for cost should be added
    if scheduling_policy == "carbon":
        return SchedulingPolicy(cluster, carbon_model, start_time_policy, True, False, False)
    elif scheduling_policy == "carbon-spot":
        return SchedulingPolicy(cluster, carbon_model, start_time_policy, True, False, True)
    elif scheduling_policy == "carbon-cost":
        return SchedulingPolicy(cluster, carbon_model, start_time_policy, True, True, False)
    elif scheduling_policy == "carbon-cost-spot":
        return SchedulingPolicy(cluster, carbon_model, start_time_policy, True, True, True)
    elif scheduling_policy == "cost":
        return SchedulingPolicy(cluster, carbon_model, start_time_policy, False, True, False)
    elif scheduling_policy == "suspend-resume":
        if dynamic_power:
            return SuspendSchedulingDynamicPowerPolicy(cluster, carbon_model)
        return SuspendSchedulingPolicy(cluster, carbon_model, optimal=True)
    elif scheduling_policy == "suspend-resume-spot":
        return SuspendSchedulingPolicy(cluster, carbon_model, optimal=True)
    elif scheduling_policy == "suspend-resume-threshold": 
        return SuspendSchedulingPolicy(cluster, carbon_model, optimal=False)
    elif scheduling_policy == "suspend-resume-spot-threshold":
        return SuspendSchedulingPolicy(cluster, carbon_model, optimal=False)
    else:
        raise Exception("Unknown Experiment Type")
