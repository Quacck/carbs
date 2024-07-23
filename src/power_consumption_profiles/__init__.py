from typing import List, TypedDict, Callable
import numpy as np

class Phase(TypedDict):
    name: str
    duration: float
    power: float

class MachineLearningParameters(TypedDict):
    start_duration: float
    start_power: float
    training_duration: float
    training_power: float
    evaluate_duration: float
    evaluate_power: float
    save_duration: float
    save_power: float
    epochs: int

def get_power_policy(name: str, *args) -> Callable[[int], float]: # type: ignore[no-untyped-def]
    match name:
        case 'constant':
            # this would be the default GAIA job
            return lambda x: 1
        case 'constant-2':
            return lambda x: 2
        case 'linear':
            return lambda x: x
        case 'gradually-increasing':
            return lambda x: (x % 1000) + 1
        case 'ml':
            return create_profile_ml(args[0])
        case 'roberta':
            return create_phases_profile(roberta_phases)
        case 'phases':
            return create_phases_profile(list(args))
        case _:
            raise ValueError(f"Could not resolve {name} to a job profle")

# This is based on the phases in the power-measurements/evaluate.ipynb
# with a little cleanup (shortening the names and truncating the durations to 2 sig. digits)
roberta_phases: List[Phase] = [
    {'name': 'Start', 'duration': 5.349, 'power': 59.9},
    {'name': 'Finish Imports', 'duration': 12.36, 'power': 53.77},
    {'name': 'after load data', 'duration': 5.7513, 'power': 63.17}, 
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

def create_phases_profile(phases: List[Phase]) -> Callable[[int], float]:
    def profile(time: int) -> float:
        time_in_program: float = 0
        for phase in phases:
            start_of_this_phase = time_in_program
            end_of_this_phase = time_in_program + phase['duration']
            if start_of_this_phase <= time and time < end_of_this_phase:
                return phase['power']
            time_in_program += phase['duration']

                  
        return 0
    
    return profile

def create_profile_ml(params: MachineLearningParameters) -> Callable[[int], float]:
    phases = [
        Phase(name='Startup', duration=params['start_duration'], power=params['start_power']),
        *([
            Phase(name='Train', duration=params['training_duration'], power=params['training_power']),
            Phase(name='Evaluate', duration=params['evaluate_duration'], power=params['evaluate_power']),
            Phase(name='Save', duration=params['save_duration'], power=params['save_power']),
            
        ] * params['epochs'])
    ]
    return create_phases_profile(phases)

