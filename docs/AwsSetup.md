# AWS Setup for Live Translation

## 1. Creating an AWS Account
- Go to the [AWS Management Console](https://aws.amazon.com/).
- Click on **Create a new AWS account**.
- Follow the on-screen instructions to complete the account creation process.

## 2. Creating a User
- Sign in to the AWS Management Console.
- Navigate to the **IAM (Identity and Access Management)** service.
- In the left navigation pane, click on **Users** and then **Create user**.
- Enter a **User name** and click **Next**.
- Skip permissions for now and click **Next**.
- Finally click **Create user**

## 3. Add Permissions and generate Access Keys for the User
- After creating the user, you will see the User details page.
- Select the user you just created.
- Click on **Add permissions** and select **Create inline policy**.
- Click **JSON** create a policy with these permissions:
  <details>
  <summary>Policy permissions</summary>
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "polly:SynthesizeSpeech",
                "transcribe:StartStreamTranscription",
                "translate:ListLanguages",
                "translate:TranslateText",
                "polly:DescribeVoices"
            ],
            "Resource": "*"
        }
    ]
  }
  </details>
- Set a Policy name, e.g. `Gemeinde-Uebersetzung`. Then select **Create policy**.
- Back in the user menu click on **Create access key**.
- Note down the **Access key ID** and **Secret access key**.

## 4. Storing Access Keys Locally
- On your local machine, create a directory named `.aws` in your home directory if it doesn’t already exist.
- Inside the `.aws` directory, create a file named `credentials`.
- Open the `credentials` file in a text editor and add the following content:
    ```
    [default]
    aws_access_key_id = YOUR_ACCESS_KEY_ID
    aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
    ```
- Replace `YOUR_ACCESS_KEY_ID` and `YOUR_SECRET_ACCESS_KEY` with the actual values from the previous step.
- In the `.aws` directory, create a file named `config`.
- Open the `config` file in a text editor and add the following content:
    ```
    [default]
    region = eu-central-1
    ```
- If required, replace the region with the region you want to set as default.

## 5. Setting Up a Monthly Budget with Notifications (Optional)
- Navigate to the **Billing and Cost Management** dashboard.
- In the left navigation pane, click on **Budgets**.
- Click on **Create budget**.
- Select **Cost budget** and click **Next**.
- Enter a **Budget name** and set the **Period** to **Monthly**.
- Set your **Budgeted amount**.
- Set up email recipients to be sent when your actual or forecasted costs exceed a certain percentage of your budget.
- Review your settings, and then click **Create budget**.
