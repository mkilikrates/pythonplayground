import os
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    CfnOutput
)
from constructs import Construct

class FunctionSampleStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        __function_name = 'Myfunction'

        # Create the Lambda function to receive the request
        # The source code is in './src' directory
        lambda_fn = lambda_.Function(
            self, "Myfunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            function_name = __function_name,
            code=lambda_.Code.from_asset(f"functions/{__function_name}/src"),
        )
        # Outputs
        CfnOutput(self, "FunctionARN", description="Function ARN", value=lambda_fn.function_arn)

