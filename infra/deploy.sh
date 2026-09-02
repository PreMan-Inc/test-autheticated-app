#!/usr/bin/env bash
# Build the Lambda bundle, upload it, and roll the stack. Prints the API URL.
set -euo pipefail

cd "$(dirname "$0")/.."

AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-test-authenticated-app}"
DEMO_PASSWORD="${DEMO_PASSWORD:-PremanDemo123!}"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ARTIFACT_BUCKET="${ARTIFACT_BUCKET:-preman-deployments-${ACCOUNT_ID}-${AWS_REGION}}"

rm -rf build
mkdir -p build/lambda

# arm64 wheels only: the function runs on Graviton, and a source build here
# would produce a bundle that imports fine locally and not at all in Lambda.
pip install \
  --quiet \
  --requirement requirements.txt \
  --target build/lambda \
  --platform manylinux2014_aarch64 \
  --python-version 3.12 \
  --only-binary :all:

cp -R app build/lambda/app
(cd build/lambda && zip -qr ../function.zip .)

ARTIFACT_KEY="test-authenticated-app/$(git rev-parse --short HEAD)-$(git hash-object build/function.zip | cut -c1-12)/function.zip"

if ! aws s3api head-bucket --bucket "${ARTIFACT_BUCKET}" 2>/dev/null; then
  aws s3api create-bucket --bucket "${ARTIFACT_BUCKET}" --region "${AWS_REGION}"
fi

aws s3 cp build/function.zip "s3://${ARTIFACT_BUCKET}/${ARTIFACT_KEY}"

aws cloudformation deploy \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --template-file infra/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    CodeBucket="${ARTIFACT_BUCKET}" \
    CodeKey="${ARTIFACT_KEY}" \
    DemoPassword="${DEMO_PASSWORD}" \
  --tags application=test-authenticated-app

aws cloudformation describe-stacks \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
