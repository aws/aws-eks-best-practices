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
**Ensure that the infrastructure used to deploy the containerized service matches the application profile and scaling needs. Use pricing models for effective utilization.**

Amazon EKS on AWS supports running the worker nodes on clusters using either EC2 Instance types or AWS Fargate, and on premises using AWS Outposts. Amazon EC2 based worker nodes can be either On-Demand Instances or Amazon EC2 Spot Instances. It has different pricing models for the Fargate launch type that are based on the amount of vCPU and memory resources that your containerized application requests. With an EC2 launch type, you pay for AWS resources (e.g., EC2 instances, EBS volumes, and Load Balancers) that you create to store and run your application. [There are important considerations that need to be taken into account when using AWS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html#fargate-considerations).

EC2 Spot Instances offer spare compute capacity available in the AWS Cloud at steep discounts compared to On-Demand Instances. Spot Instances typically cost 50–90% less than On-Demand Instances. Powering your EKS cluster with Spot Instances lets you reduce the cost of running your existing containerized workloads, or increase your compute capacity by two to ten times while keeping the same budget. Or you could do a combination of running a cluster with both On-Demand as well as Spot Instances. 

The right strategy will depend upon a number of factors—including the application architecture's ability to run on Spot Instances, and the need to maintain a minimum amount of core compute capacity regardless of the availability of Spot Instances. There are [reference architectures that show how automatic scaling with a mix of On-Demand and Spot Instances can be architected in an EKS Cluster](https://eksworkshop.com/spotworkers/workers/). 

For AWS Fargate, you only pay for the amount of vCPU and memory resources that your containerized application requests. AWS Fargate pricing is calculated based on the vCPU and memory resources used from the time you start to download your container image until the Amazon EKS Pod terminates, rounded up to the nearest second. [When pods are scheduled on Fargate, the vCPU and memory reservations within the pod specification determine how much CPU and memory to provision for the pod](https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html). 

**Monitoring overall CPU and memory utilization of the Container Cluster to ensure that you are using the right EC2 instance type**

### Matching supply and demand

Leverage Auto Scaling at a Pod level as well on Container nodes, to provision resources and keep a buffer for traffic spikes. Leverage pricing models to gain efficiency for burst and spike modes. 

#### Managed Node Groups

[Amazon EKS managed node groups automate the provisioning and lifecycle management of nodes (Amazon EC2 instances) for Amazon EKS Kubernetes clusters.](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) All managed nodes are provisioned as part of an Amazon EC2 Auto Scaling group that is managed for you by Amazon EKS and all resources including Amazon EC2 instances and Auto Scaling groups run within your AWS account. A managed node group's Auto Scaling group spans all of the subnets that you specify when you create the group. Amazon EKS tags managed node group resources so that they are configured to use the Kubernetes Cluster Autoscaler. 

#### Pod Auto Scaling

[Amazon EKS support both Horizontal Pod Autoscaler and Vertical Pod Autoscaler for scaling of Pods.](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html)
+ Horizontal Pod Autoscaler - The Kubernetes Horizontal Pod Autoscaler automatically scales the number of pods in a deployment, replication controller, or replica set based on that resource's CPU utilization.
+ Vertical Pod Autoscaler - The Kubernetes Vertical Pod Autoscaler automatically adjusts the CPU and memory reservations for your pods to help "right size" your applications. This adjustment can improve cluster resource utilization and free up CPU and memory for other pods. 
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
}
```
[After you activate cost allocation tags in the AWS Cost Explorer, AWS uses the cost allocation tags to organize your resource costs on your cost allocation report, to make it easier for you to categorize and track your AWS costs.](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)

### Optimizing over time

As microservices scale, leverage platform tools to profile the service and usage. [Amazon EKS-Optimized AMI with and without GPU support are available.](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html). \

An Amazon EKS cluster can use various EC2 instance types that the microservice needs,including such as Amazon EC2 GPU instances. Amazon EC2 P3 and P2 instances, featuring NVIDIA GPUs, power some of the most computationally advanced workloads today, including machine learning (ML), high performance computing (HPC), financial analytics, and video transcoding. [Now Amazon Elastic Container Service for Kubernetes (Amazon EKS) supports P3 and P2 instances, making it easy to deploy, manage, and scale GPU-based containerized applications.](https://aws.amazon.com/blogs/compute/running-gpu-accelerated-kubernetes-workloads-on-p3-and-p2-ec2-instances-with-amazon-eks/)

Machine learning (ML) training is increasingly being done inside containers. Being able to run those workloads on machines that are optimized for machine learning is more cost effective than running them on generic EC2 instances.


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

