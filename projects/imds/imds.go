package main

import (
	"context"
	"flag"
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ec2"
)

var region string

func getLaunchTemplates() {
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(region)},
	)
	client := ec2.New(sess)
	ctx := context.Background()

	client.DescribeLaunchTemplatesPagesWithContext(ctx, &ec2.DescribeLaunchTemplatesInput{},
		func(page *ec2.DescribeLaunchTemplatesOutput, lastPage bool) bool {
			fmt.Println("Received", len(page.LaunchTemplates), "objects in page")
			for _, obj := range page.LaunchTemplates {
				output, _ := client.DescribeLaunchTemplateVersions(&ec2.DescribeLaunchTemplateVersionsInput{
					LaunchTemplateId: obj.LaunchTemplateId,
					Versions:         []*string{aws.String("$Default")},
				})
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
			return true
		},
	)
}

func main() {
	flag.StringVar(&region, "region", "us-west-2", "AWS region")
	flag.Parse()
	getLaunchTemplates()
}
