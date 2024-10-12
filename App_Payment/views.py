from django.shortcuts import render,HttpResponseRedirect,redirect
from django.urls import reverse
from django.contrib import messages

from App_Order.models import Order ,Cart
from App_Payment.models  import BillingAddress
from App_Payment.forms  import BillingForm

from django.contrib.auth.decorators import login_required

#for payment
import requests
from sslcommerz_python.payment import SSLCSession
from decimal import Decimal
import socket

# thje follwing impoert is for not checking csrf token when we are doing payment
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@login_required
def checkout(request):
    saved_address = BillingAddress.objects.get_or_create(user=request.user)
    saved_address = saved_address[0]
    print(saved_address)
    form = BillingForm(instance=saved_address)
    if request.method == 'POST':
        form = BillingForm(request.POST, instance=saved_address)
        if form.is_valid():
            form.save()
            form = BillingForm(instance=saved_address)
            messages.success(request,f"Shippping Address is saved")
    order_qs = Order.objects.filter(user= request.user, ordered= False)
    print(order_qs)
    order_items = order_qs[0].orderitems.all()
    print(order_items)
    order_total = order_qs[0].get_totals()
    print(order_total)

    dict={'form':form,
          'order_items':order_items,
          'order_total':order_total,
          'saved_address':saved_address,}
    return render(request,'App_Payment/checkout.html',context=dict)



@login_required
def payment(request):
    saved_address = BillingAddress.objects.get_or_create(user=request.user)
    saved_address = saved_address[0]

    if not saved_address.is_fully_filled():
        messages.info(request,f"Please complete shipping Adress!")
        return redirect("App_Payment:checkout")
    
    if not request.user.profile.is_fully_filled():
        messages.info(request,f"Please complete profile details")
        return redirect("App_Login:profile")
    
    store_id='abc64f2c0846f5ba'
    api_key='abc64f2c0846f5ba@ssl'
    mypayment = SSLCSession(sslc_is_sandbox=True, sslc_store_id=store_id, sslc_store_pass=api_key)


    status_url = request.build_absolute_uri(reverse("App_Payment:complete"))
    print(status_url)
    mypayment.set_urls(success_url=status_url, fail_url=status_url, cancel_url=status_url, ipn_url=status_url)


    order_qs = Order.objects.filter(user= request.user, ordered= False)
    order_items = order_qs[0].orderitems.all()
    order_items_count = order_qs[0].orderitems.count()
    order_total = order_qs[0].get_totals()
    mypayment.set_product_integration(total_amount=Decimal( order_total), currency='BDT', product_category='Mixed', product_name=order_items, num_of_item=order_items_count, shipping_method='Courier', product_profile='None')

    current_user = request.user
    mypayment.set_customer_info(name=current_user.profile.full_name, email=current_user.email, address1=current_user.profile.address_1, address2=current_user.profile.address_1, city=current_user.profile.city, postcode=current_user.profile.zipcode, country=current_user.profile.country, phone=current_user.profile.phone)

    mypayment.set_shipping_info(shipping_to=current_user.profile.full_name, address=saved_address.address, city=saved_address.city, postcode=saved_address.zipcode, country=saved_address.country)

    response_data = mypayment.init_payment()
    print(response_data)
    dict={}
    return redirect(response_data['GatewayPageURL'])


@csrf_exempt
def complete(request):
    if request.method == 'POST' or request.method == 'post':
        payment_data = request.POST
        print(payment_data)
        status = payment_data['status']
        if status == 'VALID':
            messages.success(request,f"Your payment Completed succesfully !! Page will be redirected")
            val_id = payment_data['val_id']
            tran_id = payment_data['tran_id']
            return HttpResponseRedirect(reverse('App_Payment:purchase',kwargs={'val_id':val_id,'tran_id':tran_id}))
        else:
            messages.warning(request,f"Your payment Failed. Try Again!! Page will be redirected")
        
    dict={}
    return render(request,"App_Payment/complete.html",context=dict)


@login_required
def purchase(request,val_id,tran_id):
    order_qs = Order.objects.filter(user= request.user, ordered= False)
    order = order_qs[0]
    orderId = tran_id
    order.ordered = True
    order.orderId = orderId
    order.paymentId = val_id
    order.save()
    cart_items = Cart.objects.filter(user= request.user, purchased= False)
    for item in cart_items:
        item.purchased = True
        item.save()
    return HttpResponseRedirect(reverse('App_Shop:home'))


@login_required
def order_view(request):
    try:
        orders = Order.objects.filter(user=request.user, ordered = True)
    except:
        messages.warning(request,"You don't have an active order")
        return redirect("App_Shop:home")
    dict={'orders':orders}
    return render(request,"App_Payment/order.html",context=dict)
