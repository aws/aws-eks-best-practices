package main

import (
	"flag"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ec2"
)

var REGION string

func getLaunchTemplates() {
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(REGION)},
	)
	client := ec2.New(sess)
	input := &ec2.DescribeLaunchTemplatesInput{}
	output, err := client.DescribeLaunchTemplates(input)
	if err != nil {
		fmt.Println(err)
	}
	templates := output.LaunchTemplates

	for _, v := range templates {
		input := &ec2.DescribeLaunchTemplateVersionsInput{
			LaunchTemplateId: v.LaunchTemplateId,
			Versions:         []*string{aws.String("$Default")},
		}
		output, _ := client.DescribeLaunchTemplateVersions(input)
		versions := output.LaunchTemplateVersions

		for _, v := range versions {
			fmt.Println("The launch template:\t", aws.StringValue(v.LaunchTemplateId), aws.StringValue(v.LaunchTemplateName))
			if v.LaunchTemplateData.MetadataOptions != nil {
				fmt.Println("Has hop count of:\t", aws.Int64Value(v.LaunchTemplateData.MetadataOptions.HttpPutResponseHopLimit))
			} else {
				fmt.Println("Has hop count of:\t undefined")
			}
		}
	}
}

func main() {
	flag.StringVar(&REGION, "region", "us-west-2", "AWS region")
	flag.Parse()
	getLaunchTemplates()
}
