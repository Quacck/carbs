# Carbs: a carbon-aware scheduling testbed for power-heterogeneous jobs with startup overhead

This is part of my [master thesis](github.com/Quacck/master-thesis). 

It is an iteration on [GAIA](https://github.com/umassos/GAIA), which allows simulating the carbon-aware scheduling of jobs. 

To that I added job heterogeneity: along their execution, jobs now have different power demands. Additionally, starting a job carries an overhead, which impact suspend & resume scheduling. 

# Installation

```sh
pip3 install -r requirements.txt
```

# Usage

```sh
python3 src/run.py [arguments]
```

Examples of arguments can be found in `/jobs/`.






