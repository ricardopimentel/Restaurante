from django.shortcuts import render, redirect, resolve_url as r

# Create your views here.
def Home(request):
    try:# Verificar se usuario esta logado
        if request.session['nome']:
            return render(request, 'index.html', {'err': '', 'itemselec': 'HOME'})
    except KeyError:
        return redirect(r('Login'))