# Encryption at rest
There are 3 different AWS-native storage options you can use with Kubernetes: EBS, EFS, and FSx for Lustre.  All 3 offer encryption at rest using a service managed key or a customer master key (CMK). For EBS you can use the in-tree storage driver or the [EBS CSI driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver).  Both include parameters for encrypting volumes and supplying a CMK.  For EFS, you can use the [EFS CSI driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver), however, unlike EBS, the EFS CSI driver does not support dynamic provisioning.  If you want to use EFS with EKS, you will need to provision and configure at-rest encryption for the file system prior to creating a PV. For further information about EFS file encryption, please refer to [Encrypting Data at Rest](https://docs.aws.amazon.com/efs/latest/ug/encryption-at-rest.html). Besides offering at-rest encryption, EFS and FSx for Lustre include an option for encrypting data in transit.  FSx for Luster does this by default.  For EFS, you can add transport encryption by adding the `tls` parameter to `mountOptions` in your PV as in this example: 

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
## Recommendations
### Encrypt data at rest
Encrypting data at rest is considered a best practice.  If you're unsure whether encryption is necessary, encrypt your data. 

### Rotate your CMKs periodically
Configure KMS to automatically rotate you CMKs.  This will rotate your keys once a year while saving old keys indefinitely so that your data can still be decrypted.  For additional information see [Rotating customer master keys](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)

### Use EFS access points to simplify access to shared datasets
If you have shared datasets with different POSIX file permissions or want to restrict access to part of the shared file system by creating different mount points, consider using EFS access points. To learn more about working with access points, see https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html. Today, if you want to use access point (AP) you'll need to reference the AP in the PV's `volumeHandle` parameter.

# Secrets management
Kubernetes secrets are used to store sensitive information, such as user certificates, passwords, or API keys. They are persisted in etcd as base64 encoded strings.  On EKS, the EBS volumes for etcd nodes are encypted with [EBS encryption](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html).  A pod can retrieve a Kubernetes secrets objects by referencing the secret in the `podSpec`.  These secrets can either be mapped to an environment variable or mounted as volume. For additional information on creating secrets, see https://kubernetes.io/docs/concepts/configuration/secret/. 

> Caution: Secrets in a particular namespace can be referenced by all pods in the secret's namespace.

> Caution: The node authorizer allows the Kubelet to read all of the secrets mounted to the node. 

## Recommendations
### Use separate namespaces as a way to isolate secrets from different applications
If you have secrets that cannot be shared between applications in a namespace, create a separate namespace for those applications.

### Use volume mounts instead of environment variables
The values of environment variables can unintentionally appear in logs. Secrets mounted as volumes are instatiated as tmpfs volumes (a RAM backed file system) that are automatically removed from the node when the pod is deleted. 

### Use an external secrets provider
There are several viable alternatives to using Kubernetes secrets, include Bitnami's [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) and Hashicorp's [Vault](
https://www.hashicorp.com/blog/injecting-vault-secrets-into-kubernetes-pods-via-a-sidecar/). Unlike Kubernetes secrets which can be shared amongst all of the pods within a namespace, Vault gives you the ability to limit access to particular pods through the use of Kubernetes service accounts.  It also has support for secret rotation.  If Vault is not to your liking, you can use similar approach with AWS Secrets Manager, as in this example https://github.com/jicowan/secret-sidecar or you could try using a [serverless](https://github.com/mhausenblas/nase) mutating webhook instead.

### Audit the use of secrets
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

### Use AWS KMS for envelop encryption of Kubernetes secrets
This allows you to encrypt your secrets with a unique data encryption key (DEK). The DEK is then encypted using a key encryption key (KEK) from AWS KMS which can be automatically rotated on a recurring schedule. With the KMS plugin for Kubernetes, all Kubernetes secrets are stored in etcd in ciphertext instead of plain text and can only be decrypted by the Kubernetes API server. 
For additional details, see [using EKS encryption provider support for defense in depth](https://aws.amazon.com/blogs/containers/using-eks-encryption-provider-support-for-defense-in-depth/)