import boto3, click, subprocess
from OpenSSL import SSL
from requests import request
from urllib import parse
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pick import pick
import socket
import json, os

iam = boto3.client('iam')
eks = boto3.client('eks')
sts = boto3.client('sts')

class Cluster(object):
    def __init__(self, version, endpoint, identity, certificateAuthority, *args, **kwargs):
        self.version = float(version)
        self.endpoint = endpoint
        self.issuer = identity['oidc']['issuer']
        self.data = certificateAuthority['data']


def choice(Question: str):
    response = input(Question).strip().lower()
    return response


def check_cluster_version(version):
    if version >= 1.12:
        pass
    else:
        raise Exception('Cluster must be running v1.12 or higher')
        exit(1)


def describe_cluster(ClusterName: str):
    print('Obtaining OIDC URL and thumbprint.')
    try:
        api_response = eks.describe_cluster(name=ClusterName)
    except eks.exceptions.ResourceNotFoundException as e:
        print('Cluster {} does not exist.').format(ClusterName)

    cluster = Cluster(**api_response['cluster'])
    oidc_url = cluster.issuer
    response = request('GET', oidc_url + "/.well-known/openid-configuration", verify=True)
    jwks_uri = json.loads(response.text)['jwks_uri']
    hostname = parse.urlparse(jwks_uri).hostname
    ctx = SSL.Context(SSL.TLSv1_2_METHOD)
    sock = socket.socket()
    conn = SSL.Connection(ctx, sock)
    conn.connect((hostname, 443))
    conn.set_connect_state()
    conn.do_handshake()
    certs = conn.get_peer_cert_chain()
    thumbprint = certs[-1].digest('sha1').decode('utf-8').replace(':', "")

    return cluster, thumbprint


def create_odic_provider(OidcUrl: str, Thumbprint: str):
    while True:
        response = choice('Creating a OIDC provider. This is privileged operation. Do you want to proceed (yes/no)? ')
        if response == 'yes':
            break
        if response == 'no':
            exit(1)
        else:
            print('Please enter "Yes" or "No".')
    try:
        iam.create_open_id_connect_provider(
            Url=OidcUrl,
            ClientIDList=[
                'sts.amazonaws.com'
            ],
            ThumbprintList=[
                Thumbprint,
            ]
        )
    except iam.exceptions.EntityAlreadyExistsException:
        print('The OIDC provider already exists')


def create_iam_role(RoleName: str, TrustPolicy: dict):
    print('Creating IAM role.')
    try:
        role = iam.create_role(
            RoleName=RoleName,
            AssumeRolePolicyDocument=json.dumps(TrustPolicy)
        )
    except iam.exceptions.InvalidInputException:
        print('Invalid input.')
        exit(1)
    except iam.exceptions.MalformedPolicyDocumentException:
        print('Malformed policy document')
        exit(1)
    except iam.exceptions.EntityAlreadyExistsException:
        print('Role already exists. Getting Arn.')
        role_arn = iam.get_role(RoleName=RoleName)['Role']['Arn']
        return role_arn
    return role['Role']['Arn']


def attach_role_policy(RoleName: str):
    print('Attaching CNI policy to role.')
    try:
        iam.attach_role_policy(
            RoleName=RoleName,
            PolicyArn='arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy'
        )
    except iam.exceptions.NoSuchEntityException:
        print('No such entity found.')
        exit(1)
    except iam.exceptions.InvalidInputException:
        print('Invalid input.')
        exit(1)


def create_trust_policy(Account: str, OidcUrl: str):
    # TODO(jicowan@amazon.com) Append trust policy for re-use with multiple clusters
    OidcUrl = OidcUrl.lstrip('https://')
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": "arn:aws:iam::" + Account + ":oidc-provider/" + OidcUrl
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        OidcUrl + ":aud": "sts.amazonaws.com",
                        OidcUrl + ":sub": "system:serviceaccount:kube-system:aws-node"
                    }
                }
            }
        ]
    }
    return trust_policy


