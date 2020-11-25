# IMDS
As a best practice, you should prevent pods from accessing EC2 metadata.  This can be done by creating an iptables rule on each of your worker nodes or by 
requiring IMDSv2 and setting the hop count to 1.  The imds executable is a simple command line utility that enumerates all of the launch templates in a region
and outputs the current hop count for IMDS.  The imds-update executable accepts a launch template id as an argument and creates a new version of the launch
template with IMDSv2 required and hop count set to 1.  It then sets that version as the default version for the launch template.  The executables were compiled
for Darwin (MacOS), but the source code is also available.

## Usage
### imds
```
imds -region <aws region>
```
#### Sample output
```
The launch template:     lt-0284c77c24a6ad7a7 eksctl-agones-nodegroup-ng-0
Has hop count of:        2
The launch template:     lt-07aa2a861689548ae ecs-fleetiq-template
Has hop count of:        undefined
```

### imds-update
```
imds-update -region <aws region> -launch-template <launch template id>
```
#### Sample output
```
Updated template lt-0a85731194545a910 successfully. IMDSv2 is required and hop count is set to 1.
```
