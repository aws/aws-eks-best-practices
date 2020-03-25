# Compliance
Compliance is a shared responsibility between AWS and the consumers of its services. Generally speaking, AWS is responsible for “security of the cloud” whereas its users are responsible for “security in the cloud.” The line that delineates what AWS and its users are responsible for will vary depending on the service. For example, with Fargate, AWS is responsible for managing the physical security of its data centers, the hardware, the virtual infrastructure (Amazon EC2), and the container runtime (Docker). Users of Fargate are responsible for securing the container image and their application. Knowing who is responsible for what is an important consideration when running workloads that must adhere to compliance standards. 
The following table shows the compliance programs with which the different container services conform.

| Compliance Program | Amazon ECS | Amazon EKS | AWS Fargate | Amazon ECR |
| ------------------ |:----------:|:----------:|:-----------:|:----------:|
| PCI DSS Level 1	| 1 |	1 |	1 |	1 |
| HIPAA Eligible	| 1 |	1	| 1	| 1 |
| SOC I |	1 |	1 |	1 |	1 |
| SOC II | 1 |	1 |	1 |	1 |
| SOC III |	1 |	1 |	1 |	1 |
| ISO 27001 |	1 |	1 |	1 |	1 |
| ISO 9001 | 1 |	1 |	1 |	1 |
| ISO 27017 |	1 |	1 |	1 |	1 |
| ISO 27018 |	1 |	1 |	1 |	1 |
| IRAP | 1 | 0 | 0 | 0 |
| FedRAMP | | | | |
| JAB Review | 0 | 0 | JAB Review | |
| DOD CC SRG | JAB Review |	0 |	0 |	JAB Review |
| MTCS | 1 | 0 | 0 | 1 |
| C5 | 1 | 0 | 0 | 1 |
| K-ISMS | 0 | 0 | 0 | 0 |
| ENS High | 1 | 0 | 1 | 0 |

### Tools
+ kube-bench
+ docker-bench-security
+ actuary