import json

from datetime import datetime,date
import datetime as dt
import boto3
from botocore.exceptions import ClientError

# iam_username: emailId
mail_IDs = {
            "user1": "user1@gmail.com", 
            "user12": "user12@gmail.com",
            "user123": "user123@gmail.com"
           }
mail_IDs_avail = list(mail_IDs.keys())
SENDER_EMAIL_ID = "sender@gmail.com"

client = boto3.client('iam')
s3 = boto3.resource('s3')
s3_client=boto3.client('s3')
bucket_name='brendon1' # give your s3 bucket name here
bucket = s3.Bucket(bucket_name)

def lambda_handler(event, context):
    # TODO implement
    main()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    
def main():
    res_users = client.list_users()
    # print(res_users)
    for user in res_users['Users']:
        user_name = user['UserName']
        if user_name not in mail_IDs_avail:
            continue
        iam_username = user_name
        try:
            # getting the no.days the key is getting used
            li_access_keys = client.list_access_keys(UserName= user_name)
            li_access_keys=li_access_keys['AccessKeyMetadata']
            print(len(li_access_keys))
            if(len(li_access_keys)>1):
                delete_unused_access_key(user_name)
                delete_access_key(user_name)
            li_access_keys = client.list_access_keys(UserName= user_name)
            li_access_keys=li_access_keys['AccessKeyMetadata']
            print(len(li_access_keys))
            # no.of days calculator
            temp_date = li_access_keys[0]['CreateDate'].strftime("%Y %m %d")
            access_key_created_date = datetime.strptime(temp_date, '%Y %m %d')
            current_date = datetime.now()
            access_key_no_of_days_used = (current_date-access_key_created_date).days
        
        except:
            print('User doesnt have any keys or user doesnt exist')
            continue

        # logic for 85th day
        if (int(access_key_no_of_days_used)>=85 and int(access_key_no_of_days_used)<90):
            try:
                # user who is accessing the key regularly
                access_key = li_access_keys[0]['AccessKeyId']
                print(access_key_no_of_days_used)
                resp_new_key_date_last_used = client.get_access_key_last_used(AccessKeyId=access_key)
                access_new_key_date_last_used = (resp_new_key_date_last_used['AccessKeyLastUsed']['LastUsedDate']).strftime("%Y %m %d")
                remaining_days=90-int(access_key_no_of_days_used)
                msg='You will get a New AWS access key and your present AWS Access key will be deactivated in next '+str(remaining_days)+' days.'
                mail(user_name, mail_IDs[iam_username] , msg)
            except:
                # user who doesnt access the key regularly
                print('In except')
                msg='You have not used your key for past 85 days.'
                mail(user_name, mail_IDs[iam_username] , msg)
                continue
        
        # logic for 90th day
        elif(int(access_key_no_of_days_used)>=90 and int(access_key_no_of_days_used)<95):
            try:
                # user who is accessing the key regularly
                access_key = li_access_keys[0]['AccessKeyId']
                resp_new_key_date_last_used = client.get_access_key_last_used(AccessKeyId=access_key)
                access_new_key_date_last_used = (resp_new_key_date_last_used['AccessKeyLastUsed']['LastUsedDate']).strftime("%Y %m %d")
                file_name = 'user_details.json' # json format - {'username' : 'no.of days the key is being active'}
                obj = list(bucket.objects.filter(Prefix=file_name))
                if len(obj) > 0:
                    # if the file already Exists
                    response=s3_client.get_object(Bucket=bucket_name, Key=file_name)
                    content=response['Body']
                    data = content.read().decode('utf-8')
                    data_json = json.loads(data)
                    if(user_name not in data_json.keys()):
                        # if user name already exists in the json file
                        x = access_key_no_of_days_used
                        data_json[user_name] = x
                        write_data = json.dumps(data_json)
                        s3.Bucket(bucket_name).put_object(Key=file_name, Body=write_data)
                        AccessKeyId, SecretAccessKey=create_access_key(user_name)
                        msg='Please start using your new Access Key.Your old access key will be deactived in next 5 days, Your new AccessKeyId is '+AccessKeyId+' and new SecretAccessKey is '+SecretAccessKey
                        mail(user_name, mail_IDs[iam_username] , msg)
                    else:
                    # if user name already doesn't exists in the json file
                        pass
                else:
                    # if the file doesn't Exists
                    x=access_key_no_of_days_used
                    data_json1 = {}
                    data_json1[user_name] = x
                    write_data = json.dumps(data_json1)
                    s3.Bucket(bucket_name).put_object(Key=file_name, Body=write_data)
                    AccessKeyId, SecretAccessKey=create_access_key(user_name)
                    msg='Please start using your new Access Key.Your old access key will be deactived in next 5 days, Your new AccessKeyId is '+AccessKeyId+' and new SecretAccessKey is '+SecretAccessKey
                    mail(user_name, mail_IDs[iam_username] , msg)
            except:
                # user who doesnt access the key regularly
                delete_unused_access_key(user_name)
                msg='Your old key has been deleted as it was not used for the past 90 days.'
                mail(user_name, mail_IDs[iam_username] , msg)
                continue
        
        # logic for 95th day
        elif(int(access_key_no_of_days_used)==95):
            try:
                # user who is accessing the key regularly
                file_name = 'user_details.json' # json format - {'username' : 'no.of days the key is being active'}
                obj = list(bucket.objects.filter(Prefix=file_name))
                if len(obj) > 0:
                    # if the file already Exists
                    response=s3_client.get_object(Bucket=bucket_name, Key=file_name)
                    content=response['Body']
                    data = content.read().decode('utf-8')
                    data_json = json.loads(data)
                    if(user_name in data_json.keys()):
                        # if user name already exists in the json file
                        del data_json[user_name]
                        write_data = json.dumps(data_json)
                        s3.Bucket(bucket_name).put_object(Key=file_name, Body=write_data)
                    else:
                        pass
                else:
                    pass
                access_key = li_access_keys[0]['AccessKeyId']
                resp_new_key_date_last_used = client.get_access_key_last_used(AccessKeyId=access_key)
                access_new_key_date_last_used = (resp_new_key_date_last_used['AccessKeyLastUsed']['LastUsedDate']).strftime("%Y %m %d")
                delete_access_key(user_name)
                msg='Please start using your New Access key.Your Old Key is deactivated'
                mail(user_name, mail_IDs[iam_username] , msg)
            except:
                # user who doesnt access the key regularly
                delete_unused_access_key(user_name)
                msg='Please contact your AWS Admin if you want a new Access key.'
                mail(user_name, mail_IDs[iam_username] , msg)
                continue
            
        # logic for users who is having key older than 95 days
        elif(int(access_key_no_of_days_used)>95):
            try:
                access_key = li_access_keys[0]['AccessKeyId']
                resp_new_key_date_last_used = client.get_access_key_last_used(AccessKeyId=access_key)
                access_new_key_date_last_used = (resp_new_key_date_last_used['AccessKeyLastUsed']['LastUsedDate']).strftime("%Y %m %d")
                file_name = 'access_key_details.json' # json format - {'username' : 'no.of days the key is being active'}
                obj = list(bucket.objects.filter(Prefix=file_name))
                if len(obj) > 0:
                    # if the file already Exists
                    response=s3_client.get_object(Bucket=bucket_name, Key=file_name)
                    content=response['Body']
                    data = content.read().decode('utf-8')
                    data_json = json.loads(data)
                    
                    if(user_name not in data_json.keys()):
                        # if user name already exists in the json file
                        x = access_key_no_of_days_used
                        data_json[user_name] = x
                        write_data = json.dumps(data_json)
                        s3.Bucket(bucket_name).put_object(Key=file_name, Body=write_data)
                        third_user(data_json[user_name],data_json,access_key_no_of_days_used,iam_username)
                    else:
                        # if user name already doesn't exists in the json file
                        third_user(data_json[user_name],data_json,access_key_no_of_days_used,iam_username)
                else:
                    # if the file doesn't Exists
                    x=access_key_no_of_days_used
                    data_json1 = {}
                    data_json1[user_name] = x
                    write_data = json.dumps(data_json1)
                    s3.Bucket(bucket_name).put_object(Key=file_name, Body=write_data)
                    third_user(data_json1[user_name],data_json1,access_key_no_of_days_used,iam_username)
            except:
                # user who doesnt access the key regularly
                delete_unused_access_key(user_name)
                msg='Please contact your AWS Admin if you want a new Access key.'
                mail(user_name, mail_IDs[iam_username] , msg)
                continue
                
        # logic to be implemented if the no.of days is less than 85.
        else:
            pass

