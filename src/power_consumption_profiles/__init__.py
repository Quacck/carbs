from .profiles import Staged

def get_power_policy(name: str, *args):
    match name:
        case 'constant':
            # this would be the default GAIA job
            return Staged(dict({0: lambda x: 1}))
        case 'constant-2':
            return Staged(dict({0: lambda x: 2}))
        case 'gradually-increasing':
            return Staged(dict({
                0: lambda x: 1,
                1000: lambda x: 2,
                2000: lambda x: 3,
                3000: lambda x: 4
            }))
        case _:
            raise ValueError(f"Could not resolve {name} to a job profle")
