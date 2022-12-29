import datetime
import psycopg2
import json
import hashlib
import localstack_client.session as boto3

QUEUE_NAME = "login-queue"

# Insert record 'message' to user_logins database.
def insert_record(message: dict):
    sql = """INSERT INTO user_logins(user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date) VALUES (%s, %s, %s, %s, %s, %s, %s);"""

    with psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='postgres', port=5432) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (message['user_id'], message['device_type'], message['ip'], message['device_id'], message['locale'], int(message['app_version'].split('.')[0]), datetime.date.today()))

        cursor.close()

# Read all records from user_logins database.
def read_records():
    sql = """SELECT * FROM user_logins;"""

    with psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='postgres', port=5432) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        records = cursor.fetchall()
        for row in records:
            print(row)

        cursor.close()

# Delete all records from user_logins database.
def delete_records():
    sql = """DELETE FROM user_logins;"""

    with psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='postgres', port=5432) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        cursor.close()

# Insert all messages in the SQS queue to the user_logins Postgres database.
def save_sqs_message_to_db():
    sqs = boto3.client("sqs")
    queueUrl = sqs.create_queue(QueueName=QUEUE_NAME)["QueueUrl"]
    response = sqs.receive_message(QueueUrl=queueUrl, MaxNumberOfMessages=10, WaitTimeSeconds=5)

    for message in response.get("Messages", []):
        messageBody = json.loads(message['Body'])

        if 'device_id' in messageBody and 'ip' in messageBody:
            deviceId = messageBody.get('device_id')
            ip = messageBody.get('ip')

            # Save the sha512 hash of device_id and ip to hide PII data.
            messageBody['device_id'] = hashlib.sha512(deviceId.encode('utf-8')).hexdigest()
            messageBody['ip'] = hashlib.sha512(ip.encode('utf-8')).hexdigest()
            insert_record(messageBody)

    # read_records()


def main():
    save_sqs_message_to_db()

if __name__ == '__main__':
    main()
