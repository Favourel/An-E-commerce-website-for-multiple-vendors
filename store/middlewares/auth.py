from django.shortcuts import render, redirect, HttpResponseRedirect


def LogoutCheckMiddleware(get_response):
    def middleware(request):
        if request.user.is_authenticated:
            return redirect('profile')

        return get_response(request)

    return middleware
