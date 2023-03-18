# Flask-Website

The service is available [here](https://kapalliprogram4.azurewebsites.net) until March 20th.

The following program processes the data from the following [URL](https://s3-us-west-2.amazonaws.com/css490/input.txt) and copies it into my own S3 bucket stored [here](https://akapaica.s3.us-west-2.amazonaws.com/input.txt) then parse and load into a DynamoDB table.

The user is prompted to enter their query information after loadind the data for the first and last name with the results will be outputted to a table below. If no entry is specified in the first and last name boxes and the query button is clicked, a warning will be sent that a first or last name needs to be specified. The user can also Clear Data which removes the file from the S3 storage and the table from DynamoDB.


To utilize this service, enter your aws keys at the following lines.
```
aws_access_key_id = ''
aws_secret_access_key = ''
```

  ## Video Walkthrough

Here's a walkthrough of implemented features:

<img src='https://github.com/amoghkapalli/Flask-Website/blob/main/Kapture%202023-03-10%20at%2021.51.00.gif' title='Video Walkthrough' width='' alt='Video Walkthrough' />
