package main

import (
	"flag"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ec2"
)

var	REGION string

func updateLaunchTemplates(lt string){
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(REGION)},
	)
	client := ec2.New(sess)
	opts := &ec2.LaunchTemplateInstanceMetadataOptionsRequest{
		HttpPutResponseHopLimit: aws.Int64(1),
		HttpTokens: aws.String("required"),
	}
	ltd := &ec2.RequestLaunchTemplateData{
		MetadataOptions: opts,
	}
	ltvi := &ec2.CreateLaunchTemplateVersionInput{
		LaunchTemplateId: aws.String(lt),
		SourceVersion: aws.String("$Default"),
		LaunchTemplateData: ltd,
		VersionDescription: aws.String("Hop count 1"),
	}
	ltvo, err := client.CreateLaunchTemplateVersion(ltvi)
	if err != nil {
		fmt.Println(err)
	}
	lti := &ec2.ModifyLaunchTemplateInput{
		DefaultVersion:   aws.String(fmt.Sprint(*ltvo.LaunchTemplateVersion.VersionNumber)),
		LaunchTemplateId: aws.String(lt),
	}
	_, err = client.ModifyLaunchTemplate(lti)
	if err != nil {
		fmt.Println(err)
	}
	fmt.Printf("Updated template %s successfully. IMDSv2 is required and hop count is set to 1.", lt)
}
func main() {
	var lt string
	flag.StringVar(&REGION, "region", "us-east-1", "AWS region")
	flag.StringVar(&lt, "launch-template", "", "Launch template Id")
	flag.Parse()
	updateLaunchTemplates(lt)
}
