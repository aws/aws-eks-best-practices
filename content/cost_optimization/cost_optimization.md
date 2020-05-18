# Amazon EKS Best Practices Guide for Cost Optimization 

The cost optimization best practices includes the continual process of refinement and improvement of a system over its entire lifecycle to constantly look for ways to reduce costs. From your initial design to the ongoing operations of production workloads, adopting the practices specified in this document will help you to build and operate cost-aware systems. By doing so, you can achieve cost-effective business outcomes and maximize your return on investment.

# Design Principles

In the cloud, there are a number of principles that can help you achieve cost optimization of your microservices:

+ Ensure that microservices are independent of specific infrastructure types for running your containers — so that microservices can scale out independently on heterogeneous infrastructure. There can be exceptions like workloads that [require a GPU](https://docs.aws.amazon.com/eks/latest/userguide/gpu-ami.html) or a specific type of server.
+ Select optimally profiled container instances — profile your production or pre-production environments and monitor critical metrics. like CPU and memory, using [Amazon CloudWatch Container Insights for Amazon EKS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html). 
+ Take advantage of the different purchasing options that are available in AWS, e.g. On-Demand, Spot and Savings Plan.

# Definition

There are four general best practice areas for cost optimization in the cloud:

+ Cost-effective resources
+ Matching supply and demand
+ Expenditure awareness
+ Optimizing over time

As with the other best practices, there are trade-offs to consider. For example, do you want to optimize for speed to market or for cost? In some cases, it’s best to optimize for speed—going to market quickly, shipping new features, or simply meeting a deadline—rather than investing in upfront cost optimization. Design decisions are sometimes guided by haste as opposed to empirical data, as the temptation always exists to overcompensate “just in case” rather than spend time benchmarking for the most cost-optimal deployment. This often leads to drastically over-provisioned and under-optimized deployments. 

## Best Practices

### Cost-effective resources
**Ensure that the infrastructure used to deploy the containerized service matches the application profile and scaling needs. Use pricing models for effective utilization.**



### Key AWS Services
Cost optimization is supported by the following AWS services and features:
+ Cost-effective resources – Amazon EC2 provides multiple instance types, such as Reserved Instances and Spot Instances, at different prices.
+ Matching supply and demand – Match user demand with Auto Scaling. Consider Savings Plan (Previously Reserved Instances) for predictable workloads. Use managed data stores for elasticity and durability of the application data.
+ Expenditure awareness – The Billing and Cost Management console dashboard provides an overview of your AWS usage. Use AWS Organizations for granular billing details.
+ Optimizing over time – Amazon CloudWatch Container Metrics provides metrics around usage of resources by the EKS cluster. In addition to the Kubernetes dashboard, there are several tools in the Kubernetes ecosystem that can be used to monitor Kubernetes clusters, such as Prometheus.

### Resources
Refer to the following resources to learn more about AWS best practices for cost optimization.

Videos
+	[AWS re:Invent 2019: Save up to 90% and run production workloads on Spot Instances (CMP331-R1)](https://www.youtube.com/watch?v=7q5AeoKsGJw)

Documentation and Blogs
+	[Cost optimization for Kubernetes on AWS](https://aws.amazon.com/blogs/containers/cost-optimization-for-kubernetes-on-aws/)
+	[Using Spot Instances with EKS](https://ec2spotworkshops.com/using_ec2_spot_instances_with_eks.html)
+   [Extending the EKS API: Managed Node Groups](https://aws.amazon.com/blogs/containers/eks-managed-node-groups/)
+	[Autoscaling with Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html) 
+	[Setting Up Container Insights on Amazon EKS and Kubernetes ](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html)
+	[Amazon EKS supports tagging](https://docs.aws.amazon.com/eks/latest/userguide/eks-using-tags.html)
+	[Amazon ECR Lifecycle Policies](https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html)
+	[Amazon EKS-Optimized AMI with GPU Support](https://docs.aws.amazon.com/eks/latest/userguide/gpu-ami.html)
+	[AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/)
+   [Amazon EKS on AWS Fargate](https://aws.amazon.com/blogs/aws/amazon-eks-on-aws-fargate-now-generally-available/)
+	[Amazon EKS pricing](https://aws.amazon.com/eks/pricing/)

Tools
+	[AWS Organizations](https://aws.amazon.com/organizations/)
+	[What is AWS Billing and Cost Management?](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
+   [Third party - Kube Cost](https://kubecost.com/)

