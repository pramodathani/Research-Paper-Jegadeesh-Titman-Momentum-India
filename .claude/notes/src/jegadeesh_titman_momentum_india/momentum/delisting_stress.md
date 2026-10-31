# delisting_stress.py

- The engine's OverlappingCohorts quietly removes a share that stops trading and spreads its weight over the rest (gap 27). The stress puts -100% or -30% in the month after the last return so the loss is charged. Renames before 2013 look like delistings, so the stress is an upper bound on the damage.
