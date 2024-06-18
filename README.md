# AWS-File-Backup
 The Serverless File Backup project involves creating a system that automatically backs up files uploaded to an Amazon S3 bucket using AWS Lambda functions.


# U need to change bucket name to your bucket
 Instead of mainbucket1 use your bucket name
# Creating exe file

 Use command below \
 python -m PyInstaller -F -w AWSFileBackupOOP.py --additional-hooks-dir=.

 change datas in spec file to datas=[('app_config.ini', '.')],

 python -m PyInstaller AWSFileBackupOOP.spec

Before u use the command u need to add hook file hook-tkinterdnd2.py to your current folder.
