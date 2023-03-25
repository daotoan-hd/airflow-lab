# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

import datetime
import os

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python_operator import PythonOperator

# [START postgres_operator_howto_guide]


# create_pet_table, populate_pet_table, get_all_pets, and get_birth_date are examples of tasks created by
# instantiating the Postgres Operator

ENV_ID = os.environ.get("SYSTEM_TESTS_ENV_ID")
DAG_ID = "postgres_operator_dag"
CONNECTION_ID = "postgres"


path = '/opt/airflow/dags/output'

if os.path.isdir(path):
    os.chdir(path)
else:
    os.mkdir(path)
    os.chdir(path)

# @task(task_id="write_file_task")
def write_some_file(filename="output.txt", file_content="content"):
    try:
        with open("{}/{}".format(path,filename), "wt") as fout:
            fout.write(file_content)
    except Exception as e:
        log.error(e)
        raise AirflowException(e)

def my_task():
    hook = PostgresHook(postgres_conn_id=CONNECTION_ID)
    df = hook.get_pandas_df(sql="SELECT * FROM pet;")
    print(df)
    print("THIS IS DEBUG")
    write_some_file("query_result", df.to_string())

with DAG(
    dag_id=DAG_ID,
    start_date=datetime.datetime(2020, 2, 2),
    schedule="@once",
    catchup=False,
) as dag:
    # [START postgres_operator_howto_guide_create_pet_table]
    create_pet_table = PostgresOperator(
        postgres_conn_id=CONNECTION_ID,
        task_id="create_pet_table",
        sql="""
            CREATE TABLE IF NOT EXISTS pet (
            pet_id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            pet_type VARCHAR NOT NULL,
            birth_date DATE NOT NULL,
            OWNER VARCHAR NOT NULL);
          """,
    )
    # [END postgres_operator_howto_guide_create_pet_table]
    # [START postgres_operator_howto_guide_populate_pet_table]
    populate_pet_table = PostgresOperator(
        postgres_conn_id=CONNECTION_ID,
        task_id="populate_pet_table",
        sql="""
            INSERT INTO pet (name, pet_type, birth_date, OWNER)
            VALUES ( 'Max', 'Dog', '2018-07-05', 'Jane');
            INSERT INTO pet (name, pet_type, birth_date, OWNER)
            VALUES ( 'Susie', 'Cat', '2019-05-01', 'Phil');
            INSERT INTO pet (name, pet_type, birth_date, OWNER)
            VALUES ( 'Lester', 'Hamster', '2020-06-23', 'Lily');
            INSERT INTO pet (name, pet_type, birth_date, OWNER)
            VALUES ( 'Quincy', 'Parrot', '2013-08-11', 'Anne');
        """,
    )

    write_file_task = PythonOperator(
        task_id='write_file_task',
        python_callable=my_task,
    ) 

    # create_pet_table >> populate_pet_table >> get_all_pets >> get_birth_date
    create_pet_table >> populate_pet_table >> write_file_task
    # [END postgres_operator_howto_guide]

    # from tests.system.utils.watcher import watcher

    # This test needs watcher in order to properly mark success/failure
    # when "tearDown" task with trigger rule is part of the DAG
    # list(dag.tasks) >> watcher()

# from tests.system.utils import get_test_run  # noqa: E402

# Needed to run the example DAG with pytest (see: tests/system/README.md#run_via_pytest)
# test_run = get_test_run(dag)