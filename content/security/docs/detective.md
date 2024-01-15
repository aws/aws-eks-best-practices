# Auditing and logging
Collecting and analyzing \[audit\] logs is useful for a variety of different reasons.  Logs can help with root cause analysis and attribution, i.e. ascribing a change to a particular user. When enough logs have been collected, they can be used to detect anomalous behaviors too. On EKS, the audit logs are sent to Amazon Cloudwatch Logs. The audit policy for EKS is as follows: 

```yaml
apiVersion: audit.k8s.io/v1beta1
kind: Policy
rules:
  # Log aws-auth configmap changes
  - level: RequestResponse
    namespaces: ["kube-system"]
    verbs: ["update", "patch", "delete"]
    resources:
      - group: "" # core
        resources: ["configmaps"]
        resourceNames: ["aws-auth"]
    omitStages:
      - "RequestReceived"
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
      - group: "" # core
        resources: ["endpoints", "services", "services/status"]
  - level: None
    users: ["kubelet"] # legacy kubelet identity
    verbs: ["get"]
    resources:
      - group: "" # core
        resources: ["nodes", "nodes/status"]
  - level: None
    userGroups: ["system:nodes"]
    verbs: ["get"]
    resources:
      - group: "" # core
        resources: ["nodes", "nodes/status"]
  - level: None
    users:
      - system:kube-controller-manager
      - system:kube-scheduler
      - system:serviceaccount:kube-system:endpoint-controller
    verbs: ["get", "update"]
    namespaces: ["kube-system"]
    resources:
      - group: "" # core
        resources: ["endpoints"]
  - level: None
    users: ["system:apiserver"]
    verbs: ["get"]
    resources:
      - group: "" # core
        resources: ["namespaces", "namespaces/status", "namespaces/finalize"]
  - level: None
    users:
      - system:kube-controller-manager
    verbs: ["get", "list"]
    resources:
      - group: "metrics.k8s.io"
  - level: None
    nonResourceURLs:
      - /healthz*
      - /version
      - /swagger*
  - level: None
    resources:
      - group: "" # core
        resources: ["events"]
  - level: Request
    users: ["kubelet", "system:node-problem-detector", "system:serviceaccount:kube-system:node-problem-detector"]
    verbs: ["update","patch"]
    resources:
      - group: "" # core
        resources: ["nodes/status", "pods/status"]
    omitStages:
      - "RequestReceived"
  - level: Request
    userGroups: ["system:nodes"]
    verbs: ["update","patch"]
    resources:
      - group: "" # core
        resources: ["nodes/status", "pods/status"]
    omitStages:
      - "RequestReceived"
  - level: Request
    users: ["system:serviceaccount:kube-system:namespace-controller"]
    verbs: ["deletecollection"]
    omitStages:
      - "RequestReceived"
  # Secrets, ConfigMaps, and TokenReviews can contain sensitive & binary data,
  # so only log at the Metadata level.
  - level: Metadata
    resources:
      - group: "" # core
        resources: ["secrets", "configmaps"]
      - group: authentication.k8s.io
        resources: ["tokenreviews"]
    omitStages:
      - "RequestReceived"
  - level: Request
    resources:
      - group: ""
        resources: ["serviceaccounts/token"]
  - level: Request
    verbs: ["get", "list", "watch"]
    resources: 
      - group: "" # core
      - group: "admissionregistration.k8s.io"
      - group: "apiextensions.k8s.io"
      - group: "apiregistration.k8s.io"
      - group: "apps"
      - group: "authentication.k8s.io"
      - group: "authorization.k8s.io"
      - group: "autoscaling"
      - group: "batch"
      - group: "certificates.k8s.io"
      - group: "extensions"
      - group: "metrics.k8s.io"
      - group: "networking.k8s.io"
      - group: "policy"
      - group: "rbac.authorization.k8s.io"
      - group: "scheduling.k8s.io"
      - group: "settings.k8s.io"
      - group: "storage.k8s.io"
    omitStages:
      - "RequestReceived"
  # Default level for known APIs
  - level: RequestResponse
    resources: 
      - group: "" # core
      - group: "admissionregistration.k8s.io"
      - group: "apiextensions.k8s.io"
      - group: "apiregistration.k8s.io"
      - group: "apps"
      - group: "authentication.k8s.io"
      - group: "authorization.k8s.io"
      - group: "autoscaling"
      - group: "batch"
      - group: "certificates.k8s.io"
      - group: "extensions"
      - group: "metrics.k8s.io"
      - group: "networking.k8s.io"
      - group: "policy"
      - group: "rbac.authorization.k8s.io"
      - group: "scheduling.k8s.io"
      - group: "settings.k8s.io"
      - group: "storage.k8s.io"
    omitStages:
      - "RequestReceived"
  # Default level for all other requests.
  - level: Metadata
    omitStages:
      - "RequestReceived"
``` 

