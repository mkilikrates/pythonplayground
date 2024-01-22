#!/usr/bin/env python3
import os

import aws_cdk as cdk

from app.wordpress import WordpressStack

cdk_qualifier = os.getenv('CDK_QUALIFIER')
cdk_bucket_name = os.getenv('CDK_BUCKET')
synthesizer = cdk.DefaultStackSynthesizer(
    qualifier=cdk_qualifier,
    file_assets_bucket_name=cdk_bucket_name,
    bucket_prefix=f"{cdk_qualifier}/",
    image_assets_repository_name=cdk_bucket_name
)

app = cdk.App()
wordpress = WordpressStack(
    app,
    "Wordpress",
    synthesizer=synthesizer,
    env=cdk.Environment(
        account=os.getenv('AWS_ACCOUNT'), 
        region=os.getenv('AWS_REGION')
    ),
)

app.synth()
