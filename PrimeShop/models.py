from django.db import models

# Create your models here.
class Contact(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    desc = models.TextField()  # Removed max_length for TextField
    phonenumber = models.CharField(max_length=15)  # Changed to CharField for phone numbers

    def __str__(self):
        return self.name


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)  
    product_name = models.CharField(max_length=100)  
    category = models.CharField(max_length=100, default="General")  # Changed default
    subcategory = models.CharField(max_length=50, default="None")  # Changed default
    price = models.IntegerField(default=0)  
    desc = models.CharField(max_length=300) 
    image = models.ImageField(upload_to='images/images')  # The path for saving images

    def __str__(self):  
        return self.product_name

class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    items_json = models.CharField(max_length=5000)
    amount = models.IntegerField(default=0)  # Assuming 'e' is a typo, you can adjust it to the correct default value
    name = models.CharField(max_length=90)
    email = models.CharField(max_length=90)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=100)
    oid = models.CharField(max_length=50, blank=True)
    amountpaid = models.CharField(max_length=500, blank=True, null=True)
    paymentstatus = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=100, default="")  # Corrected max_Length and added a proper default value

    def _str_(self): 
        return self.name

class OrderUpdate(models.Model):
    update_id = models.AutoField(primary_key=True)
    order_id = models.IntegerField(default=0)  
    update_desc = models.CharField(max_length=5000)
    delivered = models.BooleanField(default=False)
    timestamp = models.DateField(auto_now_add=True)

    def _str_(self):  # Custom string representation
        return self.update_desc[0:7] + "..." if len(self.update_desc) > 7 else self.update_desc