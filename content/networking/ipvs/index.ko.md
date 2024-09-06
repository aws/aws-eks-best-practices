# IPVS 모드에서 kube-proxy 실행

IPVS (IP 가상 서버) 모드의 EKS는 레거시 iptables 모드에서 실행되는 `kube-proxy`와 함께 1,000개 이상의 서비스가 포함된 대규모 클러스터를 실행할 때 흔히 발생하는 [네트워크 지연 문제](https://aws.github.io/aws-eks-best-practices/reliability/docs/controlplane/#running-large-clusters)를 해결합니다.이러한 성능 문제는 각 패킷에 대한 iptables 패킷 필터링 규칙을 순차적으로 처리한 결과입니다.이 지연 문제는 iptables의 후속 버전인 nftables에서 해결되었습니다.하지만 이 글을 쓰는 시점 현재, nftable을 활용하기 위한 [kube-proxy는 아직 개발 중] (https://kubernetes.io/docs/reference/networking/virtual-ips/#proxy-mode-nftables) 이다.이 문제를 해결하려면 IPVS 모드에서 `kube-proxy`가 실행되도록 클러스터를 구성할 수 있다.

## 개요

[쿠버네티스 버전 1.11](https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/) 부터 GA가 된 IPVS는 선형 검색이 아닌 해시 테이블을 사용하여 패킷을 처리하므로 수천 개의 노드와 서비스가 있는 클러스터에 효율성을 제공합니다.IPVS는 로드 밸런싱을 위해 설계되었으므로 쿠버네티스 네트워킹 성능 문제에 적합한 솔루션입니다.

IPVS는 트래픽을 백엔드 포드에 분산하기 위한 몇 가지 옵션을 제공합니다.각 옵션에 대한 자세한 내용은 [공식 쿠버네티스 문서](https://kubernetes.io/docs/reference/networking/virtual-ips/#proxy-mode-ipvs) 에서 확인할 수 있지만, 간단한 목록은 아래에 나와 있다.라운드 로빈과 최소 연결은 쿠버네티스의 IPVS 로드 밸런싱 옵션으로 가장 많이 사용되는 옵션 중 하나입니다.
```
- rr (라운드 로빈)
- wrr (웨이티드 라운드 로빈)
- lc (최소 연결)
- wlc (가중치가 가장 적은 연결)
- lblc (지역성 기반 최소 연결)
- lblcr (복제를 통한 지역성 기반 최소 연결)
- sh (소스 해싱)
- dh (데스티네이션 해싱)
- sed (최단 예상 지연)
- nq (줄 서지 마세요)
```

### 구현

EKS 클러스터에서 IPVS를 활성화하려면 몇 단계만 거치면 됩니다.가장 먼저 해야 할 일은 EKS 작업자 노드 이미지에 Linux 가상 서버 관리 `ipvsadm` 패키지가 설치되어 있는지 확인하는 것입니다.Amazon Linux 2023과 같은 Fedora 기반 이미지에 이 패키지를 설치하려면 작업자 노드 인스턴스에서 다음 명령을 실행할 수 있습니다.
```bash
sudo dnf install -y ipvsadm
```
Ubuntu와 같은 데비안 기반 이미지에서는 설치 명령이 다음과 같습니다.
```bash
sudo apt-get install ipvsadm
```

다음으로 위에 나열된 IPVS 구성 옵션에 대한 커널 모듈을 로드해야 합니다.재부팅해도 계속 작동하도록 이러한 모듈을 `/etc/modules-load.d/` 디렉토리 내의 파일에 기록하는 것이 좋습니다.
```bash
sudo sh -c 'cat << EOF > /etc/modules-load.d/ipvs.conf
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_lc
ip_vs_wlc
ip_vs_lblc
ip_vs_lblcr
ip_vs_sh
ip_vs_dh
ip_vs_sed
ip_vs_nq
nf_conntrack
EOF'
```
다음 명령을 실행하여 이미 실행 중인 시스템에서 이러한 모듈을 로드할 수 있습니다.
```bash
sudo modprobe ip_vs 
sudo modprobe ip_vs_rr
sudo modprobe ip_vs_wrr
sudo modprobe ip_vs_lc
sudo modprobe ip_vs_wlc
sudo modprobe ip_vs_lblc
sudo modprobe ip_vs_lblcr
sudo modprobe ip_vs_sh
sudo modprobe ip_vs_dh
sudo modprobe ip_vs_sed
sudo modprobe ip_vs_nq
sudo modprobe nf_conntrack
```
!!! note
    이러한 작업자 노드 단계는 [사용자 데이터 스크립트](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) 를 통해 작업자 노드의 부트스트랩 프로세스의 일부로 실행하거나 사용자 지정 작업자 노드 AMI를 빌드하기 위해 실행되는 빌드 스크립트에서 실행하는 것이 좋습니다.

다음으로 IPVS 모드에서 실행되도록 클러스터의 `kube-proxy` DaemonSet를 구성합니다. 이는 `kube-proxy` `mode`를 `ipvs`로 설정하고 `ipvs scheduler`를 위에 나열된 로드 밸런싱 옵션 중 하나로 설정하면 됩니다(예: 라운드 로빈의 경우 `rr`).
!!! Warning
    이는 운영 중단을 야기하는 변경이므로 근무 시간 외 시간에 수행해야 합니다.영향을 최소화하려면 초기 EKS 클러스터 생성 중에 이러한 변경을 수행하는 것이 좋습니다.

`kube-proxy` EKS 애드온을 업데이트하여 AWS CLI 명령을 실행하여 IPVS를 활성화할 수 있습니다.
```bash
aws eks update-addon --cluster-name $CLUSTER_NAME --addon-name kube-proxy \
  --configuration-values '{"ipvs": {"scheduler": "rr"}, "mode": "ipvs"}' \
  --resolve-conflicts OVERWRITE
```
또는 클러스터에서 `kube-proxy-config` 컨피그맵을 수정하여 이 작업을 수행할 수 있습니다.
```bash
kubectl -n kube-system edit cm kube-proxy-config
```
`ipvs`에서 `scheduler` 설정을 찾아 값을 위에 나열된 IPVS 로드 밸런싱 옵션 중 하나로 설정합니다(예: 라운드 로빈의 경우 `rr`)
기본값이 `iptables`인 `mode` 설정을 찾아 값을 `ipvs`로 변경합니다.
두 옵션 중 하나의 결과는 아래 구성과 유사해야 합니다.
```yaml hl_lines="9 13"
  iptables:
    masqueradeAll: false
    masqueradeBit: 14
    minSyncPeriod: 0s
    syncPeriod: 30s
  ipvs:
    excludeCIDRs: null
    minSyncPeriod: 0s
    scheduler: "rr"
    syncPeriod: 30s
  kind: KubeProxyConfiguration
  metricsBindAddress: 0.0.0.0:10249
  mode: "ipvs"
  nodePortAddresses: null
  oomScoreAdj: -998
  portRange: ""
  udpIdleTimeout: 250ms
```

이러한 변경을 수행하기 전에 작업자 노드가 클러스터에 연결된 경우 kube-proxy 데몬셋을 다시 시작해야 합니다.
```bash
kubectl -n kube-system rollout restart ds kube-proxy
```

### 유효성 검사

작업자 노드 중 하나에서 다음 명령을 실행하여 클러스터 및 작업자 노드가 IPVS 모드에서 실행되고 있는지 확인할 수 있습니다.
```bash
sudo ipvsadm -L
```

최소한 쿠버네티스 클러스터 IP 서비스의 항목이 `10.100.0.1`이고 codedns 서비스에 대한 항목이 `10.100.0.10`인 아래와 비슷한 결과를 볼 수 있을 것이다.
```hl_lines="4 7 10"
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
TCP  ip-10-100-0-1.us-east-1. rr
  -> ip-192-168-113-81.us-eas Masq        1      0          0
  -> ip-192-168-162-166.us-ea Masq        1      1          0
TCP  ip-10-100-0-10.us-east-1 rr
  -> ip-192-168-104-215.us-ea Masq        1      0          0
  -> ip-192-168-123-227.us-ea Masq        1      0          0
UDP  ip-10-100-0-10.us-east-1 rr
  -> ip-192-168-104-215.us-ea Masq        1      0          0
  -> ip-192-168-123-227.us-ea Masq        1      0          0
```