## Recommendations

### Enable audit logs
The audit logs are part of the EKS managed Kubernetes control plane logs that are managed by EKS.  Instructions for enabling/disabling the control plane logs, which includes the logs for the Kubernetes API server, the controller manager, and the scheduler, along with the audit log, can be found here, [https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html#enabling-control-plane-log-export](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html#enabling-control-plane-log-export). 

!!! info
    When you enable control plane logging, you will incur [costs](https://aws.amazon.com/cloudwatch/pricing/) for storing the logs in CloudWatch. This raises a broader issue about the ongoing cost of security. Ultimately you will have to weigh those costs against the cost of a security breach, e.g. financial loss, damage to your reputation, etc. You may find that you can adequately secure your environment by implementing only some of the recommendations in this guide. 

!!! warning
    The maximum size for a CloudWatch Logs entry is [256KB](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html) whereas the maximum Kubernetes API request size is 1.5MiB. Log entries greater than 256KB will either be truncated or only include the request metadata. 

### Utilize audit metadata
Kubernetes audit logs include two annotations that indicate whether or not a request was authorized `authorization.k8s.io/decision` and the reason for the decision `authorization.k8s.io/reason`.  Use these attributes to ascertain why a particular API call was allowed. 
   
### Create alarms for suspicious events
Create an alarm to automatically alert you where there is an increase in 403 Forbidden and 401 Unauthorized responses, and then use attributes like `host`, `sourceIPs`, and `k8s_user.username` to find out where those requests are coming from.
  
### Analyze logs with Log Insights
Use CloudWatch Log Insights to monitor changes to RBAC objects, e.g. Roles, RoleBindings, ClusterRoles, and ClusterRoleBindings.  A few sample queries appear below: 

Lists updates to the `aws-auth` ConfigMap:
```
fields @timestamp, @message
| filter @logStream like "kube-apiserver-audit"
| filter verb in ["update", "patch"]
| filter objectRef.resource = "configmaps" and objectRef.name = "aws-auth" and objectRef.namespace = "kube-system"
| sort @timestamp desc
```
Lists creation of new or changes to validation webhooks:
```
fields @timestamp, @message
| filter @logStream like "kube-apiserver-audit"
| filter verb in ["create", "update", "patch"] and responseStatus.code = 201
| filter objectRef.resource = "validatingwebhookconfigurations"
| sort @timestamp desc
```
Lists create, update, delete operations to Roles:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="roles" and verb in ["create", "update", "patch", "delete"]
```
Lists create, update, delete operations to RoleBindings:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="rolebindings" and verb in ["create", "update", "patch", "delete"]
```
Lists create, update, delete operations to ClusterRoles:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="clusterroles" and verb in ["create", "update", "patch", "delete"]
```
Lists create, update, delete operations to ClusterRoleBindings:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="clusterrolebindings" and verb in ["create", "update", "patch", "delete"]
```
Plots unauthorized read operations against Secrets:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="secrets" and verb in ["get", "watch", "list"] and responseStatus.code="401"
| stats count() by bin(1m)
```
List of failed anonymous requests:
```
fields @timestamp, @message, sourceIPs.0
| sort @timestamp desc
| limit 100
| filter user.username="system:anonymous" and responseStatus.code in ["401", "403"]
```

### Audit your CloudTrail logs
AWS APIs called by pods that are utilizing IAM Roles for Service Accounts (IRSA) are automatically logged to CloudTrail along with the name of the service account. If the name of a service account that wasn't explicitly authorized to call an API appears in the log, it may be an indication that the IAM role's trust policy was misconfigured. Generally speaking, Cloudtrail is a great way to ascribe AWS API calls to specific IAM principals. 

### Use CloudTrail Insights to unearth suspicious activity
CloudTrail insights automatically analyzes write management events from CloudTrail trails and alerts you of unusual activity. This can help you identify when there's an increase in call volume on write APIs in your AWS account, including from pods that use IRSA to assume an IAM role. See [Announcing CloudTrail Insights: Identify and Response to Unusual API Activity](https://aws.amazon.com/blogs/aws/announcing-cloudtrail-insights-identify-and-respond-to-unusual-api-activity/) for further information.

### Use Amazon Detective to visualize your security investigations
If you do not currently have a solution for visualizing your security investigations across environments, consider using [Amazon Detective](https://aws.amazon.com/detective/). Detective helps you analyze, investigate, and quickly identify the root cause of security findings or suspicious activities. Detective automatically collects log data from your AWS resources. It then uses machine learning, statistical analysis, and graph theory to generate visualizations that help you to conduct faster and more efficient security investigations. The Detective prebuilt data aggregations, summaries, and context help you to quickly analyze and determine the nature and extent of possible security issues. 

Detective organizes Kubernetes and AWS data into findings such as:
+ Amazon EKS cluster details, including the IAM identity that created the cluster and the service role of the cluster. You can investigate the AWS and Kubernetes API activity of these IAM identities with Detective.
+ Container details, such as the image and security context. You can also review details for terminated Pods.
+ Kubernetes API activity, including both overall trends in API activity and details on specific API calls. For example, you can show the number of successful and failed Kubernetes API calls that were issued during a selected time range. Additionally, the section on newly observed API calls might be helpful to identify suspicious activity.

For more information on enablement, visit the [EKS User Guide on Detective Integration](https://docs.aws.amazon.com/eks/latest/userguide/integration-detective.html)

Amazon EKS audit logs is an optional data source package that can be added to your Detective behavior graph. You can view the available optional source packages, and their status in your account. For more information, see Amazon EKS audit logs for [Detective in the Amazon Detective User Guide](https://docs.aws.amazon.com/detective/latest/adminguide/source-data-types-EKS.html).


### Use Amazon GuardDuty, Amazon Inspector, and Amazon Security Hub to automate and accelerate security investigations for container environments
+ Use [Amazon GuardDuty](https://aws.amazon.com/guardduty/) if you do not currently have a solution for continuously monitoring EKS runtimes, analyzing EKS audit logs, identifying container image vulnerabilities, scanning for malware and other suspicious activity, Amazon strongly recommends the use of [Amazon GuardDuty](https://aws.amazon.com/guardduty/) and ,for customers who want a simple, fast, secure, scalable, and cost-effective one-click way to protect their AWS environments. Amazon GuardDuty combines machine learning (ML), anomaly detection, network monitoring, and malicious file discovery using various AWS data sources. When threats are detected, GuardDuty automatically sends security findings to [AWS Security Hub](https://aws.amazon.com/security-hub/), [Amazon EventBridge](https://aws.amazon.com/eventbridge/), and [Amazon Detective](https://aws.amazon.com/detective/). These integrations help centralize monitoring for AWS and partner services, automate responses to malware findings, and perform security investigations from GuardDuty. It also includes optional EKS Runtime Monitoring to detect runtime threats from over 30 security findings to protect your EKS clusters. The EKS Runtime Monitoring uses a fully managed EKS add-on that adds visibility into individual container runtime activities, such as file access, process execution, and network connections. GuardDuty can now identify specific containers within your EKS clusters that are potentially compromised and detect attempts to escalate privileges from an individual container to the underlying Amazon EC2 host and the broader AWS environment. It uses continuously updated threat intelligence feeds, such as lists of malicious IP addresses and domains, and machine learning to identify unexpected, potentially unauthorized, and malicious activity within your AWS environment before they escalate. This can include issues like escalation of privileges, use of exposed credentials, exposed network paths, communication with malicious IP addresses, domains, presence of malware on your Amazon EC2 instances and EKS container workloads, or discovery of suspicious API activity. GuardDuty informs you of the status of your AWS environment by producing security findings that you can view in the GuardDuty console or through Amazon EventBridge. GuardDuty also provides support for you to export your findings to an Amazon Simple Storage Service (S3) bucket, and integrate with other services such as [AWS Security Hub](https://aws.amazon.com/security-hub/), [Amazon Inspector](https://aws.amazon.com/inspector/), and [Amazon Detective](https://aws.amazon.com/detective/), which together can accelerate security investigations on EKS workloads and identify vulnerabilities in container images stored in [Amazon Elastic Container Registry (ECR)[(https://aws.amazon.com/ecr/).
+ [Amazon Inspector](https://aws.amazon.com/inspector/) automatically discovers workloads, such as Amazon EC2 instances, containers, and Lambda functions, and scans them for software vulnerabilities and unintended network exposure. Detect software vulnerabilities and unintended network exposure in AWS workloads such as Amazon EC2, AWS Lambda functions, and container images in Amazon ECR and within continuous integration and continuous delivery (CI/CD) tools, in near-real time. Incorporate security earlier in the development cycles and centrally manage software bill of materials (SBOM) exports for all monitored resources. Use the Amazon Inspector risk score to prioritize remediation reducing mean time to remediate (MTTR).
+ [AWS Security Hub](https://aws.amazon.com/security-hub/) to automate security best practice checks, aggregate security alerts into a single place and format, and understand your overall security posture across all of your AWS accounts. Detect deviations from security best practices with a single click. Automatically aggregate security findings in a standardized data format from AWS and partner services. Accelerate mean time to resolution (MTTR) with automated response and remediation actions. Visualize the security posture of your AWS-based applications.

### Use Amazon Security Lake to centralize security data to accelerate security investigation
Use [Amazon Security Lake](https://aws.amazon.com/security-lake/) to automatically centralizes security data from AWS environments, SaaS providers, on premises, and cloud sources into a purpose-built data lake stored in your account. With Security Lake, you can get a more complete understanding of your security data across your entire organization. You can also improve the protection of your workloads, applications, and data. Security Lake has adopted the [Open Cybersecurity Schema Framework (OCSF)](https://github.com/ocsf), an open standard. With OCSF support, the service normalizes and combines security data from AWS and a broad range of enterprise security data sources. This will enable you to have a comprehensive view of your security events across environments in a standardized format. 

### Additional resources
As the volume of logs increases, parsing and filtering them with Log Insights or another log analysis tool may become ineffective.  As an alternative, you might want to consider running [Sysdig Falco](https://github.com/falcosecurity/falco) and [ekscloudwatch](https://github.com/sysdiglabs/ekscloudwatch). Falco analyzes audit logs and flags anomalies or abuse over an extended period of time. The ekscloudwatch project forwards audit log events from CloudWatch to Falco for analysis. Falco provides a set of [default audit rules](https://github.com/falcosecurity/plugins/blob/master/plugins/k8saudit/rules/k8s_audit_rules.yaml) along with the ability to add your own. 

Yet another option might be to store the audit logs in S3 and use the SageMaker [Random Cut Forest](https://docs.aws.amazon.com/sagemaker/latest/dg/randomcutforest.html) algorithm to anomalous behaviors that warrant further investigation.

## Tooling
The following commercial and open source projects can be used to assess your cluster's alignment with established best practices:

+ [kubeaudit](https://github.com/Shopify/kubeaudit)
+ [kube-scan](https://github.com/octarinesec/kube-scan) Assigns a risk score to the workloads running in your cluster in accordance with the Kubernetes Common Configuration Scoring System framework
+ [kubesec.io](https://kubesec.io/)
+ [polaris](https://github.com/FairwindsOps/polaris)
+ [Starboard](https://github.com/aquasecurity/starboard)
+ [Snyk](https://support.snyk.io/hc/en-us/articles/360003916138-Kubernetes-integration-overview)
+ [Kubescape](https://github.com/kubescape/kubescape) Kubescape is an open source kubernetes security tool that scans clusters, YAML files, and Helm charts. It detects misconfigurations according to multiple frameworks (including [NSA-CISA](https://www.armosec.io/blog/kubernetes-hardening-guidance-summary-by-armo/?utm_source=github&utm_medium=repository) and [MITRE ATT&CK®](https://www.microsoft.com/security/blog/2021/03/23/secure-containerized-environments-with-updated-threat-matrix-for-kubernetes/).)
