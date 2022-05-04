# Introduction

A "Network Best Practices" guide is forthcoming.

In the interim, please review [Cluster VPC and subnet considerations.](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html)

## Subnet Calculator Spreadsheet

Some organizations have limited internal network address space to assign large CIDRs to EKS clusters. Additionally, the VPC CNI can use more IP addresses than expected.

An Excel spreadsheet is provided to calculate subnet IP usage based on the number and type of instances. The IP usage of the cluster is compared to a given subnet, to determine if it's sufficient.

[Download the Excel spreadsheet (xlsx file).](subnet-calc.xlsx)

[Download the spreadsheet in OpenDocument format (ods file).](subnet-calc.ods)