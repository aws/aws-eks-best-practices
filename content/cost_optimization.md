# Cost Optimization Pillar
The cost optimization pillar includes the continual process of refinement and improvement of a system over its entire lifecycle to constantly look for ways to reduce costs. From your initial design to the ongoing operations of production workloads, adopting the practices specified in this document will help you to build and operate cost-aware systems. By doing so, you can achieve cost-effective business outcomes and maximize your return on investment.

# Design Principles
In the cloud, there are a number of principles that can help you achieve cost optimization of your microservices:

+ Ensure that microservices are disposable—that is, the microservices are based on disposable and immutable containers. By ensuring that containers are disposable, recovering from a server failure is fast as the containers can be moved to different servers easily. When containers are based on immutable images, the containers can be upgraded to new versions by updating the image, deploying it, and then disposing of the old image.
+ Ensure that microservices are independent of specific infrastructure types for running your containers—so that microservices can scale out independently on heterogeneous infrastructure. There can be exceptions like workloads that [require a GPU](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-gpu.html) or a specific type of server.
+ Select optimally profiled container instances—profile your production or pre-production environments and monitor critical metrics. like CPU and memory, using [Amazon CloudWatch Container Insights for Amazon EKS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html). 
+ Take advantage of the different purchasing options that are available in AWS, e.g. On-Demand, Spot, and Reserved Instances.

# Definition
There are four general best practice areas for cost optimization in the cloud:

+ Cost-effective resources
+ Matching supply and demand
+ Expenditure awareness
+ Optimizing over time

As with the other pillars, there are trade-offs to consider. For example, do you want to optimize for speed to market or for cost? In some cases, it’s best to optimize for speed—going to market quickly, shipping new features, or simply meeting a deadline—rather than investing in upfront cost optimization. Design decisions are sometimes guided by haste as opposed to empirical data, as the temptation always exists to overcompensate “just in case” rather than spend time benchmarking for the most cost-optimal deployment. This often leads to drastically over-provisioned and under-optimized deployments. 

## Best Practices

### Cost-effective resources
Amazon EKS supports running has different pricing models for the Fargate launch type that are based on the amount of vCPU and memory resources that your containerized application requests. With an EC2 launch type, you pay for AWS resources (e.g., EC2 instances, EBS volumes, and Load Balancers) that you create to store and run your application. 

### Matching supply and demand

### Expenditure awareness
Amazon EKS supports adding AWS tags to your Amazon EKS clusters. This makes it easy to control access to the EKS API for managing your clusters. Tags added to an EKS cluster are specific to the AWS EKS cluster resource, they do not propagate to other AWS resources used by the cluster such as EC2 instances or Load balancers. Today, cluster tagging is supported for all new and existing EKS clusters via the AWS API, Console, and SDKs. 

Adding and Listing tags to an EKS cluster:
```
$ aws eks tag-resource --resource-arn arn:aws:eks:us-west-2:xxx:cluster/ekscluster1 --tags team=devops,env=staging,bu=cio,costcenter=1234 
$ aws eks list-tags-for-resource --resource-arn arn:aws:eks:us-west-2:xxx:cluster/ekscluster1
{
    "tags": {
        "bu": "cio", 
        "env": "staging", 
        "costcenter": "1234", 
        "team": "devops"
    }
}```

### Optimizing over time

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
+	[Using Spot Instances with EKS](https://ec2spotworkshops.com/using_ec2_spot_instances_with_eks.html)
+	[Autoscaling with Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html) 
+	Kubernetes Cluster Monitoring
+	Amazon EEKS supports tagging
+	Clean up Your Container Images with Amazon ECR Lifecycle Policies
+	Running GPU-Accelerated Kubernetes Workloads on P3 and P2 EC2 Instances with Amazon EKS
+	AWS Fargate pricing
+	Amazon EKS pricing

Tools
+	AWS Organizations
+	What is AWS Billing and Cost Management?
+	Automated Image Cleanup for Amazon ECR
+ Third party - Kube Cost 

