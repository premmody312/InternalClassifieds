from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django import forms
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from django.template.defaulttags import register
from .models import User, Listings, Category, WatchList, Comments, Bet, AdminDecision, VisibleDecision
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
import re
from textblob import TextBlob
from django.db.models import Q
# New filter for count category
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


# Class for create listing form
class CreateListing(forms.Form):
    title = forms.CharField(label="", max_length=64, widget=forms.TextInput(attrs={"placeholder": "Title",
                                                                                   "class": "form-control"}))

    text = forms.CharField(label="", widget=forms.Textarea(attrs={"placeholder": "Text",
                                                                  "class": "form-control"}))

    price = forms.FloatField(label="", min_value=0, widget=forms.NumberInput(attrs={"placeholder": "Price",
                                                                                    "class": "form-control"}))
    url = forms.URLField(label="", required=False,
                         widget=forms.URLInput(attrs={"placeholder": "URL for image", "class": "form-control"}))

    category = forms.MultipleChoiceField(label="", required=False,
                                         choices=[(choice.id, choice.cat) for choice in Category.objects.all()],
                                         widget=forms.SelectMultiple(attrs={"class": "form-control"}))
    is_comment_disabled = forms.BooleanField(label='Do you want to disable comments on your post:', label_suffix = "",
                                  required = False,  disabled = False,
                                  widget=forms.widgets.CheckboxInput(attrs={'class': 'checkbox-inline'}),
                                  help_text = "Do you want to disable comments on your post"
                                  )


# Class for add comment in listing page
class AddComment(forms.Form):
    text = forms.CharField(label="", widget=forms.Textarea(attrs={'rows': 6,
                                                                  "placeholder": "Text comment",
                                                                  "class": "form-control addComment col-24"}))


# Class for set bid in listing page
class SetBet(forms.Form):
    bet = forms.FloatField(label="", widget=forms.NumberInput(attrs={"placeholder": "Quotation",
                                                                     "class": "form-control col-6 bet"}))


# Function for pagination
def pag(request, all_listings, count_listings):
    page_number = request.GET.get("page", 1)
    paginator = Paginator(all_listings, count_listings)
    page = paginator.get_page(page_number)

    is_paginated = page.has_other_pages()

    if page.has_previous():
        prev_url = f"?page={page.previous_page_number()}"
    else:
        prev_url = ""

    if page.has_next():
        next_url = f"?page={page.next_page_number()}"
    else:
        next_url = ""

    return page, is_paginated, prev_url, next_url


# Function for index
def index(request):
    # Get all open listings
    all_open_listings = Listings.objects.filter(open=True,is_approved=True,is_visible=True)
    # Paginate
    page_list = pag(request, all_open_listings, 3)
    # For active navigation button
    active = "index"
    # If the user is not logged in
    if not request.user.is_authenticated:
        return render(request, "internalclassifieds/index.html", {
            "page_objects": page_list[0], "is_paginated": page_list[1], "next_url": page_list[3],
            "prev_url": page_list[2], "active": active
        })
    else:
        # List for watched lists
        ls = [a.id_listing for a in WatchList.objects.filter(id_user=request.user)]

        return render(request, "internalclassifieds/index.html", {
            "page_objects": page_list[0], "count": len(WatchList.objects.filter(id_user=request.user)),
            "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2], "active": active,
            "count_win": len(Listings.objects.filter(win=request.user)), "ls": ls
        })


# Login function
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            #Logic for admin page
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            active = "login"
            return render(request, "internalclassifieds/login.html", {
                "message": "Invalid username and/or password.", "active": active
            })
    else:
        active = "login"
        return render(request, "internalclassifieds/login.html", {"active": active})


# Logout function
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


