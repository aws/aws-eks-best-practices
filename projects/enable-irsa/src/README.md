You can find a copy of the binary in the /bin directory (MacOS only)

To run the script install the prerequisites: 

- Python 3.7.5 or higher
- Create venv (optional)

`python3 -m venv /path/to/new/virtual/environment`

- Install packages

`pip install --trusted-host pypi.python.org -r requirements.txt`

- Run application

`python main.py. --cluster-name <cluster_name> --role-name <role_name>  --region <aws_region(optional)> --account <aws_account_no(optional)>`
