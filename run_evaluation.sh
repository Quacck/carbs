#!/bin/bash

chmod +x run_all_even_jobs.sh
chmod +x run_all_odd_jobs.sh

# parallelization could be better, but the gurobi license only allows two parallel sessions
sbatch -A polze -p magic \
    --container-image=python \
    --container-name=test-2 \
    --container-writable \
    --mem=128G \
    --cpus-per-task=128 \
    --time=24:0:0 \
    --comment="even" \
    --output=slurmlogs/output_%j.txt \
    --error=slurmlogs/error_%j.txt \
    --constraint=ARCH:X86 \
    --container-mounts=/hpi/fs00/home/vincent.opitz:/home/vincent.opitz \
    --container-workdir=/home/vincent.opitz/master-thesis/GAIA run_all_even_jobs.sh

sbatch -A polze -p magic \
    --container-image=python \
    --container-name=test-2 \
    --container-writable \
    --mem=128G \
    --cpus-per-task=128 \
    --time=24:0:0 \
    --comment="odd" \
    --output=slurmlogs/output_%j.txt \
    --error=slurmlogs/error_%j.txt \
    --constraint=ARCH:X86 \
    --container-mounts=/hpi/fs00/home/vincent.opitz:/home/vincent.opitz \
    --container-workdir=/home/vincent.opitz/master-thesis/GAIA run_all_odd_jobs.sh 