# CogniFlow-AI

**CogniFlow-AI** is a next-generation serverless identity and document management platform built on AWS. It seamlessly unifies secure social authentication (via Google & Cognito) with intelligent, AI-driven content auditing. 

By leveraging **AWS Bedrock** and **Textract**, CogniFlow-AI doesn't just store user uploads—it actively analyzes them for compliance and insights, providing a robust, scalable foundation for modern secure applications.

This project deploys a complete infrastructure using **AWS CDK (Python)**, integrating AWS Cognito with Google Federation, DynamoDB for user data, and S3 for user uploads.

## Project Architecture

The CDK stack creates the following resources:
1.  **Amazon Cognito User Pool**: Manages users and handles sign-up/sign-in.
    -   Configured with Google Identity Provider for social login.
    -   Email sign-in enabled.
2.  **Amazon DynamoDB Table**: Stores user profiles and metadata (`AppUserTable`).
3.  **AWS Lambda Functions**:
    -   `PostConfirmationHandler`: Triggered after sign-up to save user details to DynamoDB.
    -   `AiAuditorHandler`: Triggered by S3 uploads to audit content (using Textract/Bedrock).
4.  **Amazon S3 Bucket**: Secure storage for user uploads with strict CORS policies.
5.  **Amazon Cognito Identity Pool**: Vends temporary AWS credentials to authenticated users.

## Prerequisites

-   **Node.js** (for AWS CDK CLI)
-   **Python 3.9+**
-   **AWS CLI** configured (`aws configure`)
-   **Google Cloud Project** with OAuth credentials (Client ID and Secret)

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd aws-cognito-auth
    ```

2.  **Create and activate a virtual environment:**
    -   **Windows:**
        ```powershell
        python -m venv .venv
        .venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

**IMPORTANT:** This project uses sensitive credentials. **Do not** hardcode them in your files. Instead, use a `.env` file.

1.  Create a file named `.env` in the root directory.
2.  Add the following variables to `.env` (replace values with your own):

    ```ini
    # AWS Deployment Config
    CDK_DEFAULT_ACCOUNT=123456789012
    CDK_DEFAULT_REGION=us-east-1

    # Google OAuth Credentials
    # Obtain these from the Google Cloud Console (APIs & Services > Credentials)
    GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
    GOOGLE_CLIENT_SECRET=your-google-client-secret

    # Cognito Configuration
    # Must be unique across the AWS Region
    COGNITO_DOMAIN_PREFIX=your-unique-app-prefix
    ```

    *Note: The `.env` file is already added to `.gitignore` to prevent accidental commits.*

## Deployment

1.  **Synthesize the CloudFormation template:**
    ```bash
    cdk synth
    ```

2.  **Deploy the stack:**
    ```bash
    cdk deploy
    ```
    Confirm the deployment when prompted.

## Useful Commands

-   `cdk ls`          - List all stacks in the app
-   `cdk synth`       - Emits the synthesized CloudFormation template
-   `cdk deploy`      - Deploy this stack to your default AWS account/region
-   `cdk diff`        - Compare deployed stack with current state
-   `cdk docs`        - Open CDK documentation

## Security Note

-   Ensure your `GOOGLE_CLIENT_SECRET` and other keys are never pushed to public repositories.
-   This project uses `git-secrets` or manual checks (via `.gitignore`) to keep credentials safe.
