# Networking in EKS

Kubernetes was designed to run distributed applications on a cluster of connected machines. Networking plays an integral part in orchestrating and running distributed applications in any Kubernetes environment. It is critical to understand the Kubernetes networking paradigm in order to build, run, and operate your applications efficiently. This section of the best practices advises on different cluster networking options possible with EKS.

## How to use this guide

This guide is meant for EKS cluster administrators and operators. Amazon EKS solves cluster networking through [Amazon VPC Container Network Interface (CNI)](https://github.com/aws/amazon-vpc-cni-k8s) plugin. Amazon EKS supports native VPC networking via the VPC CNI plugin for Kubernetes. Amazon VPC CNI supports different networking options. You can use this guide to learn different networking options supported by EKS so you can choose the best option for your needs.

The guide is organized into different topic areas for easier consumption. Each topic starts with a brief overview, followed by a list of recommendations and best practices for the reliability of your EKS clusters. The guide covers altarenate CNIs that you can use with Amazon EKS and best practices around the same.

We will also cover the basic networking concepts in the context of Kubernetes networking. If you would prefer to skip the learning and get straight to the choices and recommendations, you can jump ahead to Cluster Networking Options.

### Cluster Networking Options

There are several networking best practice areas that are pertinent when using a managed Kubernetes service like EKS:

### Secondary IP Mode
  
### Prefix IP Mode

### Security Groups Per Pod

### Custom Networking

### Multi-homed Pods & Multus

### Alternate CNIs

## Support for IPv6
