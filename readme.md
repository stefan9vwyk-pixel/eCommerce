# eCommere app
This is a basic eCommerce project with two apps:

**store_front** - Handles the login and registration of users. Also handles password resets and the sending of password reset emails.

**shopperz** - This is the main store part. This is where *Buyers* can view stores and products, add products to their cart, manage
their cart and checkout their cart. *Vendors* can add, view, update and delete their own stores and products.

## Table of Contents
- [Installation](#Installation)
- [Running the Project](#running-the-project)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

## Installation

1. Clone the repository to your computer.
2. Once the repository is on your system, navigate to the directory of the appplication.
 ```
 cd "your_path/eCommerce app"
 ```
3. Create and activate the virtual enviroment.
   - On Windows :
```
python -m venv venv-name
venv-name/Scripts/activate
```
  - On macOS/Linux :
```
python3 -m vanv venv-name
source venv-name/bin/activate
```
4. Install the requirements.txt
```
pip install -r requiremnets.txt
```

## Running the Project

1. Once the virtual enviroment is created and requirements are installed, its time to run the project.
2. In your terminal navigate to eCommerce app.
```
cd "your_path/eCommerce app/eCommerce"
```
3. Migrate the Database.
```
python manage.py makemigrations
python manage.py migrate
```
4. Run the server:
```
python manage.py runserver
```
5. Copy the link (usually looks like: `http://127.0.0.1:8000/`) and enter into browser.

## Usage
1. **store_front**:
   - Create user account and choose between 'Vendors' or 'Buyers' group.
   - Login to account, Vendors and Buyers will be met with welcome page with links depending on their account type.
   - Reset password emails are set to `FILEBASED`, the **emails** directory contain all emails sent.
     (Please see troubleshooting section in readme for email troubleshooting)
   - Follow the link in the emails to reset password.
2. **shopperz**:
   Buyers:
    - Can view the product list as well as the product page of each product.
    - Can add product to their cart and remove them form the cart or clear the cart completely.
    - They can checkout their cart, upon checkout an email will be sent to their email with an invoice of their purchase.
    - They can also leave reviews on the product page of each product
    - Reviews are `Verified` or `Unverified` depending on if a Buyer has bought the product or not.
   Vendors:
    - Have an Vendor Dashboard where they can add, view, update and delete their stores.
    - They can view the products in each store, which is also where they can add new products and update or delete existing ones.

## Troubleshooting
Password reset troubleshooting:

When the app sends an email with the password reset link, the link is split with an equal sign `=`.

In a normal email link this is normal as the equal is ignored when you click the link, but as I set the emails to `FILEBASED`
when you simply copy and paste the link it does not work.

Just remove the equal in the link, then the link will work normally. 

I researched this problem extensively but could not find a fix besides just manually removing the equal sign. 
