package main

import (
	"flag"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ec2"
)

var region string

func updateLaunchTemplates(lt string) {
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(region)},
	)
	client := ec2.New(sess)
	opts := &ec2.LaunchTemplateInstanceMetadataOptionsRequest{
		HttpPutResponseHopLimit: aws.Int64(1),
		HttpTokens:              aws.String("required"),
	}
	ltvo, err := client.CreateLaunchTemplateVersion(
		&ec2.CreateLaunchTemplateVersionInput{
			LaunchTemplateId:   aws.String(lt),
			SourceVersion:      aws.String("$Default"),
			LaunchTemplateData: &ec2.RequestLaunchTemplateData{MetadataOptions: opts},
			VersionDescription: aws.String("Hop count 1"),
		},
	)
	if err != nil {
		fmt.Println(err)
	}

	_, err = client.ModifyLaunchTemplate(
		&ec2.ModifyLaunchTemplateInput{
			DefaultVersion:   aws.String(fmt.Sprint(*ltvo.LaunchTemplateVersion.VersionNumber)),
			LaunchTemplateId: aws.String(lt),
		},
	)
	if err != nil {
		fmt.Println(err)
	}
	fmt.Printf("Updated template %s successfully. IMDSv2 is required and hop count is set to 1.", lt)
}
func main() {
	var lt string
	flag.StringVar(&region, "region", "us-east-1", "AWS region")
	flag.StringVar(&lt, "launch-template", "", "Launch template Id")
	flag.Parse()
	updateLaunchTemplates(lt)
}
