from django.shortcuts import render, redirect
from PrimeShop.models import Contact, Product, Orders, OrderUpdate
from django.contrib import messages
from math import ceil
from PrimeShop import keys
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from paytmchecksum import PaytmChecksum  # Corrected import
from PrimeShop.PayTm.Checksum import generate_checksum, verify_checksum  # Import the custom methods

MERCHANT_KEY = keys.MK

def index(request):
    """Homepage view displaying categorized products."""
    allProds = []
    try:
        catprods = Product.objects.values('category', 'product_id').distinct()
        cats = [item['category'] for item in catprods]
        for cat in cats:
            prod = Product.objects.filter(category=cat)
            n = len(prod)
            nSlides = n // 4 + (1 if n % 4 != 0 else 0)
            allProds.append([prod, range(1, nSlides + 1), nSlides])
    except Exception as e:
        messages.error(request, f"Error loading products: {e}")
    params = {'allProds': allProds}
    return render(request, "index.html", params)

def contact(request):
    """Contact page for submitting user queries."""
    if request.method == "POST":
        try:
            name = request.POST.get("name")
            email = request.POST.get("email")
            desc = request.POST.get("desc")
            pnumber = request.POST.get("pnumber")
            myquery = Contact(name=name, email=email, desc=desc, phonenumber=pnumber)
            myquery.save()
            messages.success(request, "We will get back to you soon.")
        except Exception as e:
            messages.error(request, f"Failed to submit your query: {e}")
        return render(request, "contact.html")
    return render(request, "contact.html")

def about(request):
    """About page view."""
    return render(request, "about.html")

def checkout(request):
    """Checkout page for placing an order and initiating payment."""
    if not request.user.is_authenticated:
        messages.warning(request, "Login & Try Again")
        return redirect('/auth/login')

    if request.method == "POST":
        try:
            items_json = request.POST.get('itemsJson', "")
            name = request.POST.get('name', "")
            amount = request.POST.get('amt', 0)
            email = request.POST.get('email', "")
            address1 = request.POST.get('address1', "")
            address2 = request.POST.get('address2', "")
            city = request.POST.get('city', "")
            state = request.POST.get('state', "")
            zip_code = request.POST.get('zip_code', "")
            phone = request.POST.get('phone', "")

            # Save order
            order = Orders(
                items_json=items_json,
                name=name,
                amount=amount,
                email=email,
                address1=address1,
                address2=address2,
                city=city,
                state=state,
                zip_code=zip_code,
                phone=phone
            )
            order.save()

            # Save order update
            update = OrderUpdate(
                order_id=order.order_id,
                update_desc="The order has been placed"
            )
            update.save()

            # Payment initialization
            oid = f"{order.order_id}shopycart"
            param_dict = {
                'MID': keys.MID,
                'ORDER_ID': oid,
                'TXN_AMOUNT': str(amount),
                'CUST_ID': email,
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'WEBSTAGING',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL': 'http://127.0.0.1:8000/handLerequest/',
            }
            param_dict['CHECKSUMHASH'] = generate_checksum(param_dict, MERCHANT_KEY)  # Custom checksum

            return render(request, 'paytm.html', {'param_dict': param_dict})

        except Exception as e:
            messages.error(request, f"Error processing your order: {e}")
            return redirect('checkout')

    return render(request, "checkout.html")

@csrf_exempt
def handlerequest(request):
    """Handle Paytm's asynchronous callback."""
    if request.method == "POST":
        try:
            # Parse the Paytm response into a dictionary
            response_dict = {key: value for key, value in request.POST.items()}

            # Extract checksum from the response
            checksum = response_dict.get('CHECKSUMHASH')

            # Verify the checksum
            verify = verify_checksum(response_dict, MERCHANT_KEY, checksum)

            if verify:
                if response_dict.get('RESPCODE') == '01':
                    print('Order successful')

                    order_id = response_dict.get('ORDERID', '')
                    txn_amount = response_dict.get('TXNAMOUNT', '')

                    # Process the order ID to remove any specific prefix
                    rid = order_id.replace("shopycart", "")
                    print("Processed Order ID:", rid)

                    # Fetch the order from the database
                    filter2 = Orders.objects.filter(order_id=rid)
                    print("Fetched Orders:", filter2)

                    # Update the order details
                    for post1 in filter2:
                        post1.oid = order_id
                        post1.amountpaid = txn_amount
                        post1.paymentstatus = "PAID"
                        post1.save()
                        print("Order updated successfully")
                else:
                    print("Order was not successful because:", response_dict.get('RESPMSG', ''))
            else:
                print("Checksum verification failed")

            return render(request, 'paymentstatus.html', {'response': response_dict})
        
        except Exception as e:
            print(f"Error handling payment: {e}")
            return render(request, 'paymentstatus.html', {'response': {"error": str(e)}})
    else:
        return render(request, 'paymentstatus.html', {'response': {"error": "Invalid request method"}})

def profile(request):
    """User profile view to display order history and status."""
    if not request.user.is_authenticated:
        messages.warning(request, "Login & Try Again")
        return redirect("/auth/login")

    currentuser = request.user.username
    items = Orders.objects.filter(email=currentuser)
    rid = ""

    for i in items:
        print(i.oid)
        print(i.order_id)
        myid = i.oid
        if myid:  # Ensure oid is not None
            rid = myid.replace("ShopyCart", "")

    print("Value of rid before conversion:", rid)

    if rid.isdigit():  # Ensure rid is a valid integer string
        try:
            status = OrderUpdate.objects.filter(order_id=int(rid))
        except ValueError as e:
            print(f"Error converting rid to integer: {e}")
            status = []
    else:
        print("Invalid order ID:", rid)
        status = []  # Fallback for invalid `rid`

    context = {"items": items, "status": status}
    if status:  # Ensure status list is not empty
        for j in status:
            print(j.update_desc)
            print(j.delivered)
            print(j.timestamp)
            context.update({"msg": j.update_desc})
            context.update({"dstatus": "Delivered" if "delivered" in j.update_desc.lower() else "In Progress"})
            context.update({"timestamp": j.timestamp})
    else:
        context.update({"msg": "No updates available", "dstatus": "Pending", "timestamp": None})

    print(context)

    return render(request, "profile.html", context)
