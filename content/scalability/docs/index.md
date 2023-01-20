# EKS Scalability best practices
This guide provides advice for scaling EKS clusters. The goal of scaling an EKS cluster is to maximize the amount of work a single cluster can perform. Using a single, large EKS cluster can reduce operational load compared to using multiple clusters, but it has trade-offs for things like multi-region deployments, tenant isolation, and cluster upgrades. In this document we will focus on how to achieve maximum scalability with a single cluster.

## How to use this guide
This guide is meant for developers and administrators responsible for creating and managing EKS clusters in AWS. It focuses on some generic Kubernetes scaling practices, but it does not have specifics for self-managed Kubernetes clusters or clusters that run outside of an AWS region with [EKS Anywhere](https://anywhere.eks.amazonaws.com/).

Each topic has a brief overview, followed by recommendations and best practices for operating EKS clusters at scale. Topics do not need to be read in a particular order and recommendations should not be applied without testing and verifying they work in your clusters.

## Understanding scaling dimensions
Scalability is different from performance and [reliability](https://aws.github.io/aws-eks-best-practices/reliability/docs/), and all three should be considered when planning your cluster and workload needs. As clusters scale, they need to be monitored, but this guide will not cover monitoring best practices. EKS can scale to large sizes, but you will need to plan how you are going to scale a cluster beyond about 300 nodes or 5000 pods.

Scaling in Kubernetes is multi-dimensional and there are no specific settings or recommendations that work in every situation. The main areas areas where we can provide guidance for scaling include:

* [Kubernetes Control Plane](control-plane)
* [Supporting Infrastructure](supporting-infrastructure)
* [Cluster Services](cluster-services)
* [Workloads](workloads)

The Kubernetes Control Plane in an EKS cluster includes all of the services AWS runs and scales for you automatically (e.g. Kubernetes API server) as well as components that run in your account (e.g. Kubelet). Scaling the Control Plane is a shared responsibility based on Kubernetes architecture and AWS infrastructure.

Supporting infrastructure scaling deals with AWS resources that are required for your cluster and workloads, but they are outside of the EKS cluster. Resources such as EC2, load balancers, and storage should all be scaled as your cluster scales.

Cluster services are Kubernetes controllers and applications that run inside the cluster and provide functionality for your cluster and workloads. These can be [EKS Add-ons](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html) and also other services or Helm charts you install for compliance and integrations. These services are often depended on by workloads and as your workloads scale your cluster services will need to scale with them.

Workloads are the reason you have a cluster and should scale horizontally with the cluster. There are integrations and settings that workloads have in Kubernetes that can help the cluster scale. There are also architectural considerations with Kubernetes abstractions such as namespaces and services.

## Feedback
This guide is being released on GitHub so as to collect direct feedback and suggestions from the broader EKS/Kubernetes community. If you have a best practice that you feel we ought to include in the guide, please file an issue or submit a PR in the GitHub repository. Our intention is to update the guide periodically as new features are added to the service or when a new best practice evolves.
