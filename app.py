import os
import re
import uuid
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import json

app = Flask(__name__)

aws_access_key_id = ''
aws_secret_access_key = ''

@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/hello', methods=['POST'])
def hello():
    source_bucket_name = 'css490'
    source_file_key = 'input.txt'
    destination_bucket_name = 'akapaica'
    destination_file_key = 'input.txt'
    # s3 = boto3.resource('s3')
    s3 = boto3.resource('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name='us-west-2')

    # Check if the file exists in the destination bucket
    bucket = s3.Bucket(destination_bucket_name)
    file_exists = False
    for obj in bucket.objects.filter(Prefix=destination_file_key):
        if obj.key == destination_file_key:
            file_exists = True
            break

    # Get the contents of the file from the source bucket
    obj = s3.Object(source_bucket_name, source_file_key)
    file_contents = obj.get()['Body'].read().decode('utf-8')

    # Upload the contents to your own bucket
    if file_exists:
        s3.Object(destination_bucket_name, destination_file_key).put(Body=file_contents, ACL='public-read')
        print(f'File "{destination_file_key}" updated in bucket "{destination_bucket_name}".')
    else:
        s3.Object(destination_bucket_name, destination_file_key).put(Body=file_contents, ACL='public-read')
        print(f'New file "{destination_file_key}" created in bucket "{destination_bucket_name}".')

    table_name = 'testing'
    partition_key = 'LastName'
    sort_key = 'FirstName'

    #dynamodb = boto3.resource('dynamodb')
    dynamodb = boto3.resource('dynamodb',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name='us-west-2')
    table = dynamodb.Table(table_name)
    if not table.creation_date_time:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': partition_key,
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': sort_key,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': partition_key,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': sort_key,
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        print(f'Table created: {table.table_name}')
    else:
        print('Table: ' + table.table_name + ' already existed')

    obj = s3.Object(destination_bucket_name, destination_file_key)
    lines = obj.get()['Body'].read().decode('utf-8').splitlines()
    for line in lines:
        line = line.strip()
        parts = re.split(r'\s+', line)
        last_name = parts[0]
        first_name = parts[1]
        attributes = {}

        for attr in parts[2:]:
            key, value = attr.split('=')
            if '.' in key:
                subkeys = key.split('.')
                subdict = attributes
                for subkey in subkeys[:-1]:
                    if subkey not in subdict:
                        subdict[subkey] = {}
                    subdict = subdict[subkey]
                subdict[subkeys[-1]] = value
            else:
                attributes[key] = value

        item = {
            'LastName': last_name,
            'FirstName': first_name,
            'Attributes': attributes
        }
        table.put_item(Item=item)
        print(f'Item added: {item}')
    return render_template('hello.html')

    '''
        else:
        print('Request for hello page received with no name or blank name -- redirecting')
        return redirect(url_for('index'))
    '''



@app.route('/clear-data', methods=['POST', 'GET'])
def clear_data():
    s3 = boto3.resource('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name='us-west-2'
                        )
    #s3 = boto3.resource('s3')
    table_name = 'testing'
    table = boto3.resource('dynamodb',
                           aws_access_key_id=aws_access_key_id,
                           aws_secret_access_key=aws_secret_access_key,
                           region_name='us-west-2').Table(table_name)
    #table = boto3.resource('dynamodb').Table(table_name)

    # Delete all items from the DynamoDB table
    with table.batch_writer() as batch:
        items = table.scan()['Items']
        for item in items:
            batch.delete_item(Key={'LastName': item['LastName'], 'FirstName': item['FirstName']})
    print(f'{len(items)} items deleted from DynamoDB table: {table_name}')

    # Delete the file from the S3 bucket
    bucket_name = 'akapaica'
    file_key = 'input.txt'
    s3.Object(bucket_name, file_key).delete()
    print(f'File "{file_key}" deleted from S3 bucket: {bucket_name}')

    return redirect(url_for('index'))

@app.route('/query-data')
def query_data():
    first_name = request.args.get('first-name', '')
    last_name = request.args.get('last-name', '')
    table_name = 'testing'
    partition_key = 'LastName'
    sort_key = 'FirstName'
    #dynamodb = boto3.resource('dynamodb')
    dynamodb = boto3.resource('dynamodb',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name='us-west-2')
    table = dynamodb.Table(table_name)
    if not first_name:
        response = table.scan(FilterExpression=Key(partition_key).eq(last_name))
    elif not last_name:
        response = table.scan(FilterExpression=Key(sort_key).eq(first_name))
    else:
        response = table.query(
            KeyConditionExpression=Key(partition_key).eq(last_name) & Key(sort_key).eq(first_name)
        )
    items = response.get('Items', [])
    print(f'{len(items)} items retrieved from DynamoDB table: {table_name}')
    print(json.dumps({'items': items}))
    return json.dumps({'items': items})

@app.route('/get-data')
def get_data():
    results = query_data()
    # process and format the results as needed
    print("results: " + results)
    return jsonify(results)


if __name__ == '__main__':
    app.run()
