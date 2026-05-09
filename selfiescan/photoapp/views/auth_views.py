# from allauth.account.views import SignupView
# from django.utils.decorators import method_decorator
# from django_ratelimit.decorators import ratelimit

# @method_decorator(
#     ratelimit(
#         key="ip",
#         rate="5/h",
#         method="POST",
#         block=True,
#     ),
#     name="dispatch",
# )
# class RateLimitedSignupView(SignupView):
#     def dispatch(self, request, *args, **kwargs):

#         print("REMOTE_ADDR:", request.META.get("REMOTE_ADDR"))
#         print("X_FORWARDED_FOR:", request.META.get("HTTP_X_FORWARDED_FOR"))

#         return super().dispatch(request, *args, **kwargs)