# Register function
def register(request):
    if request.method == "POST":
        #Regex Validation
        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
      
        # compiling regex
        compileReg = re.compile(reg)


        username = request.POST["username"]
        fname = request.POST["fname"]
        lname = request.POST["lname"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]


        pwdcondn = re.search(compileReg, password)
      

        if password != confirmation:
            active = "register"
            return render(request, "internalclassifieds/register.html", {
                "message": "Passwords must match.", "active": active
            })
        elif not pwdcondn:
            active = "register"
            return render(request, "internalclassifieds/register.html", {
                "message1": "Atleast 6 Characters.","message2":" Atleast One Uppercase | Atleast One Lowercase | Atleast One Special Character | Atleast One Digit.", "active": active
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username,email, password, first_name=fname,last_name=lname)
            user.save()
        except IntegrityError:
            active = "register"
            return render(request, "internalclassifieds/register.html", {
                "message": "Username already taken.", "active": active
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        active = "register"
        return render(request, "internalclassifieds/register.html", {"active": active})


@login_required
def create(request):
    if request.method == "POST":
        # Get form data
        form = CreateListing(request.POST)
        if form.is_valid():
            # If the URL is not specified, then we use the default
            if not form.cleaned_data["url"]:
                url = "https://www.designthenewbusiness.com/wp-content/uploads/2011/09/moving_box1.jpg"
            else:
                url = form.cleaned_data["url"]
            new_listing = Listings(title=form.cleaned_data["title"], text_base=form.cleaned_data["text"],
                                   start_bid=form.cleaned_data["price"], url_img=url,is_comments_enabled=not (form.cleaned_data["is_comment_disabled"]),
                                   author=request.user)
            new_listing.save()
            # We set the maximum bid equal to the starting one
            # and add it to the list of watched for the author of the list
            new_listing.set_max_bet(new_listing.start_bid)
            # new_listing.add_win_list(request.user)
            new_listing.save()
            # If the category is not specified, then set by default
            if not form.cleaned_data["category"]:
                category = [16]
            else:
                category = form.cleaned_data["category"]
            new_listing.category.set(Category.objects.filter(pk__in=category))

            return HttpResponseRedirect(reverse("listings", args=[new_listing.id]))
    else:
        # Method "GET"
        active = "create"
        return render(request, "internalclassifieds/create.html", {
            "form": CreateListing(), "count": len(WatchList.objects.filter(id_user=request.user)), "active": active,
            "count_win": len(Listings.objects.filter(win=request.user))
        })


# Function for list categories
def all_categories(request):
    # Get all categories
    all_cat = Category.objects.all()
    # Paginate
    page_list = pag(request, all_cat, 5)
    # We form a dictionary for the number of lists in each category that are not yet closed
    open_watch = {}
    for a in all_cat:
        open_watch[a.cat] = len(a.category.filter(open=True,is_approved=True,is_visible=True))
    # For active navigation button
    active = "allCategories"
    if request.user.is_authenticated:
        return render(request, "internalclassifieds/allCategories.html", {
            "page_objects": page_list[0], "count": len(WatchList.objects.filter(id_user=request.user)),
            "active": active,
            "openWatch": open_watch, "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2],
            "count_win": len(Listings.objects.filter(win=request.user))
        })
    return render(request, "internalclassifieds/allCategories.html", {
        "page_objects": page_list[0], "active": active, "openWatch": open_watch, "is_paginated": page_list[1],
        "next_url": page_list[3],
        "prev_url": page_list[2]
    })


# Function for a list of one category
def categories(request, title_cat):
    # Get selected category
    cat = Category.objects.get(cat=title_cat)
    # Get all open listings in a given category
    all_cat = Listings.objects.filter(category=cat, open=True,is_approved=True,is_visible=True)
    # Paginate
    page_list = pag(request, all_cat, 3)

    if request.user.is_authenticated:
        # Generating a list of watched lists
        ls = [a.id_listing for a in WatchList.objects.filter(id_user=request.user)]
        return render(request, "internalclassifieds/categories_list.html", {
            "page_objects": page_list[0], "count": len(WatchList.objects.filter(id_user=request.user)),
            "title_cat": title_cat, "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2],
            "ls": ls, "count_win": len(Listings.objects.filter(win=request.user))
        })
    return render(request, "internalclassifieds/categories_list.html", {
        "page_objects": page_list[0], "title_cat": title_cat, "is_paginated": page_list[1], "next_url": page_list[3],
        "prev_url": page_list[2]
    })


def listings(request, id_listing):
    # Get listing
    listing = Listings.objects.get(id=id_listing)

    # Get comments for listing
    list_comments = Comments.objects.filter(id_listing=id_listing)
    # Get bet for listing
    list_bet = Bet.objects.filter(id_listing=id_listing)

    if request.user.is_authenticated:
        # Checking the list of watched
        delete = WatchList.objects.filter(id_listing=id_listing, id_user=request.user)
        # Forms for comments and bet
        form = AddComment()
        form_bet = SetBet()
        # Check if the user has made a bid
        # The user can only place 1 bet. Can comment many times
        check_bet_user = Bet.objects.filter(id_listing=id_listing, id_user=request.user)

        return render(request, "internalclassifieds/listing.html", {
            "listing": listing, "count": len(WatchList.objects.filter(id_user=request.user)), "del": delete,
            "listComments": list_comments, "form": form,
            "checkBetUser": check_bet_user, "formBet": form_bet, "countListBet": len(list_bet),
            "count_win": len(Listings.objects.filter(win=request.user))
        })
    return render(request, "internalclassifieds/listing.html", {
        "listing": listing, "listComments": list_comments
    })


# Function for watchlist
@login_required
def watchlist(request):
    # Get watchlist for user
    watchlist_user = WatchList.objects.filter(id_user=request.user) 
    #print(watchlist_user)
    page_list = pag(request, watchlist_user, 3)
    #print("----------------------------------------------------")

    active = "watchlist"
    ls = [a.id_listing for a in WatchList.objects.filter(id_user=request.user)]
    #print(ls)
    return render(request, "internalclassifieds/watchlist.html", {
        "page_objects": page_list[0], "count": len(ls),
        "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2], "ls": ls,
        "active": active, "count_win": len(Listings.objects.filter(win=request.user))
    })


# The function of adding or removing from the tracked list
def add_remove_watchlist(request, id_listing):
    if len(WatchList.objects.filter(id_listing=id_listing, id_user=request.user)) == 0:
        WatchList(id_user=request.user, id_listing=Listings.objects.get(id=id_listing)).save()
    else:
        WatchList.objects.filter(id_listing=id_listing, id_user=request.user).delete()


# Three functions for adding or removing. Applied two routes due to returning to different pages
@login_required
def watchlist_index(request, id_listing):
    if request.method == "POST":
        add_remove_watchlist(request, id_listing)
        return HttpResponseRedirect(reverse("index"))


@login_required
def watchlist_listing(request, id_listing):
    if request.method == "POST":
        add_remove_watchlist(request, id_listing)
        return HttpResponseRedirect(reverse("listings", args=[id_listing]))


@login_required
def watchlist_watchlist(request, id_listing):
    if request.method == "POST":
        add_remove_watchlist(request, id_listing)
        return HttpResponseRedirect(reverse("watchlist"))


# Function for add comments
@login_required
def add_comment(request, id_listing):
    if request.method == "POST":
        form = AddComment(request.POST)
        score=TextBlob(form["text"].value()).sentiment.polarity
        sentText=""
        if score==0:
            sentText="Neutral"
        elif score<0:
            sentText="Negative"
        else:
            sentText="Positive"
        listing = Listings.objects.get(id=id_listing)
        
        if form.is_valid():
            comment = Comments(id_listing=listing, id_user=request.user, text=form.cleaned_data["text"],senttext=sentText)
            comment.save()
            listing = Listings.objects.get(id=id_listing)
            author_id=listing.author_id
            emailofUser=User.objects.get(id=author_id).email
            send_mail(
            'Internal Classifieds - You have a comment on your Posting',
            'Hi, your item posted to Internal Classifieds has a comment posted by another user. Please respond to the query raised, it helps the buyer choose quicker and better.',
            settings.EMAIL_HOST_USER,
            [emailofUser],
            fail_silently=False,
            )
            return HttpResponseRedirect(reverse("listings", args=[id_listing]))
            
# Function for add bet
@login_required
def add_bet(request, id_listing):
    if request.method == "POST":
        # Get data form
        form = SetBet(request.POST)
        # Get listing
        listing = Listings.objects.get(id=id_listing)

        if form.is_valid():
            # If there are no bets yet, then the new bet can be equal to the starting one.
            if not Bet.objects.filter(id_listing=id_listing) and form.cleaned_data["bet"] < listing.start_bid:
                messages.warning(request, "The rate must not be less than the starting price!", extra_tags="danger")
                return HttpResponseRedirect(reverse("listings", args=[id_listing]))
            # If there are already bids, then the new bid must be greater than the maximum
            if Bet.objects.filter(id_listing=id_listing) and form.cleaned_data["bet"] <= listing.max_bet:
                messages.warning(request, f"The rate must not be less than other rates! Closest value: "
                                          f"${round(listing.max_bet + 0.01, 2)}.", extra_tags="danger")
                return HttpResponseRedirect(reverse("listings", args=[id_listing]))
            # Save the bid for the current list and update the maximum bid field in the list
            new_bet = Bet(id_listing=listing, id_user=request.user, newBet=round(form.cleaned_data["bet"], 2))
            new_bet.save()
            listing.max_bet = round(form.cleaned_data["bet"], 2)
            # If the list is not tracked, then add it to the tracked list
            if len(listing.listing.filter(id_user=request.user)) == 0:
                listing.add_win_list(request.user)
            listing.save()
            return HttpResponseRedirect(reverse("listings", args=[id_listing]))

        messages.warning(request, "Wrong data!", extra_tags="danger")
        return HttpResponseRedirect(reverse("listings", args=[id_listing]))


# Function close auction
@login_required
def close_auction(request, id_listing):
    if request.method == "POST":
        get_listing = Listings.objects.get(id=id_listing)
        if Bet.objects.filter(id_listing=id_listing):
            list_bet = Bet.objects.filter(id_listing=id_listing).aggregate(Max('newBet'))
            user_win_id = Bet.objects.get(id_listing=id_listing, newBet=list_bet["newBet__max"])
            get_listing.win = User.objects.get(id=user_win_id.id_user.id)
            get_listing.open = False
            get_listing.save()
            return HttpResponseRedirect(reverse("listings", args=[id_listing]))
        get_listing.open = False
        get_listing.save()

        return HttpResponseRedirect(reverse("listings", args=[id_listing]))


# Function for winlist
@login_required
def win_list(request):
    get_win_listings = Listings.objects.filter(win=request.user)

    page_list = pag(request, get_win_listings, 3)

    active = "winlist"
    ls = [a.id_listing for a in WatchList.objects.filter(id_user=request.user)]
    return render(request, "internalclassifieds/winlist.html", {
        "page_objects": page_list[0], "count": len(WatchList.objects.filter(id_user=request.user)),
        "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2], "ls": ls,
        "active": active, "count_win": len(Listings.objects.filter(win=request.user))
    })
from django.shortcuts import render

# Create your views here.
@login_required
def admin_decision(request):
    # Get watchlist for user
    #watchlist_admin_user = AdminDecision.objects.filter(id_user=request.user)
    lists= Listings.objects.filter(is_approved=False)
    page_list = pag(request, lists, 3)
    active = "admin_decision"
    ls = [a for a in lists]
    return render(request, "internalclassifieds/admin_decision_page.html", {
        "page_objects": page_list[0], "count": len(ls),
        "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2], "ls": ls,
        "active": active, "count_win": len(Listings.objects.filter(win=request.user))
    })



# Three functions for adding or removing. Applied two routes due to returning to different pages
@login_required
def admin_decision_index(request, id_listing):
    if request.method == "POST":
        id_listing=Listings.objects.get(id=id_listing)
        id_listing.delete()
        author_id=id_listing.author_id
        emailofUser=User.objects.get(id=author_id).email

        # Mail if rejected
        send_mail(
            'Internal Classifieds - Sorry, your item posting has been rejected',
            'Hi, your item posted to Internal Classifieds has been verified and rejected based on one of the following reasons. \n1)Incomplete Information \n2)Improper image.\nHence, it has be removed from the site, please re-upload the posting with the necessary changes.',
            settings.EMAIL_HOST_USER,
            [emailofUser],
            fail_silently=False,
        )
        return HttpResponseRedirect(reverse("admin_decision"))


@login_required
def admin_decision_listing(request, id_listing):
    if request.method == "POST":
        return HttpResponseRedirect(reverse("listings", args=[id_listing]))


@login_required
def admin_decision_watchlist(request, id_listing):
    if request.method == "POST":
        id_listing=Listings.objects.get(id=id_listing)
        id_listing.is_approved=True
        id_listing.save(update_fields=['is_approved'])
        # Mail if accepted
        id=id_listing.id
        author_id=id_listing.author_id
        tmp=User.objects.get(id=author_id)
        VisibleDecision(id_user=tmp, id_listing=id_listing).save()
        emailofUser=User.objects.get(id=author_id).email
        # print("---------------------------------------------------------------------")
        # print(emailofUser)
        # print("---------------------------------------------------------------------")

        send_mail(
            'Internal Classifieds - Congratulations, your item posting has been accepted',
            'Hi, your item posted to Internal Classifieds has been verified and found to be authentic. Hence, it has be posted to the site, please keep an eye out for the bids and bets.',
            settings.EMAIL_HOST_USER,
            [emailofUser],
            fail_silently=False,
        )
        return HttpResponseRedirect(reverse("admin_decision"))


@login_required
def visible_decision(request):
    visiblelist_user = VisibleDecision.objects.filter(id_user=request.user)
    # print(watchlist_user)
    page_list = pag(request, visiblelist_user, 3)
    # print("----------------------------------------------------")

    active = "visible_decision"
    ls = [a.id_listing for a in VisibleDecision.objects.filter(id_user=request.user)]
    # print(ls)
    return render(request, "internalclassifieds/visible_decision_page.html", {
        "page_objects": page_list[0], "count": len(VisibleDecision.objects.filter(id_user=request.user)),
        "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2], "ls": ls,
        "active": active, "count_win": len(Listings.objects.filter(win=request.user))
    })



# Three functions for adding or removing. Applied two routes due to returning to different pages
@login_required
def visible_decision_index(request, id_listing):
    if request.method == "POST":
        id_listing=Listings.objects.get(id=id_listing)
        id_listing.is_visible=False
        id_listing.save(update_fields=['is_visible'])
        # Mail if accepted
        return HttpResponseRedirect(reverse("visible_decision"))


@login_required
def visible_decision_listing(request, id_listing):
    if request.method == "POST":
        return HttpResponseRedirect(reverse("listings", args=[id_listing]))


@login_required
def visible_decision_watchlist(request, id_listing):
    if request.method == "POST":
        id_listing=Listings.objects.get(id=id_listing)
        id_listing.is_visible=True
        id_listing.save(update_fields=['is_visible'])
        # Mail if accepted
        return HttpResponseRedirect(reverse("visible_decision"))


# Create your views here.
@login_required
def admin_delete(request):
    # Get watchlist for user
    #watchlist_admin_user = AdminDecision.objects.filter(id_user=request.user)
    lists= Listings.objects.filter(open=True)
    page_list = pag(request, lists, 3)
    active = "admin_delete"
    ls = [a for a in lists]
    return render(request, "internalclassifieds/admin_delete_page.html", {
        "page_objects": page_list[0], "count": len(ls),
        "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2], "ls": ls,
        "active": active, "count_win": len(Listings.objects.filter(win=request.user))
    })



# Three functions for adding or removing. Applied two routes due to returning to different pages
@login_required
def admin_delete_index(request, id_listing):
    if request.method == "POST":
        id_listing=Listings.objects.get(id=id_listing)
        id_listing.delete()

        author_id=id_listing.author_id
        emailofUser=User.objects.get(id=author_id).email
        print(emailofUser)
        #Mail if Deleted
        send_mail(
            'Internal Classifieds - Sorry, your item posting has been deleted',
            'Hi, your item posted to Internal Classifieds has been verified and deleted as it violates our terms and conditions.',
            settings.EMAIL_HOST_USER,
            [emailofUser],
            fail_silently=False,
        )
        print("Email Sent")
        return HttpResponseRedirect(reverse("admin_delete"))


@login_required
def admin_delete_listing(request, id_listing):
    if request.method == "POST":
        return HttpResponseRedirect(reverse("listings", args=[id_listing]))


def search(request):
    query=request.GET['query']
    if len(query)>78:
        allPosts=Listings.objects.none()
    elif len(query)==0:
        allPosts=Listings.objects.none()
    else:
        allPosts= Listings.objects.filter((Q(title__icontains=query) | Q(text_base__icontains=query)) & Q(open=True,is_approved=True,is_visible=True) )
    # if allPosts.count()==0:
    #     messages.warning(request, "No search results found. Please refine your query.")
    params={'allPosts': allPosts, 'query': query}
    page_list = pag(request, allPosts, 3)
    ls = [a for a in allPosts]
    active = "search"
    # return render(request, 'home/search.html', params)
    return render(request, "internalclassifieds/search.html", {
        "page_objects": page_list[0], "count": len(ls),
        "is_paginated": page_list[1], "next_url": page_list[3], "prev_url": page_list[2], "ls": ls,
        "active": active
    })
