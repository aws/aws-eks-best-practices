---
search:
  exclude: true
---


# 알려진 제한 및 서비스 할당량
Amazon EKS는 다양한 워크로드에 사용할 수 있고 광범위한 AWS 서비스와 상호 작용할 수 있습니다. 고객 워크로드에서도 비슷한 범위의 AWS 서비스 할당량(Quota) 및 확장성을 저하하는 기타 문제가 발생할 수 있습니다. 

AWS 계정에는 기본 할당량(팀에서 요청할 수 있는 각 AWS 리소스 수의 상한선)이 있습니다. 각 AWS 서비스는 자체 할당량을 정의하며 할당량은 일반적으로 리전별로 다릅니다. 일부 할당량(Soft Limit)에 대해서는 증가를 요청할 수 있지만 다른 할당량(Hard Limit)은 늘릴 수 없습니다. 애플리케이션을 설계할 때는 이러한 값을 고려해야 합니다. 이러한 서비스 제한을 정기적으로 검토하고 애플리케이션 설계에 반영하는 것을 고려해 보십시오.

[AWS 서비스 할당량 콘솔](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html#request-increase) 또는 [AWS CLI](https://repost.aws/knowledge-center/request-service-quota-increase-cli)를 사용하여 계정의 사용량을 검토하고 할당량 증가 요청을 열 수 있습니다. 서비스 할당량에 대한 자세한 내용과 서비스 할당량 증가에 대한 추가 제한 또는 공지는 해당 AWS 서비스의 AWS 설명서를 참조하십시오.


!!! note
    [Amazon EKS 서비스 할당량](https://docs.aws.amazon.com/eks/latest/userguide/service-quotas.html)에는 서비스 할당량이 나열되어 있으며 가능한 경우 증가를 요청할 수 있는 링크가 있습니다.


## 기타 AWS 서비스 할당량 
EKS 고객이 다른 AWS 서비스에 대해 아래 나열된 할당량의 영향을 받는 것을 확인했습니다. 이들 중 일부는 특정 사용 사례 또는 구성에만 적용될 수 있지만, 솔루션이 확장됨에 따라 이러한 문제가 발생할 수 있는지 고려해 볼 수 있습니다. 할당량은 서비스별로 정리되어 있으며 각 할당량에는 L-XXXXXXXX 형식의 ID가 있습니다. 이 ID를 사용하여 [AWS 서비스 할당량 콘솔](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html#request-increase)에서 조회할 수 있습니다.


| Service        | Quota (L-xxxxx)                                                                            | **Impact**                                                                                                         | **ID (L-xxxxx)** | default |
| -------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ---------------- | ------- |
| IAM            | Roles per account                                                                          | 계정의 클러스터 또는 IRSA 역할 수를 제한할 수 있습니다.                                                      | L-FE177D64       | 1,000   |
| IAM            | OpenId connect providers per account                                                       | 계정당 클러스터 수를 제한할 수 있습니다. IRSA는 OpenID Connect를 사용합니다.                                       | L-858F3967       | 100     |
| IAM            | Role trust policy length                                                                   | IRSA 사용 시 IAM 역할이 연결되는 클러스터 수를 제한할 수 있습니다.                                        | L-C07B4B0D       | 2,048   |
| VPC            | Security groups per network interface                                                      | 클러스터의 네트워킹 제어 또는 연결을 제한할 수 있습니다.                                           | L-2AFB9258       | 5       |
| VPC            | IPv4 CIDR blocks per VPC                                                                   | EKS 워커 노드 수를 제한할 수 있습니다.                                                                           | L-83CA0A9D       | 5       |
| VPC            | Routes per route table                                                                     | 클러스터의 네트워킹 제어 또는 연결을 제한할 수 있습니다.                                           | L-93826ACB       | 50      |
| VPC            | Active VPC peering connections per VPC                                                     | 클러스터의 네트워킹 제어 또는 연결을 제한할 수 있습니다.                                           | L-7E9ECCDB       | 50      |
| VPC            | Inbound or outbound rules per security group.                                              | 클러스터의 네트워킹 제어 또는 연결을 제한할 수 있습니다. EKS의 일부 컨트롤러는 새 규칙을 생성합니다. | L-0EA8095F       | 50      |
| VPC            | VPCs per Region                                                                            | 계정당 클러스터 수 또는 클러스터의 네트워킹 제어 또는 연결을 제한할 수 있습니다.     | L-F678F1CE       | 5       |
| VPC            | Internet gateways per Region                                                               | 계정당 클러스터 수 또는 클러스터의 네트워킹 제어 또는 연결을 제한할 수 있습니다.     | L-A4707A72       | 5       |
| VPC            | Network interfaces per Region                                                              | EKS 워커 노드 수를 제한하거나 또는 Impact EKS 컨트롤 플레인 스케일링/업데이트 활동에 영향을 줍니다.                   | L-DF5E4CA3       | 5,000   |
| VPC            | Network Address Usage                                                                      | 계정당 클러스터 수 또는 클러스터의 네트워킹 제어 또는 연결을 제한할 수 있습니다.     | L-BB24F6E5       | 64,000  |
| VPC            | Peered Network Address Usage                                                               | 계정당 클러스터 수 또는 클러스터의 네트워킹 제어 또는 연결을 제한할 수 있습니다.     | L-CD17FD4B       | 128,000 |
| ELB            | Listeners per Network Load Balancer                                                        | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-57A373D6       | 50      |
| ELB            | Target Groups per Region                                                                   | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-B22855CB       | 3,000   |
| ELB            | Targets per Application Load Balancer                                                      | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-7E6692B2       | 1,000   |
| ELB            | Targets per Network Load Balancer                                                          | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-EEF1AD04       | 3,000   |
| ELB            | Targets per Availability Zone per Network Load Balancer                                    | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-B211E961       | 500     |
| ELB            | Targets per Target Group per Region                                                        | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-A0D0B863       | 1,000   |
| ELB            | Application Load Balancers per Region                                                      | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-53DA6B97       | 50      |
| ELB            | Classic Load Balancers per Region                                                          | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-E9E9831D       | 20      |
| ELB            | Network Load Balancers per Region                                                          | 클러스터로의 트래픽 수신 제어를 제한할 수 있습니다.                                                           | L-69A177A2       | 50      |
| EC2            | Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances (as a maximum vCPU count) | EKS 워커 노드 수를 제한할 수 있습니다.                                                                           | L-1216C47A       | 5       |
| EC2            | All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests (as a maximum vCPU count)  | EKS 워커 노드 수를 제한할 수 있습니다.                                                                           | L-34B43A08       | 5       |
| EC2            | EC2-VPC Elastic IPs                                                                        | NAT GW (및 VPC) 수를 제한할 수 있으며, 이로 인해 한 지역의 클러스터 수가 제한될 수 있습니다.                | L-0263D0A3       | 5       |
| EBS            | Snapshots per Region                                                                       | 스테이트풀 워크로드의 백업 전략을 제한할 수 있습니다.                                                               | L-309BACF6       | 100,000 |
| EBS            | Storage for General Purpose SSD (gp3) volumes, in TiB                                      | EKS 워커 노드 또는 퍼시스턴트볼륨 스토리지의 수를 제한할 수 있습니다.                                              | L-7A658B76       | 50      |
| EBS            | Storage for General Purpose SSD (gp2) volumes, in TiB                                      | EKS 워커 노드 또는 퍼시스턴트볼륨 스토리지의 수를 제한할 수 있습니다.                                             | L-D18FCD1D       | 50      |
| ECR            | Registered repositories                                                                    | 클러스터의 워크로드 수를 제한할 수 있습니다.                                                                 | L-CFEB8E8D       | 100,000  |
| ECR            | Images per repository                                                                      | 클러스터의 워크로드 수를 제한할 수 있습니다.                                                                 | L-03A36CE1       | 10,000  |
| SecretsManager | Secrets per Region                                                                         | 클러스터의 워크로드 수를 제한할 수 있습니다.                                                                 | L-2F66C23C       | 500,000 |


## AWS 요청 스로틀링

또한 AWS 서비스는 모든 고객이 성능을 유지하고 사용할 수 있도록 요청 조절을 구현합니다. 서비스 할당량과 마찬가지로 각 AWS 서비스는 자체 요청 제한 임계값을 유지합니다. 워크로드에서 대량의 API 호출을 빠르게 실행해야 하거나 애플리케이션에서 요청 제한 오류가 발견되면 해당 AWS 서비스 설명서를 검토하는 것이 좋습니다. 

대규모 클러스터에서 또는 클러스터가 크게 확장되는 경우 EC2 네트워크 인터페이스 또는 IP 주소 프로비저닝과 관련된 EC2 API 요청에서 요청 조절이 발생할 수 있습니다. 아래 표에는 고객이 요청 스로틀링으로 인해 겪었던 몇 가지 API 작업이 나와 있습니다.
EC2 속도 제한 기본값 및 속도 제한 인상 요청 단계는 [쓰로틀링에 관한 EC2 문서](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/throttling.html) 에서 확인할 수 있습니다.


| Mutating Actions                | Read-only Actions               |
| ------------------------------- | ------------------------------- |
| AssignPrivateIpAddresses        | DescribeDhcpOptions             |
| AttachNetworkInterface          | DescribeInstances               |
| CreateNetworkInterface          | DescribeNetworkInterfaces       |
| DeleteNetworkInterface          | DescribeSecurityGroups          |
| DeleteTags                      | DescribeTags                    |
| DetachNetworkInterface          | DescribeVpcs                    |
| ModifyNetworkInterfaceAttribute | DescribeVolumes                 |
| UnassignPrivateIpAddresses      |                     |





## 기타 알려진 제한

* Route 53 DNS 리졸버는 [초당 1024개의 패킷](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html#vpc-dns-limits)으로 제한됩니다. 대규모 클러스터의 DNS 트래픽이 소수의 CoreDNS 파드 복제본을 통해 유입되는 경우 이러한 제한이 발생할 수 있습니다. [CoreDNS 스케일링 및 DNS 동작 최적화](../cluster-services/#scale-coredns)를 사용하면 DNS 조회 시 타임아웃을 방지할 수 있습니다.
 * [또한 Route 53은 Route 53 API에 대해 초당 5개의 요청이라는 매우 낮은 속도 제한을 가지고 있습니다](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html#limits-api-requests).외부 DNS와 같은 프로젝트로 업데이트해야 할 도메인 수가 많은 경우 속도 제한이 발생하고 도메인 업데이트가 지연될 수 있습니다.

* 일부 [Nitro 인스턴스 유형에는 Amazon EBS 볼륨, 네트워크 인터페이스 및 NVMe 인스턴스 스토어 볼륨 간에 공유되는 볼륨 첨부 제한이 28개](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html#instance-type-volume-limits)로 제한됩니다. 워크로드가 많은 EBS 볼륨을 마운트하는 경우 이러한 인스턴스 유형으로 달성할 수 있는 파드 밀도에 제한이 발생할 수 있습니다.

* EC2 인스턴스당 추적할 수 있는 최대 연결 수가 있습니다. [워크로드에서 많은 수의 연결을 처리하는 경우 이 최대값에 도달했기 때문에 통신 실패 또는 오류가 발생할 수 있습니다.](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-connection-tracking.html#connection-tracking-throttling) `conntrack_allowance_available` 및 `conntrack_allowance_Exceeded` [네트워크 성능 지표](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-network-performance-ena.html)를 사용하여 EKS 워커 노드에서 추적되는 연결 수를 모니터링할 수 있습니다.


* EKS 환경에서 etcd 스토리지 제한은 [업스트림 지침](https://etcd.io/docs/v3.5/dev-guide/limit/#storage-size-limit)에 따라 **8GiB**입니다.etcd db 크기를 추적하려면 `etcd_db_total_size_in_bytes` 메트릭을 모니터링하십시오. 이 모니터링을 설정하려면 [경고 규칙](https://github.com/etcd-io/etcd/blob/main/contrib/mixin/mixin.libsonnet#L213-L240) `etcdBackendQuotaLowSpace` 및 `etcdExcessiveDatabaseGrowth`를 참조하십시오.
