#!/usr/bin/env python3
import os
from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as lambda_,
    aws_apigatewayv2_alpha as apigw_,
    aws_apigatewayv2_integrations_alpha as _integrations,
    CfnOutput
)
from constructs import Construct

class ApigwSampleStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        __dirname = os.path.dirname(__file__)
        tableName = "lambda-apigateway"

        # Create the Lambda function to receive the request
        # The source code is in './src' directory
        lambda_fn = lambda_.Function(
            self, "MyFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_asset(os.path.join(__dirname, "src")),
            environment={
                "TABLENAME": tableName
            }
        )
        # Create the HTTP API with CORS
        http_api = apigw_.HttpApi(
            self, "MyHttpApi",
            cors_preflight=apigw_.CorsPreflightOptions(
                allow_methods=[apigw_.CorsHttpMethod.GET],
                allow_origins=["*"],
                max_age=Duration.days(10),
            )
        )

        # Add a route to GET /
        http_api.add_routes(
            path="/",
            methods=[apigw_.HttpMethod.GET],
            integration=_integrations.HttpLambdaIntegration("LambdaProxyIntegration", handler=lambda_fn),
        )

        # Outputs
        CfnOutput(self, "API Endpoint", description="API Endpoint", value=http_api.api_endpoint)
