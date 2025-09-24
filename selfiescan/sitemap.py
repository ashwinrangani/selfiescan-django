from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from photoapp.models import Photo
from blog.models import Blog

class EventSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        from photoapp.models import Event   # import your Event model
        return Event.objects.all()

    def lastmod(self, obj):
        return obj.date   # replace with your actual field name

    def location(self, obj):
        return reverse("event_detail", args=[obj.event_id])   # obj.id is UUID


class BlogSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Blog.objects.all()

    def lastmod(self, obj):
        return obj.published_at

    def location(self, obj):
        return reverse("public-blog-detail", args=[obj.pk])


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return ["homepage", "about-us", "privacy-policy", "terms-of-service", "cancellation-refund-policy", "contact-us"]

    def location(self, item):
        return reverse(item)

    

sitemaps = {
    "photos": EventSitemap,
    "blogs": BlogSitemap,
    "static": StaticViewSitemap,
}
