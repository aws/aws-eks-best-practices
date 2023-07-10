# Multi Account Strategy for Multi Tenant Clusters

AWS recommends using a [multi account strategy](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html) and AWS organizations to help isolate and manage your business applications and data. There are [many benefits](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/benefits-of-using-multiple-aws-accounts.html) to using a multi account strategy.

There are many benefits to using a multi account strategy with EKS:

+ Increased AWS API service quotas. Quotas are applied to AWS accounts, and using more multiple accounts for your workloads increases the overall quota available to your workloads.
+ Simpler IAM. Granting workloads and the operators that support them access to only their own AWS accounts means less time crafting fine-grained IAM policies to achieve the principle of least privilege.
+ Improved Isolation. By design, all resources provisioned within an account are logically isolated from resources provisioned in other accounts, even within your own AWS environment. This isolation boundary provides you with a way to limit the risks of an application-related issue, misconfiguration, or malicious actions. If an issue occurs within one account, impacts to workloads contained in other accounts can be either reduced or eliminated. 
+ More benefits, as described in the [AWS Multi Account Strategy Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/benefits-of-using-multiple-aws-accounts.html#group-workloads-based-on-business-purpose-and-ownership)

## Planning for a Multi Workload Account Strategy for Multi Tenant Clusters

In a multi account AWS strategy, resources that belong to a given workload such as S3 buckets, ElastiCache clusters and DynamoDBs are all created in an AWS account that contains all the resources for that workload. These is referred to as a workload account. Deploying resources into a dedicated workload account is similar to deploying kubernetes resources into a dedicated namespace. There is no additional cost for using multiple accounts in an AWS organization.

Workload accounts can then be further broken down by software development lifecycle or other requirements if appropriate, e.g. a given workload can have a production account, a development account, or accounts for hosting instances of that workload in a specific region. [More information](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-workload-oriented-ous.html) is available in this AWS whitepaper.

You can adopt following approaches when implementing EKS Multi-account strategy:

## Centralized EKS Cluster

In this approach, your EKS Cluster will be deployed in a single AWS account called the `Cluster Account`, however using [IAM roles for Service Accounts (IRSA)](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) and [AWS Resource Access Manager (RAM)](https://aws.amazon.com/ram/) you can adapt a multi account strategy for your multi tenant EKS cluster. The cluster account will contain the VPC, subnets, EKS cluster, EC2/Fargate compute resources, and any additional networking or configurations needed to run your EKS cluster.

![](./images/multi-account-eks.jpg)

 
### Implementing a Multi Workload Account Strategy for Multi Tenant Cluster

#### Sharing Subnets With AWS Resource Access Manager 

AWS Resource Resource Access Manager (RAM) allows you to share resources across AWS accounts. 

If RAM is enabled for your AWS Organization, you can share the VPC Subnets from the Cluster account to your workload accounts. This will allow AWS resources owned by your workload accounts, such as ElastiCache Clusters or RDS DBs to be deployed into the same VPC as your EKS cluster, and be consumable by the workloads running on your EKS cluster.

To share a resource via RAM, open up RAM in the AWS console of the cluster account and select "Resource Shares" and "Create Resource Share". Name your Resource Share and Select the subnets you want to share. Select Next again and enter the 12 digit account IDs for the workload accounts you wish to share the subnets with, select next again, and click Create resource share to finish. After this step, the workload account can deploy resources into those subnets.

### Accessing AWS API Resources with IAM Roles For Service Accounts
 
[IAM Roles for Service Accounts (IRSA)](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) allows you to deliver temporary AWS credentials to your workloads running on EKS. IRSA can be used to get temporary credentials for IAM roles in the workload accounts from the cluster account. This allows your workloads running on your EKS clusters in the cluster account to consume AWS API resources, such as S3 buckets hosted in the workload account seemlessly, and use IAM authentication for resources like AWS RDS Databases or AWS EFS FileSystems. 

AWS API resources and other Resources that use IAM authentication in a workload account can only be accessed by credentials for IAM roles in that same workload account, except where cross account access is capable and has been explicity enabled.

#### Enabling IRSA for cross account access

To enable IRSA for workloads in your Cluster Account to access resources in your Workload accounts, you first must create an IAM OIDC identity provider in your workload account. This can be done with the same procedure for setting up IRSA, except the Identity Provider will be created in the workload account: https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html

Then when configuring IRSA for your workloads on EKS, you can [follow the same steps as the documentation](https://docs.aws.amazon.com/eks/latest/userguide/associate-service-account-role.html), but use the [12 digit account id of the workload account](https://docs.aws.amazon.com/eks/latest/userguide/cross-account-access.html) as mentioned in the section "Example Create an identity provider from another account's cluster".

## De-centralized EKS Clusters

In this approach, EKS clusters are deployed to respective workload AWS Accounts and live along side with other AWS resources like S3 buckets, DynamoDB tables, etc., Each workload account is independant, self-sufficient, and operated by respective Business Unit/Application teams. This model allows the Platform teams to create reusuable blueprints for various cluster capabilities (AI/ML cluster, Batch processing, General purpose, etc.,) and vend the clusters based on the application team requirements. Both application and platform teams operate out of their respective [GitOps](https://www.weave.works/technologies/gitops/) repositories to manage the deployments to the workload clusters.

![De-centralized Cluster Architecture](./images/multi-account-eks-decentralized.png)

GitOps is a way of managing application and infrastructure deployment so that the whole system is described declaratively in a Git repository. It’s an operational model that offers you the ability to manage the state of multiple Kubernetes clusters using the best practices of version control, immutable artifacts, and automation. In this multi cluster model, each workload cluster is bootstraped with multiple GitOps repo, allowing each team (application, platform, security, etc.,) to deploy their respective changes on the cluster. 

You would utilize [IAM roles for Service Accounts (IRSA)](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) in each account to allow your EKS workloads to get temporary AWS credentials to securely access other AWS resources. IAM Roles are created in respective workload AWS Accounts and map them to k8s service accounts to provide temporary IAM access. So, no cross-account access is required in this approach. Follow the ]IAM roles for Service Accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) documentation on how to setup in each workload account.


## Centralized vs De-centralized Multi tenant EKS clusters


|# |Centralized EKS cluster | De-centralized EKS clusters |
|:--|:--|:--|
|Cluster Management:  |Managing a single EKS cluster is easier than administrating multiple clusters | An Efficient cluster management automation is necessary to reduce the operational overhead of managing multiple EKS clusters|
|Cost Efficiency: | Less resource overhead, able to bin pack the workloads efficiently|May create inefficiences in resource usage, also increases the resource allocation for the operational software |
|Resilience: | Creates a single point of failure | If a cluster breaks, the damage is limited to only the workloads that run on that cluster. All other workloads are unaffected |
|Isolation & Security:|Isolation/Soft Multi-tenancy is achieved using k8s native constructs like `Namespaces`. Workloads may share the underlying resources like CPU, memory, etc.,|Stronger isolation as the workloads run in individual clusters that don't share any resources|
|Performance & Scalabity:|As the workloads grow, you may hit the k8s scalability limitations of a single k8s cluster|You can size the EKS clusters based on the workload and the demand|
|Access Management: |Need to maintain many different roles and users in the cluster to provide access to all workload teams. Higher risk of breaking something| Simplified access management as each cluster is dedicated to a workload/team|