from __future__ import annotations
from typing import List, Tuple, TypedDict, Any, Iterable, NotRequired
from functools import reduce
import numpy as np

class ModelParameters(TypedDict):
    startup: List[Phase]
    work: List[Phase]
    
class Phase(TypedDict):
    name: str
    duration: float
    power: float
    is_checkpoint: NotRequired[bool]

class PowerFunction:
    def __init__(self, phases: ModelParameters, name: str | None = None):
        self.name = name
        self.phases = phases
        self.duration_startup: float = np.sum([phase['duration'] for phase in phases['startup']])
        self.duration_work: float = np.sum([phase['duration'] for phase in phases['work']])
        self.duration = self.duration_startup + self.duration_work

    def __call__(self, time: float, time_worked: float = 0) -> float:
        '''
        :param time: current time since resume or execution start
        :param time_worked: seconds of work the job has had so far
        :return: power consumption in W
        '''
        
        if (time < self.duration_startup):
            return self.get_power_in_phases(self.phases['startup'], time)
        
        time_until_end = self.duration_startup + self.duration_work - time_worked

        if (time >= self.duration_startup and time < time_until_end):
            # find the last checkpoint we have reached
            remaining_time_worked: float = float(time_worked)             
            last_checkpoint: None | Phase = None
            for phase in self.phases['work']:
                if remaining_time_worked <= 0:
                    break
                remaining_time_worked -= phase['duration']
                if (phase.get('is_checkpoint', False)):
                    last_checkpoint = phase


            start_index_of_phase = self.phases['work'].index(last_checkpoint) + 1 if last_checkpoint is not None else 0

            return self.get_power_in_phases(self.phases['work'][start_index_of_phase: ], time - self.duration_startup)
        
        return 0
    
    def get_power_in_phases(self, phases: Iterable[Phase], time: float) -> float:

        time_in_program = 0.0
        for phase in phases:
            start_of_this_phase = time_in_program
            end_of_this_phase = time_in_program + phase['duration']
            if start_of_this_phase <= time and time < end_of_this_phase:
                return phase['power']
            time_in_program += phase['duration']
 
        return 0


class MachineLearningParameters(TypedDict):
    """
    Parameters for the helpter function that create ModelParameters for a ML Job, 
    as found out during my experiments
    """
    start_duration: float
    start_power: float
    training_duration: float
    training_power: float
    evaluate_duration: float
    evaluate_power: float
    save_duration: float
    save_power: float
    epochs: int

def get_power_policy(name: str, args: Any) -> PowerFunction: # type: ignore[no-untyped-def]
    match name:
        case 'constant':
            # this would be the default GAIA job
            return PowerFunction({'startup': [], 'work': [Phase(name='Constant', duration=float('inf'), power=args)]}, 'Constant')
        case 'mocked-constant-from-phases':
            # this would be the default GAIA job
            return phases_to_constant_via_average(args)
        case 'ml':
            assert args is not None, "Power profile has no arguments supplied"
            return create_profile_ml(args)
        case 'roberta':
            return create_phases_profile(roberta_phases_spec)
        case 'phases':
            assert args is not None, "Power profile has no arguments supplied"
            return create_phases_profile(args)
        case _:
            raise ValueError(f"Could not resolve {name} to a job profle")

# This is based on the phases in the power-measurements/evaluate.ipynb
# with a little cleanup (shortening the names and truncating the durations to 2 sig. digits)
roberta_phases_spec: ModelParameters = {
    'startup': [
        {'name': 'Start', 'duration': 5.349, 'power': 59.9},
        {'name': 'Finish Imports', 'duration': 12.36, 'power': 53.77},
        {'name': 'after load data', 'duration': 5.7513, 'power': 63.17}, 
    ],
    'work': [
        {'name': 'Start training', 'duration': 8.171, 'power': 221.93}, 
        {'name': 'Epoch 1.0 ended', 'duration': 1.5477, 'power': 134.0}, 
        {'name': 'Evaluate5', 'duration': 2.720, 'power': 105.1}, 
        {'name': 'Epoch 1.0. Saved', 'duration': 7.437, 'power': 235.37}, 
        {'name': 'Epoch 2.0 ended', 'duration': 1.5130, 'power': 139.88}, 
        {'name': 'Evaluate', 'duration': 2.698, 'power': 114.09}, 
        {'name': 'Epoch 2.0. Saved', 'duration': 7.430, 'power': 239.19},
        {'name': 'Epoch 3.0 ended', 'duration': 1.4680, 'power': 143.62},
        {'name': 'Evaluate', 'duration': 2.679, 'power': 112.46},
        {'name': 'Epoch 3.0. Saved', 'duration': 7.453, 'power': 238.28},
        {'name': 'Epoch 4.0 ended', 'duration': 1.5398, 'power': 141.87},
        {'name': 'Evaluate', 'duration': 2.669, 'power': 112.87},
        {'name': 'Epoch 4.0. Saved', 'duration': 7.455, 'power': 236.59},
        {'name': 'Epoch 5.0 ended', 'duration': 1.514, 'power': 146.69},
        {'name': 'Evaluate', 'duration': 2.668, 'power': 107.83},
        {'name': 'End training', 'duration': 1.5576, 'power': 123.31}
    ]
}

def create_phases_profile(modelParameters: ModelParameters) -> PowerFunction:
    return PowerFunction(modelParameters, 'Phases')

def reduce_phase(total: Tuple[float, float], phase: Phase) -> Tuple[float, float]:
    return total[0]+phase['power']*phase['duration'], total[1]+phase['duration']

def phases_to_constant_via_average(phases: List[Phase]) -> PowerFunction:
    """
    Take some phases and output a constant function that ideally integrates to the same amount of power over its execution.
    Sounds useless, but this should give us the ability to compare the scheduling of some dynamic job vs. a constant job.
    The scheduling itself would likely not be impacted (between different constant draws), but alteast we'd get some human
    readable numbers out.
    """

    total_power, total_duration = reduce(reduce_phase, phases, (0,0)) # type: ignore 
    average_power = total_power / total_duration
    return PowerFunction({
        'startup': [],
        'work' : [{'name': 'Constant', 'duration': total_duration, 'power': average_power}]
    }, 'Constant from Phase')

def create_profile_ml(params: MachineLearningParameters) -> PowerFunction:
    modelParameters: ModelParameters = {
        'startup': [Phase(name='Startup', duration=params['start_duration'], power=params['start_power'])],
        'work': [
            Phase(name='Train', duration=params['training_duration'], power=params['training_power']),
            Phase(name='Evaluate', duration=params['evaluate_duration'], power=params['evaluate_power']),
            Phase(name='Save', duration=params['save_duration'], power=params['save_power']),
        ] * params['epochs']
    }

    return create_phases_profile(modelParameters)

