# Simulation Code for Empirical Research Project

This simulation is set up to enable the estimation of various policies on KPIs such as the proportion of clients who run out service eligibility prior to completing needed service.
Currently, the main focus is on the effect of waitlist prioritization by classwhen waiting time does/does not have an effect on the number of appointments clients will require.

This is facilitated by using FCFS queues split by class.

Multithreading is leveraged throughout to enable fast simulation run times (currently ~20s/1000 epochs). This is particularly important as the data on discharged clients is written in chunks to parquet files in order to limit the memory overhead of the program.
