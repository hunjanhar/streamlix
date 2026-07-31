# this is s3 bucket on aws
resource "aws_s3_bucket" "remote-infra" {
    bucket = "tf-state-bucket-streamlix-app"
    force_destroy = true
    tags = {
        Name = "tf-state-bucket-streamlix-app"
    }
}