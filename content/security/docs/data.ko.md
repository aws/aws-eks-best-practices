# 데이터 암호화 및 시크릿 관리

## 저장 시 암호화

쿠버네티스와 함께 사용할 수 있는 AWS 네이티브 스토리지 옵션은 [EBS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEBS.html), [EFS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEFS.html), [FSx for Lustre](https://docs.aws.amazon.com/fsx/latest/LustreGuide/what-is.html)등 세 가지가 있습니다. 세 가지 모두 서비스 관리 키 또는 고객 관리 키 (CMK)를 사용하여 저장 시 암호화를 제공합니다. EBS의 경우 인트리 스토리지 드라이버 또는 [EBS CSI드라이버](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)를 사용할 수 있습니다.둘 다 볼륨 암호화 및 CMK 제공을 위한 파라미터를 포함합니다. EFS의 경우 [EFS CSI 드라이버](https://github.com/kubernetes-sigs/aws-efs-csi-driver)를 사용할 수 있지만 EBS와 달리 EFS CSI 드라이버는 동적 프로비저닝을 지원하지 않습니다. EKS와 함께 EFS를 사용하려면 PV를 생성하기 전에 파일 시스템에 대한 저장 중 암호화를 프로비저닝하고 구성해야 합니다. EFS 파일 암호화에 대한 자세한 내용은 [저장 데이터 암호화](https://docs.aws.amazon.com/efs/latest/ug/encryption-at-rest.html)를 참조합니다. EFS와 FSx for Lustre에는 저장 시 암호화를 제공하는 것 외에도 전송 데이터를 암호화하는 옵션이 포함되어 있습니다. FSx for Luster는 기본적으로 이 작업을 수행합니다. EFS의 경우 다음 예와 같이 PV의 `MountOptions`에 `tls` 파라미터를 추가하여 전송 암호화를 추가할 수 있습니다:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: efs-pv
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: efs-sc
  mountOptions:
    - tls
  csi:
    driver: efs.csi.aws.com
    volumeHandle: <file_system_id>
```

[FSx CSI 드라이버](https://github.com/kubernetes-sigs/aws-fsx-csi-driver)는 Lustre 파일 시스템의 동적 프로비저닝을 지원합니다. 기본적으로 서비스 관리 키를 사용하여 데이터를 암호화하지만, 다음 예와 같이 자체 CMK를 제공하는 옵션이 있습니다:

```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: fsx-sc
provisioner: fsx.csi.aws.com
parameters:
  subnetId: subnet-056da83524edbe641
  securityGroupIds: sg-086f61ea73388fb6b
  deploymentType: PERSISTENT_1
  kmsKeyId: <kms_arn>
```

!!! attention
    2020년 5월 28일부터 EKS Fargate 파드의 임시 볼륨에 기록되는 모든 데이터는 업계 표준 AES-256 암호화 알고리즘을 사용하여 기본적으로 암호화됩니다. 서비스에서 암호화 및 복호화를 원활하게 처리하므로 애플리케이션을 수정할 필요가 없습니다.

### 저장된 데이터 암호화

저장된 데이터를 암호화하는 것은 모범 사례로 간주됩니다. 암호화가 필요한지 확실하지 않은 경우 데이터를 암호화하세요.

### CMK를 주기적으로 교체하세요

CMK를 자동으로 교체하도록 KMS를 구성합니다. 이렇게 하면 1년에 한 번 키가 교체되고 이전 키는 무기한 저장되므로 데이터를 계속 해독할 수 있습니다. 자세한 내용은 [고객 마스터 키 교체 문서](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)를 참조합니다.

### EFS 액세스 포인트를 사용하여 공유 데이터세트에 대한 액세스를 간소화합니다

서로 다른 POSIX 파일 권한으로 데이터 세트를 공유했거나 다른 마운트 지점을 생성하여 공유 파일 시스템의 일부에 대한 액세스를 제한하려는 경우 EFS 액세스 포인트를 사용하는 것이 좋습니다. 액세스 포인트 사용에 대한 자세한 내용은 [AWS 문서](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html)를 참조합니다. 현재 액세스 포인트(AP)를 사용하려면 PV의 `VolumeHandle` 파라미터에서 AP를 참조해야 합니다.

!!! attention
    2021년 3월 23일부터 EFS CSI 드라이버는 EFS 액세스 포인트의 동적 프로비저닝을 지원합니다. 액세스 포인트는 여러 파드 간에 파일 시스템을 쉽게 공유할 수 있게 해주는 EFS 파일 시스템의 애플리케이션 별 진입점입니다. 각 EFS 파일 시스템에는 최대 120개의 PV가 있을 수 있습니다. 자세한 내용은 [Amazon EFS CSI 동적 프로비저닝 소개](https://aws.amazon.com/blogs/containers/introducing-efs-csi-dynamic-provisioning/)를 참조하십시오.

## 시크릿 관리

쿠버네티스 시크릿은 사용자 인증서, 암호 또는 API 키와 같은 민감한 정보를 저장하는 데 사용됩니다. 이들은 etcd에 base64로 인코딩된 문자열로 유지됩니다. EKS에서는 etcd 노드의 EBS 볼륨이 [EBS 암호화](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html)로 암호화됩니다. 파드는 `PodSpec`의 시크릿을 참조하여 쿠버네티스 시크릿 객체를 검색할 수 있습니다. 이런 시크릿은 환경 변수에 매핑하거나 볼륨으로 마운트할 수 있습니다. 시크릿 생성에 대한 자세한 내용은 [쿠버네티스 문서](https://kubernetes.io/docs/concepts/configuration/secret/)를 참조하십시오.

!!! caution
    특정 네임스페이스의 시크릿은 네임스페이스의 모든 파드에서 참조할 수 있습니다.

!!! caution
    노드 권한 부여자는 Kubelet이 노드에 마운트된 모든 시크릿을 읽을 수 있도록 허용합니다.

### 쿠버네티스 시크릿 봉투 암호화에 AWS KMS 사용

이를 통해 고유한 DEK(데이터 암호화 키)으로 시크릿을 암호화할 수 있습니다. 그런 다음 DEK는 AWS KMS의 KEK (키 암호화 키) 를 사용하여 암호화되며, 이 KEK (키 암호화 키) 는 반복 일정에 따라 자동으로 교체될 수 있습니다. 쿠버네티스용 KMS 플러그인을 사용하면 모든 쿠버네티스 암호가 일반 텍스트 대신 암호문의 etcd에 저장되며 쿠버네티스 API 서버에서만 해독할 수 있습니다.
자세한 내용은 [심층 방어를 위한 EKS 암호화 공급자 지원 사용 블로그](https://aws.amazon.com/blogs/containers/using-eks-encryption-provider-support-for-defense-in-depth/)을 참조하십시오.

### 쿠버네티스 시크릿 사용 감사

EKS에서 감사 로깅을 켜고 CloudWatch 지표 필터 및 알람을 생성하여 시크릿이 사용될 때 알림을 보냅니다 (선택 사항). 다음은 쿠버네티스 감사 로그에 대한 메트릭 필터의 예시입니다, `{($.verb="get") && ($.ObjectRef.resource="Secret")}`. CloudWatch Log Insights에서는 다음 쿼리를 사용할 수도 있습니다:

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| stats count(*) by objectRef.name as secret
| filter verb="get" and objectRef.resource="secrets"
```

위 쿼리는 특정 기간 내에 시크릿에 액세스한 횟수를 표시합니다.

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter verb="get" and objectRef.resource="secrets"
| display objectRef.namespace, objectRef.name, user.username, responseStatus.code
```

이 쿼리에는 시크릿에 액세스하려고 시도한 사용자의 네임스페이스 및 사용자 이름 및 응답 코드와 함께 시크릿이 표시됩니다.

### 주기적으로 시크릿 교체하기

쿠버네티스는 시크릿을 자동으로 교체하지 않습니다. 암호를 교체해야 하는 경우 Vault 또는 AWS Secrets Manager와 같은 외부 암호 저장소를 사용하는 것이 좋습니다.

### 다른 애플리케이션으로부터 시크릿을 분리하는 방법으로 별도의 네임스페이스를 사용하십시오

네임스페이스의 애플리케이션 간에 공유할 수 없는 시크릿이 있는 경우 해당 애플리케이션에 대해 별도의 네임스페이스를 생성하십시오.

### 환경 변수 대신 볼륨 마운트 사용

환경 변수 값이 실수로 로그에 나타날 수 있습니다. 볼륨으로 마운트된 시크릿은 tmpfs 볼륨(RAM 백업 파일 시스템)으로 인스턴스화되며, 파드가 삭제되면 노드에서 자동으로 제거됩니다.

### 외부 시크릿 제공자 사용

[AWS Secret Manager](https://aws.amazon.com/secrets-manager/)와 Hishcorp의 [Vault](https://www.hashicorp.com/blog/injecting-vault-secrets-into-kubernetes-pods-via-a-sidecar/)를 포함하여 쿠버네티스 시크릿을 사용할 수 있는 몇 가지 실행 가능한 대안이 있습니다. 이런 서비스는 쿠버네티스 시크릿에서는 사용할 수 없는 세밀한 액세스 제어, 강력한 암호화, 암호 자동 교체 등의 기능을 제공합니다. Bitnami의 [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)는 비대칭 암호화를 사용하여 "봉인된 시크릿"을 생성하는 또 다른 접근 방식입니다. 공개 키는 시크릿을 암호화하는 데 사용되는 반면 암호 해독에 사용된 개인 키는 클러스터 내에 보관되므로 Git과 같은 소스 제어 시스템에 봉인된 시크릿을 안전하게 저장할 수 있습니다. 자세한 내용은 [실드 시크릿을 사용한 쿠버네티스의 시크릿 배포 관리](https://aws.amazon.com/blogs/opensource/managing-secrets-deployment-in-kubernetes-using-sealed-secrets/)를 참조합니다.

외부 시크릿 스토어의 사용이 증가함에 따라 이를 쿠버네티스와 통합해야 할 필요성도 커졌습니다. [Secret Store CSI 드라이버](https://github.com/kubernetes-sigs/secrets-store-csi-driver)는 CSI 드라이버 모델을 사용하여 외부 시크릿 스토어로부터 시크릿을 가져오는 커뮤니티 프로젝트입니다. 현재 이 드라이버는 [AWS Secret Manager](https://github.com/aws/secrets-store-csi-driver-provider-aws), Azure, Vault 및 GCP를 지원합니다. AWS 공급자는 AWS 시크릿 관리자**와** AWS 파라미터 스토어를 모두 지원합니다. 또한 암호가 만료되면 암호가 교체되도록 구성할 수 있으며, AWS Secrets Manager 암호를 쿠버네티스 암호와 동기화할 수 있습니다. 암호의 동기화는 볼륨에서 암호를 읽는 대신 암호를 환경 변수로 참조해야 할 때 유용할 수 있습니다.

!!! note
    시크릿 스토어 CSI 드라이버는 시크릿을 가져와야 하는 경우 시크릿을 참조하는 파드에 할당된 IRSA 역할을 사용합니다. 이 작업의 코드는 [Github](https://github.com/aws/secrets-store-csi-driver-provider-aws/blob/main/auth/auth.go)에서 찾을 수 있습니다.

AWS 보안 및 설정 공급자(ASCP) 에 대한 추가 정보는 다음 리소스를 참조하십시오:

- [쿠버네티스 시크릿 스토어 CSI 드라이버와 함께 AWS 보안 및 설정 공급자를 사용하는 방법](https://aws.amazon.com/blogs/security/how-to-use-aws-secrets-configuration-provider-with-kubernetes-secrets-store-csi-driver/)
- [Secret manager 시크릿을 쿠버네티스 시크릿 스토어 CSI 드라이버와 통합](https://docs.aws.amazon.com/secretsmanager/latest/userguide/integrating_csi_driver.html)

[external-secrets](https://github.com/external-secrets/kubernetes-external-secrets)는 쿠버네티스와 함께 외부 시크릿 저장소를 사용하는 또 다른 방법입니다. CSI 드라이버와 마찬가지로 외부 시크릿은 AWS Secrets Manager를 비롯한 다양한 백엔드에서 작동합니다. 차이점은 외부 시크릿이 외부 시크릿 스토어에서 시크릿을 검색하는 대신 이런 백엔드의 시크릿을 시크릿으로 Kubernetes에 복사한다는 점입니다. 이를 통해 선호하는 시크릿 스토어를 사용하여 시크릿을 관리하고 쿠버네티스 네이티브 방식으로 시크릿과 상호작용할 수 있다.
