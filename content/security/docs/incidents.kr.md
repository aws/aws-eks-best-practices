# 사고 대응 및 포렌식
사건에 신속하게 대응하는 능력은 위반으로 인한 피해를 최소화하는 데 도움이 될 수 있습니다. 의심스러운 행동을 경고할 수 있는 신뢰할 수 있는 경보 시스템을 갖추는 것이 좋은 사고 대응 계획의 첫 번째 단계입니다. 사고가 발생하면 영향을 받은 컨테이너를 폐기하고 교체할지 또는 컨테이너를 격리하고 검사할지 신속하게 결정해야 합니다. 포렌식 조사 및 근본 원인 분석의 일부로 컨테이너를 격리하기로 선택한 경우 다음 활동 집합을 따라야 합니다.

## 샘플 사고 대응 계획

### 문제가 되는 포드 및 작업자 노드 식별
첫 번째 조치는 손상을 격리하는 것입니다. 위반이 발생한 위치를 식별하는 것부터 시작하여 나머지 인프라에서 해당 Pod와 해당 노드를 격리합니다.

### 워크로드 이름을 사용하여 문제가 되는 Pod 및 작업자 노드 식별

잘못된 팟(Pod)의 이름과 네임스페이스를 알고 있는 경우 다음과 같이 팟(Pod)을 실행하는 작업자 노드를 식별할 수 있습니다.
```
kubectl get pods <이름> --namespace <이름 공간> -o=jsonpath='{.spec.nodeName}{"\n"}'
```
배포와 같은 워크로드 리소스(https://kubernetes.io/docs/concepts/workloads/controllers/)가 손상된 경우 워크로드 리소스의 일부인 모든 포드가 손상되었을 가능성이 있습니다. 다음 명령을 사용하여 워크로드 리소스의 모든 포드와 실행 중인 노드를 나열합니다.
```
selector=$(kubectl get deployments <이름> \
--네임스페이스 <네임스페이스> -o json | jq -j \
'.spec.selector.matchLabels | to_entries | .[] | "\(.키)=\(.값)"')

kubectl get pods --namespace <네임스페이스> --selector=$selector \
-o json | jq -r '.항목[] | "\(.metadata.name) \(.spec.nodeName)"'
```
위의 명령은 배포용입니다. replicasets, statefulsets 등과 같은 다른 워크로드 리소스에 대해 동일한 명령을 실행할 수 있습니다.

### 서비스 계정 이름을 사용하여 문제가 되는 Pod 및 작업자 노드 식별

경우에 따라 서비스 계정이 손상되었음을 확인할 수 있습니다. 식별된 서비스 계정을 사용하는 포드가 손상되었을 가능성이 있습니다. 다음 명령으로 실행 중인 서비스 계정 및 노드를 사용하여 모든 포드를 식별할 수 있습니다.
```
kubectl get pods -o json --namespace <네임스페이스> | \
jq -r '.항목[] |
select(.spec.serviceAccount == "<서비스 계정 이름>") |
"\(.metadata.name) \(.spec.nodeName)"'
```

### 취약하거나 손상된 이미지 및 작업자 노드가 있는 Pod 식별
경우에 따라 클러스터의 팟(Pod)에서 사용 중인 컨테이너 이미지가 악의적이거나 손상되었음을 발견할 수 있습니다. 컨테이너 이미지는 악의적이거나 손상된 것입니다. 맬웨어를 포함하는 것으로 확인되거나 알려진 불량 이미지이거나 악용된 CVE가 있는 경우입니다. 손상된 컨테이너 이미지를 사용하는 모든 포드를 고려해야 합니다. 다음 명령으로 실행 중인 이미지와 노드를 사용하여 포드를 식별할 수 있습니다.
```
IMAGE=<악성/손상된 이미지의 이름>

kubectl get pods -o json --all-namespaces | \
jq -r --arg 이미지 "$IMAGE" '.items[] |
select(.spec.containers[] | .image == $image) |
"\(.metadata.name) \(.metadata.namespace) \(.spec.nodeName)"'
```

### 포드에 대한 모든 인그레스 및 이그레스 트래픽을 거부하는 네트워크 정책을 생성하여 포드를 격리합니다.
모든 트래픽 거부 규칙은 포드에 대한 모든 연결을 끊음으로써 이미 진행 중인 공격을 중지하는 데 도움이 될 수 있습니다. 다음 네트워크 정책은 `app=web` 레이블이 있는 포드에 적용됩니다 .
```yaml
apiVersion : networking.k8s.io/v1
종류 : NetworkPolicy
메타데이터 :
  이름 : 기본 거부
사양 :
  포드 선택기 :
    일치 라벨 :
      앱 : 웹
  정책 유형 :
- 인 그레스
- 이그레스
```

!!! 주목
네트워크 정책은 공격자가 기본 호스트에 대한 액세스 권한을 얻은 경우 효과가 없는 것으로 판명될 수 있습니다. 이러한 일이 발생한 것으로 의심되는 경우 [ AWS 보안 그룹 ]( https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html )을 사용하여 손상된 호스트를 다른 호스트에서 격리할 수 있습니다. 호스트의 보안 그룹을 변경할 때 해당 호스트에서 실행 중인 모든 컨테이너에 영향을 미친다는 점에 유의하십시오.

### 필요한 경우 포드 또는 작업자 노드에 할당된 임시 보안 자격 증명 취소
작업자 노드에 포드가 다른 AWS 리소스에 액세스할 수 있도록 허용하는 IAM 역할이 할당된 경우 인스턴스에서 해당 역할을 제거하여 공격으로 인한 추가 손상을 방지합니다. 마찬가지로 포드에 IAM 역할이 할당된 경우 다른 워크로드에 영향을 주지 않고 역할에서 IAM 정책을 안전하게 제거할 수 있는지 평가합니다.

### 작업자 노드 차단
영향을 받는 작업자 노드를 차단하면 영향을 받는 노드에 Pod를 예약하지 않도록 스케줄러에 알립니다. 이렇게 하면 다른 워크로드를 방해하지 않고 포렌식 연구를 위해 노드를 제거할 수 있습니다.

!!! 정보
이 지침은 각 Fargate 포드가 자체 샌드박스 환경에서 실행되는 Fargate에는 적용되지 않습니다. 차단하는 대신 모든 수신 및 송신 트래픽을 거부하는 네트워크 정책을 적용하여 영향을 받는 Fargate 포드를 격리합니다.

### 영향을 받는 작업자 노드에서 종료 보호 활성화
공격자는 영향을 받는 노드를 종료하여 악행을 지우려고 시도할 수 있습니다. [ 종료 방지 기능 ]( https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html#Using_ChangingDisableAPITermination )을 활성화 하면 이러한 상황이 발생하지 않도록 방지할 수 있습니다. [ 인스턴스 축소 보호 ]( https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-instance-termination.html#instance-protection )는 축소 이벤트로부터 노드를 보호합니다.

!!! 경고
스팟 인스턴스에서는 종료 방지 기능을 활성화할 수 없습니다.

### 문제가 되는 포드/노드에 활성 조사의 일부임을 나타내는 레이블을 지정합니다.
이는 조사가 완료될 때까지 영향을 받는 포드/노드를 변조하지 않도록 클러스터 관리자에게 경고하는 역할을 합니다.

### 작업자 노드에서 휘발성 아티팩트 캡처
+ **운영 체제 메모리 캡처** . 그러면 Docker 데몬과 컨테이너당 하위 프로세스가 캡처됩니다. 원격 메모리 획득 도구인 [ MargaritaShotgun ]( https://github.com/ThreatResponse/margaritashotgun )이 이러한 노력을 도울 수 있습니다.
+ **실행 중인 프로세스와 열린 포트의 netstat 트리 덤프를 수행합니다** . 이렇게 하면 도커 데몬과 컨테이너당 하위 프로세스가 캡처됩니다.
+ **작업자 노드에서 증거가 변경되기 전에 docker 명령 실행** .
    + 실행 중인 프로세스를 위한 `docker container top CONTAINER` .
    + 데몬 수준 보유 로그에 대한 `docker 컨테이너 로그 CONTAINER` .
    + 열린 포트 목록에 대한 '도커 컨테이너 포트 CONTAINER' .
    + `docker container diff CONTAINER` 는 초기 실행 이후 컨테이너의 파일 시스템에 대한 파일 및 디렉토리의 변경 사항을 캡처합니다.
+ **포렌식 캡처를 위해 컨테이너를 일시중지합니다** .
+ **인스턴스의 EBS 볼륨 스냅샷** .

### 손상된 포드 또는 워크로드 리소스 재배포

포렌식 분석을 위한 데이터를 수집한 후에는 손상된 포드 또는 워크로드 리소스를 재배포할 수 있습니다.

먼저 손상된 취약성에 대한 수정 사항을 롤아웃하고 새 교체 포드를 시작합니다. 그런 다음 취약한 포드를 삭제합니다.

취약한 포드가 더 높은 수준의 Kubernetes 워크로드 리소스(예: 배포 또는 DaemonSet)에 의해 관리되는 경우 이를 삭제하면 새 포드가 예약됩니다. 따라서 취약한 포드가 다시 시작됩니다. 이 경우 취약성을 수정한 후 새 대체 워크로드 리소스를 배포해야 합니다. 그런 다음 취약한 워크로드를 삭제해야 합니다.

## 추천

### AWS 보안 사고 대응 백서 검토
AWS 보안 사고 대응 ]( https://d1.awsstatic.com/whitepapers/aws_security_incident_response.pdf 백서에서 철저하게 다룹니다. ).

### 보안 게임 연습 날
보안 실무자를 빨간색과 파란색의 두 팀으로 나눕니다. 레드 팀은 서로 다른 시스템의 취약점을 조사하는 데 집중하고 블루 팀은 시스템 방어를 담당합니다. 별도의 팀을 만들 보안 실무자가 충분하지 않은 경우 Kubernetes 익스플로잇에 대한 지식이 있는 외부 엔터티를 고용하는 것이 좋습니다.

[ Kubesploit ]( https://github.com/cyberark/kubesploit )는 CyberArk의 침투 테스트 프레임워크로 게임 데이를 수행하는 데 사용할 수 있습니다. 클러스터의 취약점을 스캔하는 다른 도구와 달리 kubesploit은 실제 공격을 시뮬레이션합니다. 이를 통해 블루 팀은 공격에 대한 대응을 연습하고 그 효과를 측정할 수 있습니다.

### 클러스터에 대한 침투 테스트 실행
자신의 클러스터를 주기적으로 공격하면 취약성과 잘못된 구성을 발견하는 데 도움이 될 수 있습니다. 시작하기 전에 클러스터에 대한 테스트를 수행하기 전에 [ 침투 테스트 지침 ]( https://aws.amazon.com/security/penetration-testing/ )을 따르십시오.

## 도구
+ [ kube-hunter ]( https://github.com/aquasecurity/kube-hunter ), Kubernetes용 침투 테스트 도구.
+ [ Gremlin ]( https://www.gremlin.com/product/#kubernetes ), 애플리케이션 및 인프라에 대한 공격을 시뮬레이션하는 데 사용할 수 있는 카오스 엔지니어링 툴킷.
+ [ kube-forensics ]( https://github.com/keikoproj/kube-forensics ), 실행 중인 포드의 상태를 수집하고 S3 버킷에 덤프하는 작업을 트리거하는 Kubernetes 컨트롤러.
+ [ Kubernetes 설치 공격 및 방어 ]( https://github.com/kubernetes/sig-security/blob/main/sig-security-external-audit/security-audit-2019/findings/AtredisPartners_Attacking_Kubernetes-v1.0.pdf )
+ [ kubesploit ]( https://www.cyberark.com/resources/threat-research-blog/kubesploit-a-new-offensive-tool-for-testing-containerized-environments )

## 동영상
+ [ 지능형 지속적 위협 ]( https://www.youtube.com/watch?v=CH7S5rE3j8w )
+ [ Kubernetes 실용 공격 및 방어 ]( https://www.youtube.com/watch?v=LtCx3zZpOfs )
+ [ RBAC 권한을 악용하여 Kubernetes 클러스터 손상 ]( https://www.youtube.com/watch?v=1LMo0CftVC4 )


