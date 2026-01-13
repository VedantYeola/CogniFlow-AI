import json
import boto3
import os
import uuid
import logging

# 1. Setup Structured Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
textract = boto3.client('textract')
bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('USER_TABLE_NAME')
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    logger.info(f"Received S3 Event: {json.dumps(event)}")
    
    record = event['Records'][0]
    event_name = record['eventName']
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    if 'ObjectRemoved' in event_name:
        logger.info(f"Object removed, deleting record: {key}")
        table.delete_item(Key={'userId': key})
        return {'statusCode': 200}

    try:
        # 2. EXTRACTION STAGE
        logger.info(f"Starting Textract for: {key}")
        extraction = textract.analyze_expense(
            Document={'S3Object': {'Bucket': bucket, 'Name': key}}
        )
        
        extracted_text = ""
        amount = "0.00"
        
        for doc in extraction.get('ExpenseDocuments', []):
            for field in doc.get('SummaryFields', []):
                label = field.get('Type', {}).get('Text', 'Field')
                value = field.get('ValueDetection', {}).get('Text', '')
                extracted_text += f"{label}: {value}\n"
                if label == "TOTAL":
                    amount = value

        logger.info(f"Textract Results: {extracted_text}")

        # 3. AI AUDIT STAGE
        logger.info("Sending data to Bedrock (metallama3-8b-instruct-v1)")
        prompt = f"""Act as a corporate auditor. Analyze this receipt:
        {extracted_text}
        Rules: Meals over $50 are a violation. 
        Return ONLY valid JSON: {{"category": "string", "violation": boolean, "summary": "string"}}"""

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "temperature": 0
        }

        response = bedrock.invoke_model(
            modelId="meta.llama3-8b-instruct-v1:0",
            body=json.dumps(payload)
        )
        
        # Parse and Clean AI Response
        result = json.loads(response['body'].read())
        ai_text = result['content'][0]['text']
        logger.info(f"Raw AI Response: {ai_text}")

        # Sanitize JSON output
        start = ai_text.find("{")
        end = ai_text.rfind("}") + 1
        audit_data = json.loads(ai_text[start:end])

        # 4. FINAL SAVE
        logger.info(f"Saving audit result to DynamoDB for: {key}")
        table.put_item(
            Item={
                'userId': key,
                'auditId': str(uuid.uuid4()),
                'finalAmount': amount,
                'category': audit_data.get('category'),
                'violation': audit_data.get('violation'),
                'summary': audit_data.get('summary'),
                'status': 'PROCESSED',
                'timestamp': record['eventTime']
            }
        )
        logger.info("Successfully saved record.")
        return {'statusCode': 200}

    except Exception as e:
        logger.error(f"CRITICAL FAILURE for {key}: {str(e)}", exc_info=True)
        table.put_item(Item={'userId': key, 'status': 'FAILED', 'error': str(e)})
        return {'statusCode': 500}