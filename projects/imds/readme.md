# IMDS
As a best practice, you should prevent pods from accessing EC2 metadata.  This can be done by creating an iptables rule on each of your worker nodes or by 
requiring IMDSv2 and setting the hop count to 1.  The imds executable is a simple command line utility that enumerates all of the launch templates in a region
and outputs the current hop count for IMDS.  The imds-update executable accepts a launch template id as an argument and creates a new version of the launch
template with IMDSv2 required and hop count set to 1.  It then sets that version as the default version for the launch template.  The executables were compiled
for Darwin (MacOS), but the source code is also available.
