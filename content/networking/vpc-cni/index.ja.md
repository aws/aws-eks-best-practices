# Amazon VPC CNI

<iframe width="560" height="315" src="https://www.youtube.com/embed/RBE3yk2UlYA" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

Amazon EKSは、[Amazon VPC Container Network Interface](https://github.com/aws/amazon-vpc-cni-k8s)[(VPC CNI)](https://github.com/aws/amazon-vpc-cni-k8s)プラグインを使用してクラスターネットワーキングを実装しています。CNIプラグインにより、KubernetesのPodはVPCネットワーク上と同じIPアドレスを持つことができます。具体的には、Pod内のすべてのコンテナはネットワーク名前空間を共有し、ローカルポートを使用してお互いと通信することができます。

Amazon VPC CNIには2つのコンポーネントがあります：

* CNIバイナリ：Pod間の通信を有効にするためにPodネットワークを設定します。CNIバイナリはノードのルートファイルシステムで実行され、新しいPodがノードに追加されるか、既存のPodがノードから削除されるときにkubeletによって呼び出されます。
* ipamd：長時間実行されるノードローカルのIPアドレス管理（IPAM）デーモンで、以下の役割を担当します：
  * ノード上のENIの管理
  * 利用可能なIPアドレスまたはプレフィックスのウォームプールの維持

インスタンスが作成されると、EC2はプライマリサブネットに関連付けられたプライマリENIを作成し、アタッチします。プライマリサブネットはパブリックまたはプライベートのいずれかである場合があります。ホストネットワークモードで実行されるPodは、ノードのプライマリENIに割り当てられたプライマリIPアドレスを使用し、ホストと同じネットワーク名前空間を共有します。

CNIプラグインは、ノード上の[Elastic Network Interfaces (ENI)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html)を管理します。ノードがプロビジョニングされると、CNIプラグインは自動的にノードのサブネットからスロット（IPアドレスまたはプレフィックス）のプールを割り当てます。このプールは「ウォームプール」と呼ばれ、そのサイズはノードのインスタンスタイプによって決まります。CNIの設定によっては、スロットはIPアドレスまたはプレフィックスのいずれかになる場合があります。ENIのスロットに割り当てられた場合、CNIはウォームプールのスロットを持つ追加のENIをノードにアタッチすることがあります。これらの追加のENIはセカンダリENIと呼ばれます。各ENIは、インスタンスタイプに基づいて一定数のスロットのみをサポートできます。CNIは、必要なスロットの数に応じてインスタンスに追加のENIをアタッチし続けます。このプロセスは、ノードが追加のENIをサポートできなくなるまで続きます。CNIはまた、Podの高速起動のために「ウォーム」ENIとスロットを事前に割り当てます。ただし、各インスタンスタイプにはアタッチできるENIの最大数があります。これは、Podの密度（ノードあたりのPodの数）の制約の1つであり、計算リソースに加えて考慮する必要があります。

![flow chart illustrating procedure when new ENI delegated prefix is needed](./image.png)

使用できるネットワークインターフェースの最大数とスロットの最大数は、EC2インスタンスのタイプによって異なります。各Podはスロットごとに1つのIPアドレスを消費するため、特定のEC2インスタンスで実行できるPodの数は、それにアタッチできるENIの数と各ENIがサポートするスロットの数に依存します。インスタンスのCPUとメモリリソースの枯渇を防ぐために、EKSユーザーガイドで推奨される最大Pod数を設定することをおすすめします。`hostNetwork`を使用するPodはこの計算から除外されます。特定のインスタンスタイプに対してEKSの推奨最大Pod数を計算するために、[max-pods-calculator.sh](https://github.com/awslabs/amazon-eks-ami/blob/main/templates/al2/runtime/max-pods-calculator.sh)というスクリプトを使用することを検討してください。

## 概要

セカンダリIPモードは、VPC CNIのデフォルトモードです。このガイドでは、セカンダリIPモードが有効な場合のVPC CNIの動作について一般的な概要を提供します。VPC CNIの動作は、VPC CNIの構成設定（[プレフィックスモード](../prefix-mode/index_linux.md)、[ポッドごとのセキュリティグループ](../sgpp/index.md)、[カスタムネットワーキング](../custom-networking/index.md)など）によって異なる場合があります。

Amazon VPC CNIは、ワーカーノード上のKubernetes Daemonsetとしてデプロイされます。ワーカーノードがプロビジョニングされると、プライマリENIと呼ばれるデフォルトのENIがノードにアタッチされます。CNIは、ノードのプライマリENIにアタッチされたサブネットからウォームプールのENIとセカンダリIPアドレスを割り当てます。デフォルトでは、ipamdはノードに追加のENIを割り当てるために試行します。ipamdは、単一のPodがスケジュールされ、プライマリENIからセカンダリIPアドレスが割り当てられると、追加のENIをノードに割り当てます。この「ウォーム」ENIにより、Podのネットワーキングが高速化されます。セカンダリIPアドレスのプールが枯渇すると、CNIは別のENIを追加してさらに割り当てます。

ENIとIPアドレスの数は、[WARM_ENI_TARGET、WARM_IP_TARGET、MINIMUM_IP_TARGET](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/eni-and-ip-target.md)という環境変数で設定されます。`aws-node` Daemonsetは定期的にアタッチされたENIの数をチェックします。すべての`WARM_ENI_TARGET`、または`WARM_IP_TARGET`と`MINIMUM_IP_TARGET`の条件が満たされている場合、十分な数のENIがアタッチされていると見なされます。ENIが不足している場合、CNIは`MAX_ENI`の制限に達するまで、EC2に対してAPIコールを行ってさらにENIをアタッチします。

* `WARM_ENI_TARGET` - 整数、値が>0の場合は要件が有効です
  * 維持するウォームENIの数。ENIは、ノードにセカンダリENIとしてアタッチされているが、いかなるPodにも使用されていない場合に「ウォーム」となります。具体的には、ENIのIPアドレスがいずれのPodにも関連付けられていない状態です。
  * 例：2つのENIをサポートし、各ENIが5つのIPアドレスをサポートするインスタンスを考えてみましょう。WARM_ENI_TARGETを1に設定します。インスタンスに正確に5つのIPアドレスが関連付けられている場合、CNIは2つのENIをインスタンスにアタッチし続けます。最初のENIは使用中であり、このENIの5つの可能なIPアドレスがすべて使用されています。2番目のENIはプール内の5つのIPアドレスを持つ「ウォーム」な状態です。インスタンス上で別のPodが起動されると、6番目のIPアドレスが必要になります。CNIはこの6番目のPodに、2番目のENIから1つのIPアドレスとプールから5つのIPアドレスを割り当てます。2番目のENIは現在使用中であり、「ウォーム」の状態ではありません。CNIは、少なくとも1つのウォームENIを維持するために3番目のENIを割り当てます。

!!! Note
    ウォームENIは、VPCのCIDRからIPアドレスを消費します。IPアドレスは、Podなどのワークロードに関連付けられるまで「未使用」または「ウォーム」です。

* `WARM_IP_TARGET` - 整数、値が>0の場合は要件が有効です
  * 維持するウォームIPアドレスの数。ウォームIPは、アクティブにアタッチされたENIで利用可能ですが、Podに割り当てられていません。つまり、利用可能なウォームIPの数は、追加のENIなしでPodに割り当てることができるIPの数です。
  * 例：1つのENIをサポートし、各ENIが20のIPアドレスをサポートするインスタンスを考えてみましょう。WARM_IP_TARGETを5に設定します。WARM_ENI_TARGETは0に設定します。16番目のIPアドレスが必要になるまで、ENIは1つだけアタッチされます。その後、CNIは2番目のENIをアタッチし、サブネットCIDRから20のアドレスを消費します。
* `MINIMUM_IP_TARGET` - 整数、値が>0の場合は要件が有効です
  * 常に割り当てられるIPアドレスの最小数。これは、インスタンス起動時に複数のENIの割り当てをフロントロードするために一般的に使用されます。
  * 例：新しく起動されたインスタンスを考えてみましょう。1つのENIがあり、各ENIが10のIPアドレスをサポートしています。MINIMUM_IP_TARGETを100に設定します。ENIはすぐに9つのENIを追加アタッチし、合計100のアドレスを持つようになります。これは、WARM_IP_TARGETやWARM_ENI_TARGETの値に関係なく行われます。

このプロジェクトには、[サブネット計算機のExcelドキュメント](../subnet-calc/subnet-calc.xlsx)が含まれています。この計算機のドキュメントでは、異なるENI構成オプション（WARM_IP_TARGETやWARM_ENI_TARGETなど）の下で指定されたワークロードのIPアドレス消費をシミュレートします。

![illustration of components involved in assigning an IP address to a pod](./image-2.png)

KubeletがPodの追加リクエストを受け取ると、CNIバイナリは利用可能なIPアドレスをipamdにクエリし、それをPodに提供します。CNIバイナリはホストとPodのネットワークを接続します。

ノードに展開されたPodは、デフォルトでプライマリENIと同じセキュリティグループに割り当てられます。また、Podは異なるセキュリティグループで構成することもできます。

![second illustration of components involved in assigning an IP address to a pod](./image-3.png)

IPアドレスのプールが枯渇すると、プラグインは自動的に別のElastic Network Interfaceをインスタンスにアタッチし、そのインターフェースに対して別のセカンダリIPアドレスのセットを割り当てます。このプロセスは、ノードが追加のElastic Network Interfaceをサポートできなくなるまで続きます。

![third illustration of components involved in assigning an IP address to a pod](./image-4.png)

Podが削除されると、VPC CNIはPodのIPアドレスを30秒間のクールダウンキャッシュに配置します。クールダウンキャッシュ内のIPは新しいPodに割り当てられません。冷却期間が終了すると、VPC CNIはPodのIPをウォームプールに戻します。冷却期間により、PodのIPアドレスが早期に再利用されるのを防ぎ、すべてのクラスターノード上のkube-proxyがiptablesルールの更新を完了するのを待ちます。IPまたはENIの数がウォームプールの設定数を超えると、ipamdプラグインはIPとENIをVPCに返します。

上記のように、セカンダリIPモードでは、各Podはインスタンスに接続されたENIの1つから1つのセカンダリプライベートIPアドレスを受け取ります。各Podが1つのIPアドレスを使用するため、特定のEC2インスタンスで実行できるPodの数は、それに接続できるENIの数とサポートするIPアドレスの数に依存します。VPC CNIは、各インスタンスタイプごとに許可されるENIとIPアドレスの数を調べるために、[limits](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/pkg/aws/vpc/limits.go)ファイルをチェックします。

ノードごとに展開できる最大のPod数を決定するために、次の式を使用できます。

`(インスタンスタイプのネットワークインターフェースの数 × (ネットワークインターフェースごとのIPアドレスの数 - 1)) + 2`

+2は、kube-proxyやVPC CNIなどのホストネットワーキングを使用するKubernetesのPodを示しています。Amazon EKSでは、kube-proxyとVPC CNIがすべてのノードで実行される必要があり、これらはmax-podsに計算されます。ホストネットワーキングのPodを実行する予定がある場合は、max-podsを更新することを検討してください。起動テンプレートのユーザーデータに`--kubelet-extra-args "—max-pods=110"`を指定できます。

例えば、3つのc5.largeノード（3つのENIとENIごとに最大10個のIP）を持つクラスターでは、クラスターが起動し、2つのCoreDNSポッドがある場合、CNIは49個のIPアドレスを消費し、ウォームプールに保持します。ウォームプールにより、アプリケーションの展開時により速いPodの起動が可能になります。

ノード1（CoreDNSポッドあり）：2つのENI、20個のIPが割り当てられています

ノード2（CoreDNSポッドあり）：2つのENI、20個のIPが割り当てられています

ノード3（ポッドなし）：1つのENI、10個のIPが割り当てられています

インフラストラクチャポッド（通常はデーモンセットとして実行される）は、max-podのカウントに寄与します。これには次のものが含まれます。

* CoreDNS
* Amazon Elastic LoadBalancer
* metrics-serverの操作ポッド

これらのポッドの容量を組み合わせてインフラストラクチャを計画することをお勧めします。各インスタンスタイプでサポートされる最大Pod数のリストについては、GitHubの[eni-max-Pods.txt](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt)を参照してください。

![illustration of multiple ENIs attached to a node](./image-5.png)

## 推奨事項

### VPC CNI Managed Add-Onをデプロイする

クラスターをプロビジョニングすると、Amazon EKSは自動的にVPC CNIをインストールします。ただし、Amazon EKSは、クラスターが計算、ストレージ、ネットワーキングなどの基礎となるAWSリソースと対話するための管理されたアドオンをサポートしています。VPC CNIを含む管理されたアドオンを使用してクラスターをデプロイすることを強くお勧めします。

Amazon EKSの管理されたアドオンは、Amazon EKSクラスターのVPC CNIのインストールと管理を提供します。Amazon EKSのアドオンには、最新のセキュリティパッチやバグ修正が含まれており、Amazon EKSとの互換性がAWSによって検証されています。VPC CNIアドオンにより、Amazon EKSクラスターのセキュリティと安定性を継続的に確保し、アドオンのインストール、設定、更新に必要な作業量を減らすことができます。また、管理されたアドオンは、Amazon EKS API、AWS Management Console、AWS CLI、eksctlを介して追加、更新、削除することができます。

`kubectl get`コマンドに`--show-managed-fields`フラグを使用して、VPC CNIの管理フィールドを確認できます。

```
kubectl get daemonset aws-node --show-managed-fields -n kube-system -o yaml
```

管理されたアドオンは、自動的に15分ごとに構成のドリフトを防止するために設定を上書きします。これは、アドオンの作成後にKubernetes APIを介して行われた管理されたアドオンの変更が、自動化されたドリフト防止プロセスによって上書きされ、デフォルトに設定されることを意味します。

本番クラスターを更新する前に、特定の構成に対して非本番クラスターでアドオンの動作をテストすることをお勧めします。また、[add-onの設定](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html)に関するEKSユーザーガイドの手順に従ってください。

#### 管理されたアドオンに移行する

自己管理型のVPC CNIのバージョン互換性とセキュリティパッチの更新を管理する必要があります。自己管理型のアドオンを更新するには、Kubernetes APIと[EKSユーザーガイド](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html#updating-vpc-cni-add-on)で説明されている手順を使用する必要があります。既存のEKSクラスターでは、管理されたアドオンに移行することを強くお勧めし、移行前に現在のCNI設定のバックアップを作成することを強くお勧めします。管理されたアドオンの設定については、Amazon EKS API、AWS Management Console、またはAWS Command Line Interfaceを使用できます。

```
kubectl apply view-last-applied daemonset aws-node -n kube-system > aws-k8s-cni-old.yaml
```

Amazon EKSは、フィールドが管理され、デフォルトの設定でリストされている場合、CNIの設定を置き換えます。管理されたフィールドの変更を変更しないように注意してください。アドオンは、*warm*環境変数やCNIモードなどの構成フィールドを調整しません。Podとアプリケーションは、管理されたCNIに移行する間も引き続き実行されます。

#### アップデート前にCNI設定をバックアップする

VPC CNIは、カスタマーデータプレーン（ノード）で実行されるため、新しいバージョンがリリースされた場合やクラスターを新しいKubernetesマイナーバージョンに[更新](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)した後に、自動的にアドオン（管理されたおよび自己管理型）を更新しません。既存のクラスターのアドオンを更新するには、アドオンの更新をトリガーする必要があります。これは、update-addon APIを介して更新をトリガーするか、EKSコンソールのupdate nowリンクをクリックすることで行うことができます。自己管理型のアドオンを展開した場合は、[自己管理型VPC CNIアドオンの更新](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html#updating-vpc-cni-add-on)に記載されている手順に従ってください。

1つのマイナーバージョンずつアップデートすることを強くお勧めします。たとえば、現在のマイナーバージョンが「1.9」で、「1.11」に更新する場合は、まず「1.10」の最新のパッチバージョンに更新し、次に「1.11」の最新のパッチバージョンに更新する必要があります。

Amazon VPC CNIの更新前にaws-node Daemonsetを検査してください。既存の設定のバックアップを取得してください。管理されたアドオンを使用している場合は、Amazon EKSが上書きする可能性のある設定を更新していないことを確認してください。アドオンの更新後に自動化ワークフローでのポスト更新フックまたは手動の適用ステップをお勧めします。

```
kubectl apply view-last-applied daemonset aws-node -n kube-system > aws-k8s-cni-old.yaml
```

自己管理型のアドオンの場合、バックアップをGitHubの`releases`と比較して利用可能なバージョンを確認し、更新するバージョンの変更に慣れてください。自己管理型のアドオンを管理するためにHelmを使用し、値ファイルを利用して設定を適用することをお勧めします。Daemonsetの削除を伴う更新操作は、アプリケーションのダウンタイムを引き起こすため、避ける必要があります。

### セキュリティコンテキストを理解する

VPC CNIを効率的に管理するために、設定されたセキュリティコンテキストを理解することを強くお勧めします。Amazon VPC CNIには、CNIバイナリとipamd（aws-node）Daemonsetの2つのコンポーネントがあります。CNIはノード上でバイナリとして実行され、ノードのルートファイルシステムへのアクセス権限があり、iptablesをノードレベルで扱うため特権アクセス権限を持っています。CNIバイナリは、Podが追加または削除されたときにkubeletによって呼び出されます。

aws-node Daemonsetは、ノードレベルでのIPアドレス管理を担当する長時間実行プロセスです。aws-nodeは`hostNetwork`モードで実行され、ループバックデバイスへのアクセスや同じノード上の他のポッドのネットワークアクティビティにアクセスできます。aws-nodeのinitコンテナは特権モードで実行され、CRIソケットをマウントし、ノード上で実行されているPodのIP使用状況を監視するためのDaemonsetにアクセス権限を与えます。Amazon EKSは、aws-node initコンテナの特権要件を削除するための作業を進めています。さらに、aws-nodeはNATエントリを更新し、iptablesモジュールをロードする必要があるため、NET_ADMIN特権で実行されます。

Amazon EKSでは、Podとネットワーキング設定のIP管理のために、aws-nodeマニフェストで定義されたセキュリティポリシーをデプロイすることをお勧めします。VPC CNIの最新バージョンに更新することを検討してください。さらに、特定のセキュリティ要件がある場合は、[GitHubの問題](https://github.com/aws/amazon-vpc-cni-k8s/issues)を開くことを検討してください。

### CNI用に別のIAMロールを使用する

AWS VPC CNIには、AWS Identity and Access Management（IAM）の権限が必要です。IAMロールを使用する前に、CNIポリシーを設定する必要があります。IPv4クラスター用に[`AmazonEKS_CNI_Policy`](https://console.aws.amazon.com/iam/home#/policies/arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy%24jsonEditor)を使用できます。AmazonEKS CNI管理ポリシーには、IPv4クラスターの権限のみが含まれています。IPv6クラスター用の別個のIAMポリシーを作成し、[ここ](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-create-ipv6-policy)にリストされている権限を割り当てる必要があります。

VPC CNIは、デフォルトで[Amazon EKSノードIAMロール](https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html)（管理されたおよび自己管理型のノードグループの両方）を継承します。

Amazon VPC CNIのために関連するポリシーを持つ別個のIAMロールを設定することを**強く**お勧めします。そうしない場合、Amazon VPC CNIのポッドはノードに割り当てられた権限を持つノードIAMロールにアクセス権限を与えられ、ノードに割り当てられたインスタンスプロファイルにアクセスできます。

デフォルトでは、VPC CNIは[Amazon EKSノードIAMロール](https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html)（管理されたおよび自己管理型のノードグループの両方）を継承します。

Amazon VPC CNIのために関連するポリシーを持つ別個のIAMロールを設定することを**強く**お勧めします。そうしない場合、Amazon VPC CNIのポッドはノードに割り当てられた権限を持つノードIAMロールにアクセス権限を与えられ、ノードに割り当てられたインスタンスプロファイルにアクセスできます。

VPC CNIプラグインは、aws-nodeというサービスアカウントを作成および設定します。デフォルトでは、サービスアカウントはAmazon EKSノードIAMロールにAmazon EKS CNIポリシーが添付された状態でバインドされます。別個のIAMロールを使用する場合は、Amazon EKS CNIポリシーが添付された新しいサービスアカウントを[作成](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-create-role)することをお勧めします。新しいサービスアカウントを使用するには、CNIポッドを[再デプロイ](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-redeploy-pods)する必要があります。新しいクラスターを作成する際には、VPC CNI管理されたアドオンの`--service-account-role-arn`を指定することを検討してください。また、Amazon EKSノードロールからIPv4およびIPv6のAmazon EKS CNIポリシーを削除してください。

セキュリティ侵害の影響範囲を最小限に抑えるために、[インスタンスメタデータへのアクセスをブロック](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#restrict-access-to-the-instance-profile-assigned-to-the-worker-node)することをお勧めします。

### Liveness/Readiness Probeの失敗に対処する

EKS 1.20以降のクラスターでは、liveness および readiness probe のタイムアウト値（デフォルトは`timeoutSeconds: 10`）を増やすことをお勧めします。これにより、プローブの失敗がアプリケーションのPodがcontainerCreating状態になるのを防ぐことができます。この問題は、データ集約型およびバッチ処理クラスターで見られます。高いCPU使用率により、aws-nodeのプローブのヘルスチェックが失敗し、PodのCPUリクエストが満たされなくなります。プローブのタイムアウトを変更するだけでなく、aws-nodeのCPUリソースリクエスト（デフォルトは`CPU: 25m`）が正しく設定されていることも確認してください。ノードに問題がない限り、設定の更新はおすすめしません。

Amazon EKSサポートに連絡する際には、ノードでsudo `bash /opt/cni/bin/aws-cni-support.sh`を実行することを強くお勧めします。このスクリプトは、ノード上のkubeletログとメモリ使用状況の評価を支援します。Amazon EKSワーカーノードにSSMエージェントをインストールしてスクリプトを実行することを検討してください。

### EKS最適化されていないAMIインスタンスでのIPTablesフォワードポリシーの設定

カスタムAMIを使用している場合は、[kubelet.service](https://github.com/awslabs/amazon-eks-ami/blob/master/files/kubelet.service#L8)のiptablesフォワードポリシーをACCEPTに設定してください。多くのシステムでは、iptablesのフォワードポリシーがDROPに設定されています。[HashiCorp Packer](https://packer.io/intro/why.html)と[Amazon EKS AMIリポジトリのリソースと設定スクリプト](https://github.com/awslabs/amazon-eks-ami)を使用してカスタムAMIをビルドし、[kubelet.service](https://github.com/awslabs/amazon-eks-ami/blob/master/files/kubelet.service#L8)を更新し、[ここ](https://aws.amazon.com/premiumsupport/knowledge-center/eks-custom-linux-ami/)で指定されている手順に従ってカスタムAMIを作成してください。

### 定期的なCNIバージョンのアップグレード

VPC CNIは後方互換性があります。最新バージョンは、すべてのAmazon EKSでサポートされているKubernetesバージョンと互換性があります。さらに、VPC CNIはEKSアドオンとして提供されています（上記の「VPC CNI Managed Add-Onのデプロイ」を参照）。EKSアドオンはアドオンのアップグレードをオーケストレーションしますが、CNIのようなアドオンはデータプレーンで実行されるため、自動的にアップグレードされません。VPC CNIアドオンのアップグレードは、管理されたおよび自己管理型のワーカーノードのアップグレードに続いて行う必要があります。

