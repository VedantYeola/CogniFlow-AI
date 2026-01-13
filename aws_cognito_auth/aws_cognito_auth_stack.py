import os
from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    SecretValue,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_iam as iam,
    CfnOutput,
    aws_cognito_identitypool as identitypool,
    aws_s3_notifications as s3_notifications
)
from constructs import Construct
from aws_cdk.aws_cognito_identitypool import (
    IdentityPool, 
    UserPoolAuthenticationProvider,
    IdentityPoolAuthenticationProviders
)

class MyAuthAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. DynamoDB Table
        user_table = dynamodb.Table(
            self, "AppUserTable",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # 2. Lambda Trigger (Post Confirmation)
        post_confirmation_fn = _lambda.Function(
            self, "PostConfirmationHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="post_confirmation.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={"USER_TABLE_NAME": user_table.table_name}
        )
        user_table.grant_write_data(post_confirmation_fn)

        # 3. Cognito User Pool
        user_pool = cognito.UserPool(self, "MyUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(username=False, email=True),
            lambda_triggers=cognito.UserPoolTriggers(post_confirmation=post_confirmation_fn)
        )

        # 4. Google Identity Provider
        google_provider = cognito.UserPoolIdentityProviderGoogle(
            self, "GoogleProvider",
            user_pool=user_pool,
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret_value=SecretValue.unsafe_plain_text(os.getenv("GOOGLE_CLIENT_SECRET")),
            attribute_mapping=cognito.AttributeMapping(
                email=cognito.ProviderAttribute.GOOGLE_EMAIL,
                fullname=cognito.ProviderAttribute.GOOGLE_NAME
            ),
            scopes=["profile", "email", "openid"]
        )

        # 5. User Pool Client
        user_pool_client = user_pool.add_client("WebAppClient",
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.GOOGLE,
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=["http://localhost:3000/"],
                logout_urls=["http://localhost:3000/"]    
            )
        )
        user_pool_client.node.add_dependency(google_provider)

        # 6. Cognito Identity Pool
        identity_pool = IdentityPool(self, "AppIdentityPool", 
            identity_pool_name="AuthAppIdentityPool",
            allow_unauthenticated_identities=False,
            authentication_providers=IdentityPoolAuthenticationProviders(
                user_pools=[UserPoolAuthenticationProvider(user_pool=user_pool, user_pool_client=user_pool_client)]
            )
        )

            # 7. Storage (S3 with Enhanced 2026 CORS)
        upload_bucket = s3.Bucket(self, "UserUploadBucket",
            cors=[s3.CorsRule(
                allowed_methods=[
                    s3.HttpMethods.GET, 
                    s3.HttpMethods.POST, 
                    s3.HttpMethods.PUT, 
                    s3.HttpMethods.DELETE,
                    s3.HttpMethods.HEAD
                ],
                allowed_origins=["http://localhost:3000"],
                # Amplify v6 sends custom headers that must be allowed
                allowed_headers=[
                    "*", 
                    "Authorization", 
                    "Content-Type", 
                    "x-amz-date", 
                    "x-amz-user-agent", 
                    "x-amz-content-sha256"
                ],
                # Exposed headers allow the browser to read metadata like ETags
                exposed_headers=[
                    "ETag", 
                    "x-amz-request-id", 
                    "x-amz-id-2", 
                    "Access-Control-Allow-Origin"
                ],
                max_age=3000
            )],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # 8. AI Auditor Lambda (DEFINED ONLY ONCE)
        ai_auditor_fn = _lambda.Function(self, "AiAuditorHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="ai_auditor.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(45),
            environment={"USER_TABLE_NAME": user_table.table_name}
        )

        # 9. Permissions & Triggers
        upload_bucket.grant_read(ai_auditor_fn)
        user_table.grant_write_data(ai_auditor_fn)
        user_table.grant_read_data(identity_pool.authenticated_role)
        upload_bucket.grant_read_write(identity_pool.authenticated_role)

        # AI Service Permissions
        ai_auditor_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["textract:AnalyzeExpense", "bedrock:InvokeModel"],
            resources=["*"]
        ))

        # S3 Notification to Trigger Lambda
        upload_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(ai_auditor_fn)
        )

        # 10. Outputs
        user_pool.add_domain("CognitoDomain", 
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=os.getenv("COGNITO_DOMAIN_PREFIX"))
        )
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
        CfnOutput(self, "IdentityPoolId", value=identity_pool.identity_pool_id)
        CfnOutput(self, "BucketName", value=upload_bucket.bucket_name)