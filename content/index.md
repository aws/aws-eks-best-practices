# Introduction
Welcome to the EKS Best Practices Guides.  The primary goal of this project is to offer a set of best practices for day 2 operations for Amazon EKS. We elected to publish this guidance to GitHub so we could iterate quickly, provide timely and effective recommendations for variety of concerns, and easily incorporate suggestions from the broader community.  

We currently have published guides for the following topics: 

* [Best Practices for Security](security/docs/)
* [Best Practices for Reliability](reliability/docs/)
* Best Practices for Cluster Autoscaling: [karpenter](karpenter/), [cluster-autoscaler](cluster-autoscaling/)
* [Best Practices for Networking](networking/index/)
* [Best Practices for Scalability](scalability/docs/)
* [Best Practices for Cluster Upgrades](upgrades/)
* [Best Practices for Cost Optimization](cost_optimization/cfm_framework.md)
* [Best Practices for Running Windows Containers](windows/docs/ami/)

We also open sourced a Python based CLI (Command Line Interface) called [hardeneks](https://github.com/aws-samples/hardeneks) to check some of the recommendations from this guide.

In the future we will be publishing best practices guidance for performance, cost optimization, and operational excellence. 

## Related guides
In addition to the [EKS User Guide](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html), AWS has published several other guides that may help you with your implementation of EKS.

* [EMR Containers Best Practices Guides](https://aws.github.io/aws-emr-containers-best-practices/)
* [Data on EKS](https://awslabs.github.io/data-on-eks/)
* [AWS Observability Best Practices](https://aws-observability.github.io/observability-best-practices/)
* [Amazon EKS Blueprints for Terraform](https://aws-ia.github.io/terraform-aws-eks-blueprints/)
* [Amazon EKS Blueprints Quick Start](https://aws-quickstart.github.io/cdk-eks-blueprints/)

## Contributing
We encourage you to contribute to these guides. If you have implemented a practice that has proven to be effective, please share it with us by opening an issue or a pull request. Similarly, if you discover an error or flaw in the guidance we've already published, please submit a PR to correct it. The guidelines for submitting PRs can be found in our [Contributing Guidelines](https://github.com/aws/aws-eks-best-practices/blob/master/CONTRIBUTING.md).
