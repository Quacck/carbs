from .profiles import Staged

def get_power_policy(name: str, *args):
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
            return periodically_changing
        case _:
            raise ValueError(f"Could not resolve {name} to a job profle")

def periodically_changing(time):
    period = time % 1000
    mode = period % 2 # metaphorically, either "training" (0) or "evaluating" (1)
    return (mode + 1) * 5 # 5 is just some arbitrary multiplier
