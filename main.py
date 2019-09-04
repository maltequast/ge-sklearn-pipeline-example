#!/usr/bin/env python

import pandas as pd
import numpy as np

from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, KBinsDiscretizer, FunctionTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline, make_pipeline, FeatureUnion
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV

import great_expectations as ge
from datetime import datetime

from lib.constants import *
from lib.transformers import ftransformer_cut, ColumnSelector

if __name__ == "__main__":

    # Create our great_expectations context
    context = ge.data_context.DataContext()

    # Validate raw data -------------------------------------------------------------------
    # Check that the data inputs are what we expect before preprocessing and modeling
    # NOTE: The expectations for this data asset were defined in the
    # file entitled ''. That file must be run to create and save the expectation
    # suite that is being used here to validate the new batches.
    df_raw = pd.read_csv('data/raw-data.csv')
    data_asset_name = "raw-data"
    expectation_suite_name = "default"
    batch = context.get_batch(data_asset_name, expectation_suite_name, df_raw)
    run_id = datetime.utcnow().isoformat().replace(":", "") + "Z"
    validation_result_df_raw = batch.validate(run_id=run_id)
    assert validation_result_df_raw["success"]

    # Transform data ----------------------------------------------------------------------
    # Now proceed to transform the data before modeling it using the concept of
    # a scikit-learn pipeline which chains together "transformers"

    # Create dummy variables transformer across species and color
    ohe = OneHotEncoder(categories=[SPECIES, COLOR], drop='first', sparse=False)
    ohe_cols = df_raw.loc[:, ['species', 'color']]
    ohe.fit(ohe_cols)

    # Create ordinal variable transformer for beak_ratio
    oe = OrdinalEncoder(categories=[BEAK_RATIO])
    oe_cols = df_raw.loc[:, ['beak_ratio']]
    oe.fit(oe_cols)

    # Create a transformer to bin claw_length across [0, 0.2, 0.4, 0.6, 0.8, 1]
    ft = FunctionTransformer(ftransformer_cut,
                             kw_args={'bins': np.linspace(0, 1, 5)})

    # Create a transformer to bin wing_density into 2 quantiles
    kbd = KBinsDiscretizer(n_bins=2, encode='ordinal', strategy='quantile')
    kbd_cols = df_raw.loc[:, ['wing_density']]
    kbd.fit(kbd_cols)

    # String together the created transformers into a sklearn "pipeline"
    preprocess_pipeline = make_pipeline(
        FeatureUnion(transformer_list=[
            ("ohe", make_pipeline(
                ColumnSelector(columns=['species', 'color']),
                ohe
            )),
            ("oe", make_pipeline(
                ColumnSelector(columns=['beak_ratio']),
                oe
            )),
            ("ft", make_pipeline(
                ColumnSelector(columns=['claw_length']),
                ft
            )),
            ("kbd", make_pipeline(
                ColumnSelector(columns=['wing_density']),
                kbd
            )),
            ("label", make_pipeline(
                ColumnSelector(columns=['weight'])
            ))
        ])
    )

    # Apply the pipeline to the raw data
    # NOTE: The transformers are fitted based on the data loaded here when
    # main.py is run, but could be pickled and loaded so that they are
    # consistent across runs and batches.
    df_modeling = preprocess_pipeline.transform(df_raw)
    modeling_cols = ['V' + str(x) for x in range(df_modeling.shape[1])]
    df_modeling.to_csv('./output/modeling-data.csv', index=False, columns=modeling_cols)

    # Validate modeling data ---------------------------------------------------------------
    # Check that the transformed data are what we expect before modeling
    # NOTE: The expectations for this data asset were defined in the
    # file entitled ''. That file must be run to create and save the expectation
    # suite that is being used here to validate the new batches.
    data_asset_name = "modeling-data"
    expectation_suite_name = "default"
    batch = context.get_batch(data_asset_name, expectation_suite_name,
                              pd.DataFrame(df_modeling, columns=modeling_cols))
    validation_result_df_modeling = batch.validate(run_id=run_id)
    assert validation_result_df_modeling["success"]

    # Model the data -----------------------------------------------------------------------
    # Split up the data into train and test, assuming last column is target
    X = df_modeling[:, :-1]
    y = df_modeling[:, -1]
    X_train, X_test, \
        y_train, y_test = train_test_split(X, y,
                                           train_size=0.75,
                                           test_size=0.25,
                                           random_state=21)

    # Build the final estimator step of our pipeline
    # NOTE: This estimator does not need to be its own pipeline but for consistency
    # against the preprocessing pipeline
    rf = RandomForestRegressor(n_estimators=100, random_state=22)
    modeling_pipeline = Pipeline([('rf', rf)])

    # Tune the RandomForest parameters and make some predictions on the holdout test dataset
    # NOTE: The choice of parameters and two fold cross validation are purely for
    # demonstration to work with this small training dataset
    param_grid = {'rf__n_estimators': [50, 100, 150], 'rf__max_depth': [10, 20, 30]}
    rf_cv = GridSearchCV(modeling_pipeline, param_grid, iid=False, cv=2)
    rf_cv.fit(X_train, y_train)
    print(f"Tuned Hyperparameters: {rf_cv.best_params_}")

    # Save off the holdout predictions and errors
    y_pred_tuned_forest = rf_cv.predict(X_test)
    df_holdout_error = pd.DataFrame({'actual': y_test, 'pred': y_pred_tuned_forest})
    df_holdout_error['error'] = df_holdout_error['actual'] - df_holdout_error['pred']
    df_holdout_error.to_csv('./output/holdout-error-data.csv', index=False)

    # Validate holdout errors ---------------------------------------------------------------
    # Check that the holdout errors are what we would typically see for this model
    # NOTE: The expectations for this data asset were defined in the
    # file entitled ''. That file must be run to create and save the expectation
    # suite that is being used here to validate the new batches.
    data_asset_name = "holdout-error-data"
    expectation_suite_name = "default"
    batch = context.get_batch(data_asset_name, expectation_suite_name, df_holdout_error)
    validation_result_df_holdout_error = batch.validate(run_id=run_id)
    assert validation_result_df_holdout_error["success"]
