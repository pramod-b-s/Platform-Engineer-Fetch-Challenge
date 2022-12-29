# Fetch Rewards #
## Data Engineering Take Home: ETL off a SQS Qeueue ##

You may use any programming language to complete this exercise. We strongly encourage you to write a README to explain how to run your application and summarize your thought process.

## What do I need to do?
This challenge will focus on your ability to write a small application that can read from an AWS SQS Qeueue, transform that data, then write to a Postgres database. This project includes steps for using docker to run all the components locally, **you do not need an AWS account to do this take home.**

Your objective is to read JSON data containing user login behavior from an AWS SQS Queue that is made available via [localstack](https://github.com/localstack/localstack). Fetch wants to hide personal identifiable information (PII). The fields `device_id` and `ip` should be masked, but in a way where it is easy for data analysts to identify duplicate values in those fields.

Once you have flattened the JSON data object and masked those two fields, write each record to a Postgres database that is made available via [Postgres's docker image](https://hub.docker.com/_/postgres). Note the target table's DDL is:

```sql
-- Creation of user_logins table

CREATE TABLE IF NOT EXISTS user_logins(
    user_id             varchar(128),
    device_type         varchar(32),
    masked_ip           varchar(256),
    masked_device_id    varchar(256),
    locale              varchar(32),
    app_version         integer,
    create_date         date
);
```

You will have to make a number of decisions as you develop this solution:

*    How will you read messages from the queue?
*    What type of data structures should be used?
*    How will you mask the PII data so that duplicate values can be identified?
*    What will be your strategy for connecting and writing to Postgres?
*    Where and how will your application run?

**The recommended time to spend on this take home is 2-3 hours.** Make use of code stubs, doc strings, and a next steps section in your README to elaborate on ways that you would continue fleshing out this project if you had the time.

For this assignment an ounce of communication and organization is worth a pound of execution. The following questions are answered inline:

* How would you deploy this application in production?

The current script `write_to_db.py` can be run periodically if the throughput of incoming data is not large (a cron job can be used, for instance). The script can be placed in the docker container which can run on an EC2 instance on AWS, or it can be added to an EKS cluster node. We should also ensure that the database is initialized/configured properly with the right security to avoid data breach issues.

* What other components would you want to add to make this production ready?

Input validation needs to be added to filter out invalid messages. Automation testing needs to be added to ensure the application is robust enough and does not break down in production environment. A front-end dashboard/webpage should also be added to control the ETL processes easily and the frequently run ETL workflows can be automated. CI/CD should also be setup for the application to run at regular intervals and report any errors while integrating code changes without breaking down existing functionality.
The database connection is not always possible at the first attempt and a timeout with retries using an exponential backoff mechanism should be added for production. The credentials for connecting to the database also need to be hidden/read from securely.

* How can this application scale with a growing data set.

With a larger throughput of incoming data, more workers are needed and this can be achieved by adding more worker nodes (multi-processing) or using concurrency in the application (multi-threading). For multi-threading, the threading module can be used and for multi-processing, the job can be run in docker containers in a cluster managed by Kubernetes. With both multi-threading and multi-processing, the `visibility timeout` should be properly configured. This is the time period during which SQS prevents other processes from handling the message so duplicate rows are not created in the database by multiple threads/nodes handling the same message. Load balancers should also be used with multi-processing.

* How can PII be recovered later on?

Using a two-way hashing module will help and a secret key needs to be used for (en)decryption (libraries like `cryptography` can be used in Python). PII cannot be recovered with the current implementation as one-way hash is used.

## Project Setup
1. Fork this repository to a personal Github, GitLab, Bitbucket, etc... account. We will not accept PRs to this project.
2. You will need the following installed on your local machine
    * make
        * Ubuntu -- `apt-get -y install make`
        * Windows -- `choco install make`
        * Mac -- `brew install make`
    * python3 -- [python install guide](https://www.python.org/downloads/)
    * pip3 -- `python -m ensurepip --upgrade` or run `make pip-install` in the project root
    * awslocal -- `pip install awscli-local`  or run `make pip install` in the project root
    * docker -- [docker install guide](https://docs.docker.com/get-docker/)
    * docker-compose -- [docker-compose install guide]()
3. Run `make start` to execute the docker-compose file in the the project (see scripts/ and data/ directories to see what's going on, if you're curious)
    * An AWS SQS Queue is created
    * A script is run to write 100 JSON records to the queue
    * A Postgres database will be stood up
    * A user_logins table will be created in the public schema
4. Test local access
    * Read a message from the queue using awslocal, `awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/login-queue`
    * Connect to the Postgres database, verify the table is created
    * username = `postgres`
    * database = `postgres`
    * password = `postgres`

```bash
# password: postgres

psql -d postgres -U postgres  -p 5432 -h localhost -W
Password:

postgres=# select * from user_logins;
 user_id | device_type | hashed_ip | hashed_device_id | locale | app_version | create_date
---------+-------------+-----------+------------------+--------+-------------+-------------
(0 rows)
```
5. Run `make stop` to terminate the docker containers and optionally run `make clean` to clean up docker resources.

## Approach used

The function `save_sqs_message_to_db()` in script `write_to_db.py` processes the messages from the AWS SQS and saves them into the Postgres database. Multiple enhancements can be made for production. AWS SDK for Python is used for processing the data. Upon receiving the message, it is saved in json format and a dictionary is used to flatten and process the data.

Python's default hash library to mask device_id and ip, the personal identifiable information (PII). SHA-512 hash function is used as hash collisions are unlikely with a large number of messages and it is more secure since it encrypts the value in 512 bits. The hash value helps in duplicate detection for fields device_id and ip. Hash functions like MD5 are faster but not by a significant extent. SHA-512 is a one-way hash and it is not possible to recover the PII later. If the PII needs to be recoverable, we can consider using a two-way hash function for encryption and decryption, using libraries like `cryptography`.

`psycopg2` is used to connect to, insert to, and read from the Postgres database since it is easier to maintain. If the application needs to handle data at a larger scale, a flask app  would be a better choice since it is lightweight, fast, and scalable.


## Steps To Run
1. Run `make start` to initialize AWS SQS Queue and Postgres Database.
2. Run `python3 scripts/write_to_db.py` to run the script that reads messages from SQS queue, masks the PII, and writes the records to the Postgres database.

## All done, now what?
Upload your codebase to a public Git repo (GitHub, Bitbucket, etc.) and please submit your Link where it says to - under the exercise via Green House our ATS. Please double-check this is publicly accessible.

Please assume the evaluator does not have prior experience executing programs in your chosen language and needs documentation understand how to run your code
