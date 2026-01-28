#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { SchedulerStack } from '../lib/scheduler-stack';

const app = new cdk.App();

// Get environment from context or default to 'dev'
const environment = app.node.tryGetContext('env') || 'dev';

new SchedulerStack(app, `GoldSportScheduler-${environment}`, {
  environment,
  env: {
    account: '299025166536',
    region: 'eu-central-1',
  },
  description: `GoldSport Scheduler infrastructure (${environment})`,
});