def delete_unused_access_key(user_name):
    li_access_keys = client.list_access_keys(UserName= user_name)
	# getting access key for the list of user
    li_access_keys=li_access_keys['AccessKeyMetadata']
    for key in li_access_keys:
        try:
            access_key = key['AccessKeyId']
            resp_new_key_date_last_used = client.get_access_key_last_used(AccessKeyId=access_key)
            access_new_key_date_last_used = (resp_new_key_date_last_used['AccessKeyLastUsed']['LastUsedDate']).strftime("%Y %m %d")
            continue
        except:
            resp_key_delete = client.delete_access_key(UserName = user_name, AccessKeyId = key['AccessKeyId'])       		
    return True
	
def delete_access_key(user_name):
    # logic for deleting the old access key
	li_date = []
	li_access_keys = client.list_access_keys(UserName= user_name)
	# getting access key for the list of users
	li_access_keys=li_access_keys['AccessKeyMetadata']
	for i in range(len(li_access_keys)):
		date = li_access_keys[i]['CreateDate']
		li_date.append(date.strftime("%Y %m %d %H"))
	li_date.sort()
	latest_date = li_date[-1]
	for i in range(len(li_access_keys)):
		date = li_access_keys[i]['CreateDate']
		if date.strftime("%Y %m %d %H") != latest_date:
			resp_key_delete = client.delete_access_key(UserName = user_name, 
													   AccessKeyId = li_access_keys[i]['AccessKeyId'])
	return True
        
