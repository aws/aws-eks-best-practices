# Compliance
Compliance is a shared responsibility between AWS and the consumers of its services. Generally speaking, AWS is responsible for “security of the cloud” whereas its users are responsible for “security in the cloud.” The line that delineates what AWS and its users are responsible for will vary depending on the service. For example, with Fargate, AWS is responsible for managing the physical security of its data centers, the hardware, the virtual infrastructure (Amazon EC2), and the container runtime (Docker). Users of Fargate are responsible for securing the container image and their application. Knowing who is responsible for what is an important consideration when running workloads that must adhere to compliance standards.

The following table shows the compliance programs with which the different container services conform.

| Compliance Program | Amazon ECS | Amazon EKS | ECS Fargate | Amazon ECR |
| ------------------ |:----------:|:----------:|:-----------:|:----------:|
| PCI DSS Level 1	| 1 | 1 | 1 | 1 |
| HIPAA Eligible	| 1 | 1	| 1	| 1 |
| SOC I | 1 | 1 | 1 | 1 |
| SOC II | 1 |	1 |	1 |	1 |
| SOC III |	1 |	1 |	1 |	1 |
| ISO 27001:2013 | 1 | 1 | 1 | 1 |
| ISO 9001:2015 | 1 | 1 | 1 | 1 |
| ISO 27017:2015 |	1 |	1 |	1 |	1 |
| ISO 27018:2019 |	1 |	1 |	1 |	1 |
| IRAP | 1 | 0 | 1 | 1 |
| FedRAMP Moderate (East/West) | 1 | 3PAO Assessment | 0 | 1 |
| FedRAMP High (GovCloud) | 1 | 0 | 0 | 1 |
| DOD CC SRG | 1 |	Undergoing assessment |	0 |	1 |
| HIPAA BAA | 1 | 1 | 1 | 1 |
| MTCS | 1 | 1 | 0 | 1 |
| C5 | 1 | 1 | 0 | 1 |
| K-ISMS | 1 | 1 | 0 | 1 |
| ENS High | 1 | 1 | 0 | 1 |
| OSPAR | 1 | 0 | 0 | 1 | 
| HITRUSST CSF | 1 | 1 | 1 | 1 |

Compliance status changes over time. For the latest status, always refer to https://aws.amazon.com/compliance/services-in-scope/. 

### Tools and resources
+ [kube-bench](https://github.com/aquasecurity/kube-bench)
+ [docker-bench-security](https://github.com/docker/docker-bench-security)
+ [actuary](https://github.com/diogomonica/actuary)
+ [AWS Inspector](https://aws.amazon.com/inspector/)