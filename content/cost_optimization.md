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

