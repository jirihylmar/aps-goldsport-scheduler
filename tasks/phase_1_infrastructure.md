# Phase 1: Infrastructure Foundation

**Objective**: Set up AWS resources and CDK project with modular architecture

**Repos involved**: orchestration (this repo - mono-repo)

---

## Tasks

### 1.1 Initialize CDK Project
**Size**: small

Create CDK TypeScript project in `infrastructure/` directory.

**Steps**:
1. Create `infrastructure/` directory
2. Run `cdk init app --language typescript`
3. Update `package.json` with project name
4. Verify with `npm run build`

**Verify**: `infrastructure/` exists, `npm run build` succeeds

---

### 1.2 Create S3 Input Bucket
**Size**: small

Add S3 bucket for input data (orders, instructors, etc.)

**CDK Code**:
```typescript
const inputBucket = new s3.Bucket(this, 'InputBucket', {
  bucketName: `goldsport-scheduler-input-${props.env}`,
  versioned: false,
  removalPolicy: RemovalPolicy.RETAIN,
});
```

**Verify**: `cdk synth` succeeds, bucket defined in template

---

### 1.3 Create S3 Website Bucket
**Size**: small

Add S3 bucket for static website hosting.

**CDK Code**:
```typescript
const websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
  bucketName: `goldsport-scheduler-web-${props.env}`,
  websiteIndexDocument: 'index.html',
  publicReadAccess: false, // CloudFront will access it
  removalPolicy: RemovalPolicy.RETAIN,
});
```

**Verify**: `cdk synth` succeeds, bucket defined with website config

---

### 1.4 Create DynamoDB Table
**Size**: small

Add DynamoDB table for schedule state storage.

**CDK Code**:
```typescript
const dataTable = new dynamodb.Table(this, 'DataTable', {
  tableName: `goldsport-scheduler-data-${props.env}`,
  partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
  billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
  removalPolicy: RemovalPolicy.RETAIN,
});
```

**Verify**: `cdk synth` succeeds, table defined in template

---

### 1.5 Create Lambda Function Skeleton
**Size**: medium

Create Lambda function with basic handler and IAM permissions.

**Steps**:
1. Create `lambda/processor/` directory
2. Create `handler.py` with basic structure
3. Create `requirements.txt`
4. Add Lambda to CDK stack with permissions

**CDK Code**:
```typescript
const processorLambda = new lambda.Function(this, 'ProcessorLambda', {
  functionName: `goldsport-scheduler-engine-${props.env}`,
  runtime: lambda.Runtime.PYTHON_3_11,
  handler: 'handler.main',
  code: lambda.Code.fromAsset('../lambda/processor'),
  timeout: Duration.minutes(5),
  memorySize: 512,
  environment: {
    DATA_TABLE: dataTable.tableName,
    WEBSITE_BUCKET: websiteBucket.bucketName,
  },
});

// Grant permissions
inputBucket.grantRead(processorLambda);
websiteBucket.grantReadWrite(processorLambda);
dataTable.grantReadWriteData(processorLambda);
```

**Verify**: `cdk synth` succeeds, Lambda and IAM role defined

---

### 1.6 Configure S3 Trigger
**Size**: small

Add S3 event notification to trigger Lambda on file upload.

**CDK Code**:
```typescript
inputBucket.addEventNotification(
  s3.EventType.OBJECT_CREATED,
  new s3n.LambdaDestination(processorLambda),
  { prefix: 'orders/' }
);

inputBucket.addEventNotification(
  s3.EventType.OBJECT_CREATED,
  new s3n.LambdaDestination(processorLambda),
  { prefix: 'instructors/' }
);
```

**Verify**: `cdk synth` succeeds, notification config in template

---

### 1.7 Deploy and Verify Infrastructure
**Size**: medium

Deploy stack to AWS and verify all resources created.

**Steps**:
1. Bootstrap CDK (if needed): `cdk bootstrap`
2. Deploy: `cdk deploy --require-approval never`
3. Verify resources via MCP tool

**Verify Commands**:
```bash
# Check S3 buckets exist
mcp__aws-vsb-299__call_aws aws s3 ls | grep goldsport-scheduler

# Check DynamoDB table
mcp__aws-vsb-299__call_aws aws dynamodb describe-table --table-name goldsport-scheduler-data-dev

# Check Lambda function
mcp__aws-vsb-299__call_aws aws lambda get-function --function-name goldsport-scheduler-engine-dev
```

**Verify**: All resources exist and are configured correctly

---

## Dependencies

```
1.1 ─┬─▶ 1.2 ─┬─▶ 1.5 ─▶ 1.6 ─▶ 1.7
     ├─▶ 1.3 ─┤
     └─▶ 1.4 ─┘
```

- 1.1 must complete before all others
- 1.2, 1.3, 1.4 can run in parallel after 1.1
- 1.5 needs buckets and table
- 1.6 needs Lambda
- 1.7 needs everything

---

## Phase Completion Criteria

- [ ] CDK project builds without errors
- [ ] All resources deployed to AWS
- [ ] Lambda has correct permissions
- [ ] S3 trigger configured for orders/ and instructors/
- [ ] Resources verified via MCP tools
