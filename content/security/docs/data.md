# Data encryption and secrets management

## Encryption at rest
There are three different AWS-native storage options you can use with Kubernetes: [EBS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEBS.html), [EFS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEFS.html), and [FSx for Lustre](https://docs.aws.amazon.com/fsx/latest/LustreGuide/what-is.html).  All three offer encryption at rest using a service managed key or a customer master key (CMK). For EBS you can use the in-tree storage driver or the [EBS CSI driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver).  Both include parameters for encrypting volumes and supplying a CMK.  For EFS, you can use the [EFS CSI driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver), however, unlike EBS, the EFS CSI driver does not support dynamic provisioning.  If you want to use EFS with EKS, you will need to provision and configure at-rest encryption for the file system prior to creating a PV. For further information about EFS file encryption, please refer to [Encrypting Data at Rest](https://docs.aws.amazon.com/efs/latest/ug/encryption-at-rest.html). Besides offering at-rest encryption, EFS and FSx for Lustre include an option for encrypting data in transit.  FSx for Luster does this by default.  For EFS, you can add transport encryption by adding the `tls` parameter to `mountOptions` in your PV as in this example: 

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

The [FSx CSI driver](https://github.com/kubernetes-sigs/aws-fsx-csi-driver) supports dynamic provisioning of Lustre file systems.  It encrypts data with a service managed key by default, although there is an option to provide you own CMK as in this example:

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
    As of May 28, 2020 all data written to the ephemeral volume in EKS Fargate pods is encrypted by default using an industry-standard AES-256 cryptographic algorithm. No modifications to your application are necessary as encryption and decryption are handled seamlessly by the service. 

## Recommendations
### Encrypt data at rest
Encrypting data at rest is considered a best practice.  If you're unsure whether encryption is necessary, encrypt your data. 

### Rotate your CMKs periodically
Configure KMS to automatically rotate you CMKs.  This will rotate your keys once a year while saving old keys indefinitely so that your data can still be decrypted.  For additional information see [Rotating customer master keys](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)

### Use EFS access points to simplify access to shared datasets
If you have shared datasets with different POSIX file permissions or want to restrict access to part of the shared file system by creating different mount points, consider using EFS access points. To learn more about working with access points, see [https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html). Today, if you want to use an access point (AP) you'll need to reference the AP in the PV's `volumeHandle` parameter.

!!! attention
    As of March 23, 2021 the EFS CSI driver supports dynamic provisioning of EFS Access Points. Access points are application-specific entry points into an EFS file system that make it easier to share a file system between multiple pods. Each EFS file system can have up to 120 PVs. See [Introducing Amazon EFS CSI dynamic provisioning](https://aws.amazon.com/blogs/containers/introducing-efs-csi-dynamic-provisioning/) for additional information. 

## Secrets management
Kubernetes secrets are used to store sensitive information, such as user certificates, passwords, or API keys. They are persisted in etcd as base64 encoded strings.  On EKS, the EBS volumes for etcd nodes are encrypted with [EBS encryption](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html).  A pod can retrieve a Kubernetes secrets objects by referencing the secret in the `podSpec`.  These secrets can either be mapped to an environment variable or mounted as volume. For additional information on creating secrets, see [https://kubernetes.io/docs/concepts/configuration/secret/](https://kubernetes.io/docs/concepts/configuration/secret/). 

!!! caution
    Secrets in a particular namespace can be referenced by all pods in the secret's namespace.

!!! caution 
    The node authorizer allows the Kubelet to read all of the secrets mounted to the node. 

## Recommendations
### Use AWS KMS for envelope encryption of Kubernetes secrets
This allows you to encrypt your secrets with a unique data encryption key (DEK). The DEK is then encrypted using a key encryption key (KEK) from AWS KMS which can be automatically rotated on a recurring schedule. With the KMS plugin for Kubernetes, all Kubernetes secrets are stored in etcd in ciphertext instead of plain text and can only be decrypted by the Kubernetes API server. 
For additional details, see [using EKS encryption provider support for defense in depth](https://aws.amazon.com/blogs/containers/using-eks-encryption-provider-support-for-defense-in-depth/)

### Audit the use of Kubernetes Secrets
On EKS, turn on audit logging and create a CloudWatch metrics filter and alarm to alert you when a secret is used (optional). The following is an example of a metrics filter for the Kubernetes audit log, `{($.verb="get") && ($.objectRef.resource="secret")}`.  You can also use the following queries with CloudWatch Log Insights: 
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| stats count(*) by objectRef.name as secret
| filter verb="get" and objectRef.resource="secrets"
```
The above query will display the number of times a secret has been accessed within a specific timeframe. 
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter verb="get" and objectRef.resource="secrets"
| display objectRef.namespace, objectRef.name, user.username, responseStatus.code
```
This query will display the secret, along with the namespace and username of the user who attempted to access the secret and the response code. 

### Rotate your secrets periodically
Kubernetes doesn't automatically rotate secrets.  If you have to rotate secrets, consider using an external secret store, e.g. Vault or AWS Secrets Manager. 

### Use separate namespaces as a way to isolate secrets from different applications
If you have secrets that cannot be shared between applications in a namespace, create a separate namespace for those applications.

### Use volume mounts instead of environment variables
The values of environment variables can unintentionally appear in logs. Secrets mounted as volumes are instantiated as tmpfs volumes (a RAM backed file system) that are automatically removed from the node when the pod is deleted. 

### Use an external secrets provider
There are several viable alternatives to using Kubernetes secrets, including [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) and Hashicorp's [Vault](https://www.hashicorp.com/blog/injecting-vault-secrets-into-kubernetes-pods-via-a-sidecar/). These services offer features such as fine grained access controls, strong encryption, and automatic rotation of secrets that are not available with Kubernetes Secrets. Bitnami's [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) is another approach that uses asymetric encryption to create "sealed secrets". A public key is used to encrypt the secret while the private key used to decrypt the secret is kept within the cluster, allowing you to safely to store sealed secrets in source control systems like Git. See [Managing secrets deployment in Kubernetes using Sealed Secrets](https://aws.amazon.com/blogs/opensource/managing-secrets-deployment-in-kubernetes-using-sealed-secrets/) for further information. 

As the use of external secrets stores has grown, so has need for integrating them with Kubernetes. The [Secret Store CSI Driver](https://github.com/kubernetes-sigs/secrets-store-csi-driver) is a community project that uses the CSI driver model to fetch secrets from external secret stores. Currently, the Driver has support for [AWS Secrets Manager](https://github.com/aws/secrets-store-csi-driver-provider-aws), Azure, Vault, and GCP. The AWS provider supports both AWS Secrets Manager **and** AWS Parameter Store. It can also be configured to rotate secrets when they expire and can synchronize AWS Secrets Manager secrets to Kubernetes Secrets. Synchronization of secrets can be useful when you need to reference a secret as an environment variable instead of reading them from a volume. 

!!! note
    When the the secret store CSI driver has to fetch a secret, it assumes the IRSA role assigned to the pod that refereces a secret. The code for this operation can be found [here](https://github.com/aws/secrets-store-csi-driver-provider-aws/blob/main/auth/auth.go).
    
For additional information about the AWS Secrets & Configuration Provider (ASCP) refer to the following resources:

+ [How to use AWS Secrets Configuration Provider with Kubernetes Secret Store CSI Driver](https://aws.amazon.com/blogs/security/how-to-use-aws-secrets-configuration-provider-with-kubernetes-secrets-store-csi-driver/)
+ [Integrating Secrets Manager secrets with Kubernetes Secrets Store CSI Driver](https://docs.aws.amazon.com/secretsmanager/latest/userguide/integrating_csi_driver.html)

[external-secrets](https://github.com/external-secrets/kubernetes-external-secrets) is yet another way to use an external secret store with Kubernetes. Like the CSI Driver, external-secrets works against a variety of different backends, including AWS Secrets Manager. The difference is, rather than retrieving secrets from the external secret store, external-secrets copies secrets from these backends to Kubernetes as Secrets.  This let's you manage secrets using your preferred secret store and interact with secrets in a Kubernetes-native way. 
