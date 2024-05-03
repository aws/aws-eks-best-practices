# enable-irsa

Is a commandline utility that does the following: 

1. Creates an OIDC endpoint for your cluster if it doesn't already exist
2. Creates an IAM role with a trust policy that allows the aws-node ServiceAccount to assume a role that allows the AWS VPC CNI plugin to function
3. Annotates the aws-node ServiceAccount with a reference to the Arn of the IAM role created in the previous step
4. Annotates the aws-node Daemonset to trigger a rolling update

Running this utility effectively replaces the IAM role currently assigned to the EC2 instance that the aws-node Daemonset is running on with IRSA which allows you to assign an IAM role to a pod.   

> Note: The binary for this utility can be found in the /bin directory (MacOS only)

## Installation

To run the script on your local machine, please install the following prerequisites: 

- Python 3.7.5 or higher
- Create venv (optional)

`python3 -m venv /path/to/new/virtual/environment`

- Install packages

`pip install --trusted-host pypi.python.org -r requirements.txt`

- Run application

`python main.py. --cluster-name [cluster_name(required)] --role-name [role_name(required)]  --region [aws_region(optional)] --account [aws_account_no(optional)]`

## Running with Docker

To run as a Docker container, complete the following steps: 

- Clone this repository

`git clone git@github.com:aws/aws-eks-best-practices.git`

- Build the container

`docker build -t [repo]/[image]:[tag] .`

- Run the Docker container

`docker run -it -v ~/.aws/:/root/.aws/ [repo]/[image]:[tag] --cluster-name [cluster_name(required)] --role-name [role_name(required)]  --region [aws_region(optional)] --account [aws_account_no(optional)]`
