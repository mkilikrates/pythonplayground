
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## Customizing Bootstrap

Following the [documentation](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html#bootstrapping-customizing)

Export template to make some changes

```bash
cdk bootstrap --show-template > cfn-templates/cfn-bootstrap.yaml
```

In this case my changes are:

- Disable versioning on S3 Bucket
- Enable Key rotation and Multi-Region on KMS
- Use same name from S3 Bucket to ECR Repository
- Use same KMS CMK for both S3 Bucket and ECR Repository
- KMS Policy to allow rds, secrets, logs and efs services due import via from_lookup not allow change resource policy

Export variables and execute bootstrap:

```bash
export AWS_ACCOUNT=<Account Number>
export AWS_REGION='us-east-1'
export BUCKET='<my bucket>'
export QUALIFIER='myprj'
export STACK_NAME='myprjcdkbootstrap'
export WORDPRESS_DB_USER='<myadminuser>'
export MY_IPv4="$(curl -4 ifconfig.co/)"
#export MY_IPv6="$(curl -6 ifconfig.co/)"
```

Deploy using Template

```bash
cdk bootstrap "aws://$AWS_ACCOUNT/$AWS_REGION" --template 'cfn-templates/cfn-bootstrap.yaml' --bootstrap-bucket-name "$CDK_BUCKET" --bootstrap-customer-key --qualifier "$CDK_QUALIFIER" --termination-protection --toolkit-stack-name "$CDK_STACK_NAME" --version-reporting false --public-access-block-configuration
```

#https://github.com/dhenne/aws-cdk-fargate-aurora-wordpress-example/blob/main/cdk_stacks/application.py
#https://www.codecentric.de/wissens-hub/blog/fargate-with-efs-and-aurora-serverless-using-aws-cdk
#https://github.com/amitrahav/wordpress-AWSecs-fargate--template/blob/master/nginx.Dockerfile
#https://aws.amazon.com/pt/blogs/startups/how-to-accelerate-your-wordpress-site-with-amazon-cloudfront/
#https://wp2static.com/
#https://github.com/aws/aws-cdk/issues/8977
#https://repost.aws/knowledge-center/fargate-unable-to-mount-efs
#https://github.com/MikletNg/aws-serverless-wordpress/tree/master
#https://medium.com/@mhkafadar/a-practical-aws-cdk-walkthrough-deploying-multiple-websites-to-s3-and-cloudfront-7caaabc9c327
#https://dev.to/aws-builders/best-practices-for-running-wordpress-on-aws-using-cdk-aj9
https://www.hostinger.com/tutorials/how-to-migrate-wordpress

Enjoy!
