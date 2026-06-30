# 🚀 Step-by-Step Guide: Setting Up Google Cloud APIs & Authentication

## Part 1: Project Creation & Billing Activation
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. If you haven't already, sign up for Google Cloud by completing the setup (entering your billing address, payment method, etc.).
3. Create a **new project** using the project dropdown menu located at the top of the screen.
4. Ensure that this newly created project is **actively selected** in the top navigation bar.

## Part 2: Create a Service Account
1. Click the **Navigation Menu** (the three horizontal lines) in the top-left corner.
2. Go to **IAM & Admin** ➔ **Service Accounts**.
3. Click the **+ Create Service Account** button at the top.
4. Enter a suitable name (e.g., `Live-Translation`) and a brief description. Click **Create and continue**.
5. Assign the following roles (permissions) to the account:
   * **Cloud Speech Client**
   * **Cloud Translation API User**
6. Click **Continue** and then click **Done**.

## Part 3: Adjust Organization Policies
> *Note: This step ensures that Google does not block the creation and usage of service account keys in your project.*

### 3a: Grant yourself the required Organization roles first
Before you can edit Organization Policies, your user account needs the correct permissions at the **Organization** level (not just the project level).

1. In the top navigation bar, open the project dropdown and select your **Organization** (the root node above all projects).
2. Go to **IAM & Admin** ➔ **IAM**.
3. Assign the following two roles to the Principal (your user account):
   * **Organization Administrator**
   * **Organization Policy Administrator**
4. Click **Save**.

> *After saving, it may take a moment for the permissions to propagate. Switch back to your project before continuing.*

### 3b: Edit the Organization Policies
1. Make sure your **project** (not the organization) is selected in the top navigation bar.
2. In the left-hand menu, click on **Organization Policies**.
2. Type `iam.disableServiceAccountKeyCreation` into the filter search bar.
3. You will see two results. Perform the following steps for **each of the two entries**:
   * Click the three dots (**Actions**) on the right side of the row and select **Edit Policy**.
   * Under Policy source, select **Override parent's policy**.
   * Click **Add a rule**.
   * Set **Enforcement** to **Off**.
   * Click **Done**, and then click **Set Policy** at the bottom.

## Part 4: Enable the Required Google APIs
1. Open the main menu in the top-left corner again and navigate to **APIs & Services** ➔ **Library**.
2. Use the search bar to find the following three APIs one by one, and click the blue **Enable** button for each:
   * **Cloud Translation API**
   * **Cloud Speech-to-Text API**
   * **Cloud Text-to-Speech API**

## Part 5: Generate & Download the JSON Key
1. Go back to the main menu and navigate to **IAM & Admin** ➔ **Service Accounts**.
2. Click on your newly created service account (`Live-Translation`) from the list.
3. Switch to the **Keys** tab at the top.
4. Click the **Add Key** dropdown and choose **Create new key**.
5. Select **JSON** as the key type and click **Create**.
6. The `.json` credentials file will be automatically downloaded to your computer.

---

### 🎉 All Done!
You can now reference this downloaded JSON file under the "Google" provider settings within your live translation service.