def create_access_key(user_name):
    # logic for creating a new access key
	li_access_keys = client.list_access_keys(UserName= user_name)
	li_access_keys=li_access_keys['AccessKeyMetadata']
	if len(li_access_keys)>1:
		delete_access_key(user_name)
	response = client.create_access_key(UserName = user_name)
	AccessKeyId = response['AccessKey']['AccessKeyId']
	SecretAccessKey = response['AccessKey']['SecretAccessKey']
	return AccessKeyId, SecretAccessKey

def mail(user_name, reciever, msg):
    # logic for sending mail
    SENDER = SENDER_EMAIL_ID
    RECIPIENT = reciever #"shubhshubh2480@gmail.com"
    SUBJECT = str(user_name)+" - Amazon Access Key Reminder"
    BODY_TEXT = msg
    CHARSET = "UTF-8"
    client_mail = boto3.client('ses')
    try:
        response = client_mail.send_email(
            Source=SENDER,
            Destination={
                'ToAddresses': [
                    RECIPIENT,
					SENDER
                ]
            },
            Message={
                'Subject': {
                    'Data': SUBJECT,
                    'Charset': CHARSET
                },
                'Body': {
                    'Text': {
                        'Data': BODY_TEXT,
                        'Charset': CHARSET
                    },
                    'Html': {
                        'Data': BODY_TEXT,
                        'Charset': CHARSET
                    }
                }
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])    
        pass
        
def third_user(x,data_json,access_key_no_of_days_used,iam_username):
    # logic for users who is having key older than 95 days
    if(access_key_no_of_days_used==x):
        msg='You will get a New AWS access key and your present AWS Access key will be deactivated in next 5 days.'
        mail(iam_username, mail_IDs[iam_username] , msg)
    elif(access_key_no_of_days_used==(x+5)):
        AccessKeyId, SecretAccessKey=create_access_key(iam_username)
        msg='Please start using your new Access Key.Your old access key will be deactived in next 5 days, Your new AccessKeyId is '+AccessKeyId+' and new SecretAccessKey is '+SecretAccessKey
        mail(iam_username, mail_IDs[iam_username] , msg)
    elif(access_key_no_of_days_used==(x+10)):
        delete_access_key(iam_username)
        del data_json[iam_username]
        write_data = json.dumps(data_json)
        s3.Bucket(bucket_name).put_object(Key=file_name, Body=write_data)
        msg='Please start using your New Access key.Your Old Key is deactivated'
        mail(iam_username, mail_IDs[iam_username] , msg)
    return True
