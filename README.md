# Human Behavior Modeling with Passive Monitoring

## Description

This repository includes the code of each of the component programs that are part of the programmatic solution for the "Human Behavior Modeling with Passive Monitoring" Final Degree Project (TFG) by Diego Herrero Quevedo for the Degree in Data Science and Engineering. This TFG was jointly supervised by Pablo Martínez Olmos and Antonio Artés Rodríguez.

## Structure

Most of the modules in which the repository is structured correspond to one of the functional components of the solution. The modules are structurally divided in two contexts. The first context relates to the creation of an unified data matrix that is adequeate to solve a regression problem. The second context relates to the solution to the regression problem itself.

### Data engineering problem

The modules that are involved in the creation of the unified data matrix for regression are:

- [csv](./csv): data unification component. Extracts unified data matrix from the Databases for PostgreSQL instance.
- [postgre](./postgre): data processing component. Updates the Databases for PostgreSQL instance from data arriving to a COS bucket.
- [startup](./startup): initialization script for local execution. Connects to the local machine through VPN to IBM Cloud and initializes the watchdog component on local execution.
- [toolchain](./toolchain): continuous delivery component. Tracks changes in the directory and rebuilds Code Engine jobs when a new change is pushed.
- [utils](./utils): utilities component. Implements functionality for authenticating to an IBM Cloud account and connecting to a COS instance.
- [watchdog](./watchdog): data extraction component. Observes export directories and uploads any data written to the directory to a COS instance.

### Data science probem

The scripts involved in solving the regression problem are contained in the module [data](./data). These include:

- ```process.ipynb```: data matrix processing component. Performs data exploration and processing tasks to prepare the data matrix for model training.
- ```train.ipynb```: model evaluation component. Executes the nested cross-validation scheme for model evaluation.
- ```visualize.ipynb```: results visualization component. Depicts evaluation results in plots and tables that are easy to interpret and analyze.
