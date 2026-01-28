import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import { Construct } from 'constructs';

export interface SchedulerStackProps extends cdk.StackProps {
  environment: string; // 'dev' or 'prod'
}

export class SchedulerStack extends cdk.Stack {
  // Expose resources for cross-references
  public readonly inputBucket: s3.Bucket;
  public readonly websiteBucket: s3.Bucket;
  public readonly dataTable: dynamodb.Table;
  public readonly processorLambda: lambda.Function;
  public readonly fetcherLambda: lambda.Function;
  public readonly distribution: cloudfront.Distribution;

  constructor(scope: Construct, id: string, props: SchedulerStackProps) {
    super(scope, id, props);

    const env = props.environment;

    // Task 1.2 - S3 input bucket (receives data uploads and fetched files)
    this.inputBucket = new s3.Bucket(this, 'InputBucket', {
      bucketName: `goldsport-scheduler-input-${env}`,
      versioned: false,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    });

    // Task 1.3 - S3 website bucket (static site + config + data)
    this.websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
      bucketName: `goldsport-scheduler-web-${env}`,
      websiteIndexDocument: 'index.html',
      publicReadAccess: false, // CloudFront will access it via OAI
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // Task 1.4 - DynamoDB table (processed schedules, state)
    this.dataTable = new dynamodb.Table(this, 'DataTable', {
      tableName: `goldsport-scheduler-data-${env}`,
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // Task 1.5 - Processor Lambda (processing pipeline, triggered by S3)
    this.processorLambda = new lambda.Function(this, 'ProcessorLambda', {
      functionName: `goldsport-scheduler-engine-${env}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.main',
      code: lambda.Code.fromAsset('../lambda/processor'),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        DATA_TABLE: this.dataTable.tableName,
        WEBSITE_BUCKET: this.websiteBucket.bucketName,
        INPUT_BUCKET: this.inputBucket.bucketName,
      },
    });

    // Grant Processor Lambda permissions
    this.inputBucket.grantRead(this.processorLambda);
    this.websiteBucket.grantReadWrite(this.processorLambda);
    this.dataTable.grantReadWriteData(this.processorLambda);

    // Task 1.5a - Fetcher Lambda (fetches data from external URLs)
    this.fetcherLambda = new lambda.Function(this, 'FetcherLambda', {
      functionName: `goldsport-scheduler-fetcher-${env}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.main',
      code: lambda.Code.fromAsset('../lambda/fetcher'),
      timeout: cdk.Duration.minutes(2),
      memorySize: 256,
      environment: {
        INPUT_BUCKET: this.inputBucket.bucketName,
        ORDERS_URL: 'http://kurzy.classicskischool.cz/export/export-tsv-2026.php?action=download',
      },
    });

    // Grant Fetcher Lambda permissions
    this.inputBucket.grantWrite(this.fetcherLambda);

    // Task 1.5b - EventBridge schedule rule (triggers Fetcher every 5 minutes)
    const fetchSchedule = new events.Rule(this, 'FetchSchedule', {
      ruleName: `goldsport-scheduler-fetch-schedule-${env}`,
      schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
      description: 'Triggers data fetcher Lambda every 5 minutes',
    });

    fetchSchedule.addTarget(new targets.LambdaFunction(this.fetcherLambda));

    // Task 1.6 - S3 trigger for Processor Lambda
    // Trigger on file uploads to orders/ and instructors/ prefixes
    this.inputBucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(this.processorLambda),
      { prefix: 'orders/' }
    );

    this.inputBucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(this.processorLambda),
      { prefix: 'instructors/' }
    );

    this.inputBucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(this.processorLambda),
      { prefix: 'schedule-overrides/' }
    );

    // Task 5.1 - CloudFront distribution for HTTPS access
    this.distribution = new cloudfront.Distribution(this, 'Distribution', {
      comment: `GoldSport Scheduler CDN (${env})`,
      defaultRootObject: 'index.html',
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(this.websiteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: new cloudfront.CachePolicy(this, 'DefaultCachePolicy', {
          cachePolicyName: `goldsport-scheduler-cache-${env}`,
          comment: 'Cache policy for static assets',
          defaultTtl: cdk.Duration.hours(1),
          maxTtl: cdk.Duration.days(1),
          minTtl: cdk.Duration.minutes(1),
          enableAcceptEncodingGzip: true,
          enableAcceptEncodingBrotli: true,
        }),
      },
      additionalBehaviors: {
        // Shorter cache for dynamic data
        'data/*': {
          origin: origins.S3BucketOrigin.withOriginAccessControl(this.websiteBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: new cloudfront.CachePolicy(this, 'DataCachePolicy', {
            cachePolicyName: `goldsport-scheduler-data-cache-${env}`,
            comment: 'Short cache for schedule data',
            defaultTtl: cdk.Duration.minutes(1),
            maxTtl: cdk.Duration.minutes(5),
            minTtl: cdk.Duration.seconds(30),
            enableAcceptEncodingGzip: true,
            enableAcceptEncodingBrotli: true,
          }),
        },
        // Config files cached longer but not too long
        'config/*': {
          origin: origins.S3BucketOrigin.withOriginAccessControl(this.websiteBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: new cloudfront.CachePolicy(this, 'ConfigCachePolicy', {
            cachePolicyName: `goldsport-scheduler-config-cache-${env}`,
            comment: 'Moderate cache for config files',
            defaultTtl: cdk.Duration.minutes(15),
            maxTtl: cdk.Duration.hours(1),
            minTtl: cdk.Duration.minutes(5),
            enableAcceptEncodingGzip: true,
            enableAcceptEncodingBrotli: true,
          }),
        },
      },
      errorResponses: [
        {
          httpStatus: 404,
          responsePagePath: '/index.html',
          responseHttpStatus: 200,
          ttl: cdk.Duration.minutes(1),
        },
        {
          httpStatus: 403,
          responsePagePath: '/index.html',
          responseHttpStatus: 200,
          ttl: cdk.Duration.minutes(1),
        },
      ],
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // US, Canada, Europe
    });

    // Outputs for reference
    new cdk.CfnOutput(this, 'InputBucketName', {
      value: this.inputBucket.bucketName,
      description: 'S3 bucket for input data (orders, instructors)',
    });

    new cdk.CfnOutput(this, 'WebsiteBucketName', {
      value: this.websiteBucket.bucketName,
      description: 'S3 bucket for website and generated schedule',
    });

    new cdk.CfnOutput(this, 'DataTableName', {
      value: this.dataTable.tableName,
      description: 'DynamoDB table for schedule state',
    });

    new cdk.CfnOutput(this, 'ProcessorLambdaName', {
      value: this.processorLambda.functionName,
      description: 'Processor Lambda function name',
    });

    new cdk.CfnOutput(this, 'FetcherLambdaName', {
      value: this.fetcherLambda.functionName,
      description: 'Fetcher Lambda function name',
    });

    new cdk.CfnOutput(this, 'DistributionId', {
      value: this.distribution.distributionId,
      description: 'CloudFront distribution ID',
    });

    new cdk.CfnOutput(this, 'DistributionUrl', {
      value: `https://${this.distribution.distributionDomainName}`,
      description: 'CloudFront distribution URL (HTTPS)',
    });
  }
}
