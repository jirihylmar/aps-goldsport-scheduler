# Phase 5: CloudFront & Production

**Objective**: HTTPS delivery (required for display engine) and production readiness

**Repos involved**: orchestration (this repo - mono-repo)

---

## Tasks

### 5.1 Add CloudFront Distribution to CDK
**Size**: medium

Add CloudFront distribution for HTTPS access.

**CDK Code**:
```typescript
const distribution = new cloudfront.Distribution(this, 'Distribution', {
  defaultBehavior: {
    origin: new origins.S3Origin(websiteBucket),
    viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
    cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
  },
  additionalBehaviors: {
    '/data/*': {
      origin: new origins.S3Origin(websiteBucket),
      viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      cachePolicy: new cloudfront.CachePolicy(this, 'DataCachePolicy', {
        defaultTtl: Duration.seconds(60),
        maxTtl: Duration.seconds(120),
        minTtl: Duration.seconds(0),
      }),
    },
  },
  defaultRootObject: 'index.html',
});
```

**Verify**: `cdk synth` succeeds, CloudFront in template

---

### 5.2 Configure Cache Policies
**Size**: small

Set appropriate cache TTLs.

**Policy**:
- Static files (html, css, js): 1 hour
- Config files: 5 minutes
- Data (schedule.json): 60 seconds
- Assets: 1 day

**Verify**: Cache policies defined in CDK

---

### 5.3 Deploy CloudFront
**Size**: small

Deploy updated stack with CloudFront.

**Steps**:
1. Run `cdk deploy`
2. Note CloudFront distribution URL
3. Update CLAUDE.md with URL

**Verify**: CloudFront distribution active, HTTPS works

---

### 5.4 Test HTTPS Access
**Size**: small

Verify HTTPS access works correctly.

**Tests**:
1. Access via CloudFront HTTPS URL
2. Verify certificate is valid
3. Test all pages load
4. Test schedule.json accessible

**Verify**: All content accessible via HTTPS

---

### 5.5 Test with Display Engine
**Size**: medium

Test with actual Windows screensaver display engine.

**Steps**:
1. Configure screensaver with CloudFront HTTPS URL
2. Verify page loads in screensaver
3. Verify auto-refresh works
4. Test different languages

**Verify**: Display engine shows schedule correctly

---

### 5.6 Add CloudWatch Monitoring
**Size**: small

Set up basic monitoring and alerting.

**Metrics**:
- Lambda errors
- Lambda duration
- S3 request errors
- CloudFront error rate

**Alarms** (optional):
- Lambda error rate > 1%
- Lambda duration > 30s

**Verify**: CloudWatch dashboard shows metrics

---

### 5.7 Create Deployment Documentation
**Size**: small

Document deployment and operations.

**Content**:
- How to upload new TSV data
- How to update translations
- How to deploy code changes
- Troubleshooting guide

**Verify**: Documentation in docs/ folder

---

### 5.8 Production Deployment
**Size**: medium

Deploy to production environment.

**Steps**:
1. Create prod stack (or use stack parameter)
2. Deploy: `cdk deploy --context env=prod`
3. Verify all resources
4. Test end-to-end

**Verify**: Production environment fully functional

---

## Dependencies

```
5.1 ──▶ 5.2 ──▶ 5.3 ──▶ 5.4 ──▶ 5.5
                 │
                 └──▶ 5.6

5.7 (can run anytime)

5.5 ──▶ 5.8
```

---

## Phase Completion Criteria

- [ ] CloudFront deployed with HTTPS
- [ ] Cache policies configured correctly
- [ ] Display engine works with HTTPS URL
- [ ] Monitoring in place
- [ ] Documentation complete
- [ ] Production environment deployed
