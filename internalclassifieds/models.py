from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

    def __str__(self):
        return f"id: {self.id}, name: {self.username}"


class Category(models.Model):
    cat = models.CharField(max_length=64)

    def __str__(self):
        return f"id: {self.id}, category: {self.cat}"

    class Meta:
        ordering = ["cat"]


class Listings(models.Model):
    title = models.CharField(max_length=64)
    text_base = models.TextField()
    start_bid = models.FloatField()
    url_img = models.URLField()
    category = models.ManyToManyField(Category, related_name="category")
    create_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author")
    open = models.BooleanField(default=True)
    max_bet = models.FloatField(default=0)
    win = models.ForeignKey(User, on_delete=models.CASCADE, related_name="win", null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    is_comments_enabled=models.BooleanField(default=True)

    def set_max_bet(self, start_bid):
        self.max_bet = float(start_bid)

    def add_win_list(self, id_user):
        add_win_list = WatchList(id_user=id_user, id_listing=self)
        add_win_list.save()

    def __str__(self):
        return f"id: {self.id}, title: {self.title} text_base: {self.text_base} start_bid: {self.start_bid} " \
               f"url_img: {self.url_img} category: {self.category} create_date: {self.create_date} " \
               f"author: {self.author} win: {self.win}"

    class Meta:
        ordering = ["-create_date"]



class WatchList(models.Model):
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    id_listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="listing")

    def __str__(self):
        return f"id_user: {self.id_user.id}, id_listing: {self.id_listing.id}"


class AdminDecision(models.Model):
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_admin_dec")
    id_listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="listing_admin_dec")

    def __str__(self):
        return f"id_user: {self.id_user.id}, id_listing: {self.id_listing.id}"


class VisibleDecision(models.Model):
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_visible_dec")
    id_listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="listing_visible_dec")

    def __str__(self):
        return f"id_user: {self.id_user.id}, id_listing: {self.id_listing.id}"

class Comments(models.Model):
    id_listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="listCom")
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userCom")
    text = models.TextField()
    senttext=models.TextField(default="Neutral")
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"id: {self.id}, id listing: {self.id_listing.id}, id user: {self.id_user.id}, text: {self.text}"

    class Meta:
        ordering = ["-create_date"]


class Bet(models.Model):
    id_listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="listBet")
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userBet")
    newBet = models.FloatField()

    def __str__(self):
        return f"id: {self.id}, id listing: {self.id_listing.id}, id user: {self.id_user.id}, newBet: {self.newBet}"
