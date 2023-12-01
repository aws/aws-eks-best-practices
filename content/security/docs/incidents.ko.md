# 사고 대응 및 포렌식
사고에 신속하게 대응할 수 있으면 침해로 인한 피해를 최소화하는 데 도움이 될 수 있습니다. 의심스러운 행동을 경고할 수 있는 신뢰할 수 있는 경고 시스템을 갖추는 것이 올바른 사고 대응 계획의 첫 번째 단계입니다. 사고가 발생하면 영향을 받는 컨테이너를 폐기하여 교체할지 아니면 컨테이너를 격리하고 검사할지 신속하게 결정해야 합니다. 포렌식 조사 및 근본 원인 분석의 일환으로 컨테이너를 격리하기로 선택한 경우 다음과 같은 일련의 활동을 따라야 합니다.

## 사고 대응 계획 예

### 문제가 되는 파드와 워커 노드 식별
첫 번째 조치는 침해를 격리하는 것입니다. 먼저 침해가 발생한 위치를 파악하고 해당 파드와 해당 노드를 인프라의 나머지 부분으로부터 격리합니다.

### 워크로드 이름을 사용하여 문제가 되는 파드와 워커 노드를 식별

문제가 되는 파드의 이름과 네임스페이스를 알면 다음과 같이 파드를 실행하는 워커 노드를 식별할 수 있습니다.
```
kubectl get pods <name> --namespace <namespace> -o=jsonpath='{.spec.nodeName}{"\n"}'   
```
디플로이먼트와 같은 [워크로드 리소스](https://kubernetes.io/docs/concepts/workloads/controllers/)가 손상된 경우, 워크로드 리소스의 일부인 모든 파드가 손상될 가능성이 있다. 다음 명령어를 사용하여 워크로드 리소스의 모든 파드와 해당 파드가 실행 중인 노드를 나열하세요.
```
selector=$(kubectl get deployments <name> \
 --namespace <namespace> -o json | jq -j \
'.spec.selector.matchLabels | to_entries | .[] | "\(.key)=\(.value)"')

kubectl get pods --namespace <namespace> --selector=$selector \
-o json | jq -r '.items[] | "\(.metadata.name) \(.spec.nodeName)"'
```
위는 디플로이먼트를 위한 명령입니다. 레플리카셋, 스테이트풀셋 등과 같은 다른 워크로드 리소스에 대해서도 동일한 명령을 실행할 수 있습니다. 

### 서비스 어카운트 이름을 사용하여 문제가 되는 파드와 워커 노드를 식별

경우에 따라 서비스 어카운트가 손상된 것으로 확인될 수 있습니다. 식별된 서비스 어카운트를 사용하는 파드가 손상될 가능성이 있습니다. 다음 명령어를 사용하여 서비스 어카운트 및 실행 중인 노드를 사용하여 모든 파드를 식별할 수 있습니다.
```
kubectl get pods -o json --namespace <namespace> | \
    jq -r '.items[] |
    select(.spec.serviceAccount == "<service account name>") |
    "\(.metadata.name) \(.spec.nodeName)"'
```

### 취약하거나 손상된 이미지와 워커 노드가 있는 파드를 식별
경우에 따라 클러스터의 파드에서 사용 중인 컨테이너 이미지가 악의적이거나 손상된 것을 발견할 수 있습니다. 컨테이너 이미지는 악의적이거나 손상된 것입니다. 멀웨어가 포함되어 있는 것으로 밝혀진 경우, 알려진 잘못된 이미지 또는 악용된 CVE가 있는 경우입니다. 컨테이너 이미지를 사용하는 모든 파드가 손상된 것으로 간주해야 합니다. 다음 명령어로 파드가 실행 중인 이미지와 노드를 사용하여 파드를 식별할 수 있다.
```
IMAGE=<Name of the malicious/compromised image>

kubectl get pods -o json --all-namespaces | \
    jq -r --arg image "$IMAGE" '.items[] | 
    select(.spec.containers[] | .image == $image) | 
    "\(.metadata.name) \(.metadata.namespace) \(.spec.nodeName)"'
```

### 파드에 대한 모든 수신 및 송신 트래픽을 거부하는 네트워크 정책을 생성하여 파드를 격리
모든 트래픽 거부 규칙은 파드에 대한 모든 연결을 끊어 이미 진행 중인 공격을 중지하는 데 도움이 될 수 있습니다.다음 네트워크 정책은 레이블이 `app=web`인 파드에 적용됩니다. 
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector:
    matchLabels: 
      app: web
  policyTypes:
  - Ingress
  - Egress
```

!!! attention
    공격자가 기본 호스트에 대한 액세스 권한을 획득한 경우 네트워크 정책이 효과가 없는 것으로 판명될 수 있습니다. 그런 일이 발생했다고 의심되는 경우 [AWS 보안 그룹](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)을 사용하여 손상된 호스트를 다른 호스트로부터 격리할 수 있습니다.호스트의 보안 그룹을 변경할 때는 해당 호스트에서 실행 중인 모든 컨테이너에 영향을 미치므로 주의하십시오.  

### 필요한 경우 파드 또는 워커 노드에 할당된 임시 보안 자격 증명을 취소
워커 노드에 파드가 다른 AWS 리소스에 액세스할 수 있도록 허용하는 IAM 역할을 할당받은 경우, 공격으로 인한 추가 피해를 방지하기 위해 인스턴스에서 해당 역할을 제거해야 합니다. 마찬가지로, 파드에 IAM 역할이 할당된 경우, 다른 워크로드에 영향을 주지 않으면서 역할에서 IAM 정책을 안전하게 제거할 수 있는지 평가해 보세요.

### 워커 노드 차단(cordon)
영향을 받는 워커 노드를 차단함으로써 영향을 받는 노드에 파드를 스케줄링하지 않도록 스케줄러에 알리는 것입니다.이렇게 하면 다른 워크로드에 영향을 주지 않으면서 포렌식 연구를 위해 노드를 제거할 수 있습니다.

!!! info
    이 지침은 각 Fargate 파드가 자체 샌드박스 환경에서 실행되는 Fargate에는 적용되지 않습니다. 차단하는 대신 모든 수신 및 송신 트래픽을 거부하는 네트워크 정책을 적용하여 영향을 받는 Fargate 파드를 격리하십시오. 

### 영향을 받는 워커 노드에서 종료 보호 활성화
공격자는 영향을 받은 노드를 종료하여 자신의 흔적을 지우려고 시도할 수 있습니다. [종료 방지 기능](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html#Using_ChangingDisableAPITermination)을 활성화하면 이런 일이 발생하지 않도록 할 수 있습니다. [인스턴스 스케일-인 보호](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-instance-termination.html#instance-protection)는 스케일-인 이벤트로부터 노드를 보호합니다. 

!!! warning
    스팟 인스턴스에서는 종료 방지 기능을 활성화할 수 없습니다.

### 문제가 되는 파드/노드에 현재 조사 중임을 나타내는 레이블을 지정
이는 조사가 완료될 때까지 클러스터 관리자에게 영향을 받는 파드/노드를 변경하지 말라는 경고 역할을 합니다. 

### 워커 노드에서 휘발성 아티팩트 캡처
+ **운영 체제 메모리 캡처**. 이는 도커 데몬(또는 다른 컨테이너 런타임)과 컨테이너별 하위 프로세스의 메모리를 캡처합니다. 이는 [LiME](https://github.com/504ensicsLabs/LiME) 및 [Volatility](https://www.volatilityfoundation.org/)와 같은 도구를 사용하거나, 이를 기반으로 구축되는 [Amazon EC2용 자동 포렌식 오케스트레이터](https://aws.amazon.com/solutions/implementations/automated-forensics-orchestrator-for-amazon-ec2/)와 같은 상위 수준 도구를 사용하여 수행할 수 있습니다.
+ **실행 중인 프로세스와 열린 포트의 netstat 트리 덤프를 수행**. 이는 컨테이너별로 도커 데몬과 해당 하위 프로세스가 캡처됩니다. 
+ **상태가 변경되기 전에 컨테이너 레벨의 상태를 저장하는 명령을 실행** 컨테이너 런타임의 기능을 사용하여 현재 실행 중인 컨테이너에 대한 정보를 캡처할 수 있습니다. 예를 들어 Docker를 사용하면 다음과 같은 작업을 수행할 수 있습니다.
    + `docker top CONTAINER` : 실행 중인 프로세스를 확인
    + `docker logs CONTAINER` : 데몬 레벨 로그 확인 
    + `docker inspect CONTAINER` : 컨테이너의 다양한 정보 확인
    
    컨테이너에서 '도커' 대신 [nerdctl](https://github.com/containerd/nerdctl) CLI를 사용하면 동일한 결과를 얻을 수 있다 (예: `nerdctl inspect`). 컨테이너 런타임에 따라 몇 가지 추가 명령을 사용할 수 있습니다. 예를 들어 도커에는 컨테이너 파일 시스템의 변경 사항을 확인하기 위한 `docker diff`와 휘발성 메모리(RAM)를 포함한 모든 컨테이너 상태를 저장하는 `docker checkpoint`가 있습니다. 컨테이너드 또는 CRI-O 런타임의 유사한 기능에 대한 설명은 [이 쿠버네티스 블로그 게시물](https://kubernetes.io/blog/2022/12/05/forensic-container-checkpointing-alpha/)을 참조합니다.

+ **포렌식 캡처를 위해 컨테이너를 일시 중지**.
+ **인스턴스의 EBS 볼륨 스냅샷을 생성**.

### 손상된 파드 또는 워크로드 리소스 재배포

포렌식 분석을 위해 데이터를 수집한 후에는 손상된 파드 또는 워크로드 리소스를 재배포할 수 있습니다.

먼저 손상된 취약점에 대한 수정 사항을 배포하고 새 대체 파드를 시작합니다. 그리고 취약한 파드를 삭제합니다.

취약한 파드를 상위 수준의 쿠버네티스 워크로드 리소스(예: 디플로이먼트 또는 데몬셋) 에서 관리하는 경우, 이를 삭제하면 새 파드가 스케줄링된다. 따라서 취약한 파드가 다시 실행될 것입니다. 이 경우 취약성을 수정한 후 새로운 대체 워크로드 리소스를 배포해야 합니다. 그런 다음 취약한 워크로드를 삭제해야 합니다.

## 권장 사항

### AWS 보안 사고 대응 백서 검토
이 섹션에서는 의심되는 보안 침해를 처리하기 위한 몇 가지 권장 사항과 함께 간략한 개요를 제공하지만, 이 주제는 [AWS 보안 사고 대응 백서](https://d1.awsstatic.com/whitepapers/aws_security_incident_response.pdf)에서 자세히 다룹니다.

### 보안 게임 데이를 통한 대응 준비
보안 실무자를 레드팀과 블루팀, 두 팀으로 나눕니다. 레드 팀은 여러 시스템의 취약점을 조사하는 데 집중하고 파란색 팀은 취약점을 방어하는 데 집중합니다. 별도의 팀을 만들 수 있는 보안 실무자가 충분하지 않은 경우 쿠버네티스 악용에 대한 지식이 있는 외부 법인을 고용하는 것을 고려해 보십시오. 

[Kubesploit](https://github.com/cyberark/kubesploit)는 CyberArk의 침투 테스트 프레임워크로, 게임 데이를 진행하는 데 사용할 수 있습니다. 클러스터에서 취약점을 검사하는 다른 도구와 달리 kubesploit는 실제 공격을 시뮬레이션합니다. 이를 통해 블루 팀은 공격에 대한 대응을 연습하고 그 효과를 측정할 수 있습니다.

### 클러스터에 대한 침투 테스트 실행
자신의 클러스터를 주기적으로 공격하면 취약성과 구성 오류를 발견하는 데 도움이 될 수 있습니다. 시작하기 전에 클러스터를 대상으로 테스트를 수행하기 전에 [침투 테스트 지침](https://aws.amazon.com/security/penetration-testing/)을 따르십시오. 

## 도구
+ [kube-hunter](https://github.com/aquasecurity/kube-hunter), 쿠버네티스를 위한 침투 테스트 도구
+ [Gremlin](https://www.gremlin.com/product/#kubernetes), 애플리케이션 및 인프라에 대한 공격을 시뮬레이션하는 데 사용할 수 있는 카오스 엔지니어링 툴킷
+ [Attacking and Defending Kubernetes Installations](https://github.com/kubernetes/sig-security/blob/main/sig-security-external-audit/security-audit-2019/findings/AtredisPartners_Attacking_Kubernetes-v1.0.pdf)
+ [kubesploit](https://www.cyberark.com/resources/threat-research-blog/kubesploit-a-new-offensive-tool-for-testing-containerized-environments)

## 동영상 자료
+ [지능적이고 지속적인 위협](https://www.youtube.com/watch?v=CH7S5rE3j8w)
+ [쿠버네티스 실무 공격 및 방어](https://www.youtube.com/watch?v=LtCx3zZpOfs)
+ [RBAC 권한을 악용하여 쿠버네티스 클러스터 손상](https://www.youtube.com/watch?v=1LMo0CftVC4)