def update_cni_sa(RoleArn: str, Context: object, **kwargs):
    print('Patching aws-node ServiceAccount')
    if 'Clientset' in kwargs:
        api_client = kwargs['Clientset']
        CoreV1 = client.CoreV1Api(api_client)
    else:
        CoreV1 = client.CoreV1Api(api_client=config.new_client_from_config(context=Context))
    patch = {
        "metadata": {
            "annotations": {
                "eks.amazonaws.com/role-arn": RoleArn
            }
        }
    }
    try:
        CoreV1.patch_namespaced_service_account(name='aws-node', namespace='kube-system', body=patch)
    except ApiException:
        print('An error occurred while trying to patch the aws-node ServiceAccount')
        exit(1)


def get_token(ClusterName: str):
    args = ("aws", "eks", "get-token", "--cluster-name", ClusterName)
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    token = popen.stdout.read().rstrip().decode('UTF8')
    token = json.loads(token)['status']['token']
    return str(token)


def create_clientset(ApiEndpoint: str, ClusterName: str, Certificate: str):
    token = get_token(ClusterName)
    configuration = client.Configuration()
    configuration.host = ApiEndpoint
    configuration.verify_ssl = False  # Should change this to true
    configuration.api_key = {'authorization': 'Bearer ' + token}
    api_client = client.ApiClient(configuration)
    return api_client


def patch_aws_node(Context: str, **kwargs):
    while True:
        response = choice("Do you want to patch the aws-node Daemonset(Yes/No)? This will trigger a rolling restart of the networking plugin: ")
        if response == 'yes':
            break
        if response == 'no':
            exit(1)
        else:
            print('Please enter "Yes" or "No".')
    print('Patching aws-node daemonset')
    if 'Clientset' in kwargs:
        api_client = kwargs['Clientset']
        AppsV1 = client.AppsV1Api(api_client)
    else:
        AppsV1 = client.AppsV1Api(api_client=config.new_client_from_config(context=Context))

    patch = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "irsa": "enabled"
                    }
                }
            }
        }
    }
    try:
        AppsV1.patch_namespaced_daemon_set_with_http_info(name='aws-node', namespace='kube-system', body=patch)
    except ApiException:
        print('An error occurred while patching the aws-node Daemonset')
        exit(1)

def choose_context():
    try:
        config.load_kube_config()
    except Exception:
        print(f'Could not find kubeconfig in the default location.')
        return None
    contexts, active_context = config.list_kube_config_contexts()
    if not contexts:
        print("Cannot find any context in kube-config file.")
        exit()
    contexts = [context['name'] for context in contexts]
    active_index = contexts.index(active_context['name'])
    selected, first_index = pick(contexts, title="Pick the context to run this against (press SPACE to mark, ENTER to continue): ", default_index=active_index)
    return selected

@click.command()
@click.option('--account', help='The AWS account number', required=False)
@click.option('--cluster-name', help='The EKS cluster name', required=True)
@click.option('--role-name', help='The role name for the AWS CNI', required=True)
@click.option('--region', help='The AWS region', required=False)
def main(account, cluster_name, role_name, region):
    global iam, eks, sts
    iam.region_name = region
    eks.region_name = region
    sts.region_name = region
    if account == None:
        account = sts.get_caller_identity()["Account"]

    cluster, thumbprint = describe_cluster(ClusterName=cluster_name)
    check_cluster_version(cluster.version)
    create_odic_provider(OidcUrl=cluster.issuer, Thumbprint=thumbprint)
    trust_policy = create_trust_policy(Account=account, OidcUrl=cluster.issuer)
    role_arn = create_iam_role(RoleName=role_name, TrustPolicy=trust_policy)
    attach_role_policy(RoleName=role_name)
    context = choose_context()
    if context == None:
        api_client = create_clientset(ApiEndpoint=cluster.endpoint, ClusterName=cluster_name, Certificate=cluster.data)
        update_cni_sa(RoleArn=role_arn, Context=context, Clientset=api_client)
        patch_aws_node(Context=context, Clientset=api_client)
    else:
        update_cni_sa(RoleArn=role_arn, Context=context)
        patch_aws_node(Context=context)


if __name__ == '__main__':
    main()
