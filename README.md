# Great Expectations Pipeline Tests for scikit-learn

This repository is an example for how the [**great_expectations**](https://github.com/great-expectations/great_expectations) 
library could be integrated with a scikit-learn machine learning pipeline to ensure that data 
inputs, transformed data, and even the model predictions conform to an expected standard. 

## Table of Contents

 - [Background](#background)
 - [Project Folder Structure](#project-folder-structure)
 - [Pipeline](#pipeline)
 - [Creating Expectations](#creating-expectations)


---

### Background

In this example assume that we want to build a machine learning pipeline to 
estimate the weight of two species of birds. Along with the species we have other  
attributes such as, color, beak_ratio, claw_length, and wing_density. This is fake 
data that was generated using the script [lib/datagenerator.py](./lib/datagenerator.py). 
The raw data is available at [data/raw-data.csv](./data/raw-data.csv). The purpose 
of using a fake dataset was to have a small reproducible example.


---

### Project Folder Structure

This project contains four folders, one README, and one file entitled `main.py`. 
In this structure we have a `data` folder and an `output` folder to physically separate 
the inputs and outputs:  

1.  [`data`](./data): Folder for raw, unprocessed data
2.  [`output`](./output): Folder for cleaned data, plots, etc.

There are two other folders in the structure:

3. [`lib`](./lib): Folder for Python scripts that hold global settings and functions
4. [`great_expectations`](./great_expectations): Folder of configurations and artifacts for pipeline tests
  
You should also notice at the top-level of the project folder there are the two files: 

5. [`main.py`](main.py): A single Python file that runs the main analysis for the project 
6. [`README.md`](README.md): A file that explains what this project is about

With this folder configuration we have a single Python file ([`main.py`](main.py)) that runs 
our entire analysis, but interacts with the other folders to read and write artifacts 
of the analysis. 

---

### Pipeline

In scikit-learn there is functionality where you can take multiple "transformers" 
and chain them together to preprocess data and model it. The ([`main.py`](main.py)) 
file is where these transformers preprocess the raw data located in 
[`data/raw-data.csv`](./data/raw-data.csv). However, we introduce the **great_expectations** (`ge`)  
library in three key areas to validate assumptions about data in our pipeline: 

1. Use `ge` to check the raw data
2. Use `ge` to check the data after preprocessing, which is right before modeling
3. Use `ge` to check the difference between predicted and actuals in a holdout dataset

It is pretty obvious that **great_expectations** could be used to validate the input, raw data. 
Checking preprocessed data is also helpful. This ensures that all of your transformers 
behaved as you would expect in case they encoded data incorrectly or changed in another 
environment if you pickle them after fitting them to data, etc. Even another analyst 
could tweak a transformer parameter in `main.py` which is running the analysis and 
the pipeline tests would catch the change in parameters of the transformers. This is 
extremely helpful in ensuring the data you are modeling is what you expect. In the third 
area, we check the model errors on a holdout set. This is also very helpful in 
ensuring that there are no extremely large errors caused by outliers or shift away 
from a defined distribution, which is normally assumed to be mean-zero with constant 
variance.

---

### Creating Expectations

In this example repo we started setting up **great_expectations** by running the 
command from the terminal: 

```
great_expectations init
```

When following the prompts we declined to initialize a datasource. Instead we 
created the datasources with the script [``](). 




---

[Top](#great-expectations-pipeline-tests-for-scikit-learn)