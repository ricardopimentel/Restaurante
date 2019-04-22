from django import forms
from restaurante.core.libs.conexaoAD3 import conexaoAD
from django.shortcuts import resolve_url as r

class LoginForm(forms.Form):
    usuario = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Login'}))
    senha = forms.CharField(label="", widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))
    
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(LoginForm, self).__init__(*args, **kwargs)


    def clean(self):
        cleaned_data = self.cleaned_data
        usuario = cleaned_data.get("usuario")
        senha = cleaned_data.get("senha")
        
        if usuario and senha:
            c = conexaoAD(usuario, senha)
            result = c.Login() #tenta login no ldap

            if(result == ('i')): # Credenciais invalidas
                # Adiciona erro na validação do formulário
                raise forms.ValidationError("Usuário ou senha incorretos", code='invalid')
            elif(result == ('n')): # Server Down
                # Adiciona erro na validação do formulário
                raise forms.ValidationError("Servidor AD não encontrado", code='invalid')
            elif(result == ('o')): # Usuario fora do escopo permitido
                # Adiciona erro na validação do formulário
                raise forms.ValidationError("Usuário não tem permissão para acessar essa página", code='invalid')
            else:# se logou
                # Retirar virgulas do member of
                result['memberOf'] = str(result['memberOf']).replace(',', '')
                # Remover cabeçalhos desnecessarios 
                ret = repr(result)
                
                # Transformar em dicionario
                ret = ret.replace('[', '')
                ret = ret.replace(']', '')

                MontarMenu(self.request, ret, usuario)
        # Sempre retorne a coleção completa de dados válidos.
        return cleaned_data


def MontarMenu(request, ret, usuario):
    result = eval(ret)
    if (ret.find(str('G_PSO_CGTI_SERVIDORES')) > -1):
        request.session['usertip'] = 'admin'
        # Preparar menu admin
        request.session['menu'] = ['logo', 'HOME', 'VENDAS', 'RELATÓRIOS', 'ADMINISTRAÇÃO', 'sair']
        request.session['url'] = [r('Home').replace('/restaurante/', 'restaurante/'),
                                  r('Home').replace('/restaurante/', 'restaurante/'),
                                  r('Vendas').replace('/restaurante/', 'restaurante/'),
                                  r('Relatorios').replace('/restaurante/', 'restaurante/'),
                                  r('Administracao').replace('/restaurante/', 'restaurante/'), '']
        request.session['img'] = ['if.png', 'home24.png', 'dinheiro24b.png', 'relatorio24.png', 'admin24.png', '']
        # logou então, adicionar os dados do usuário na sessão
        request.session['userl'] = usuario
        request.session['nome'] = result['displayName'].title()
        try:
            request.session['mail'] = result['mail']
        except KeyError:
            request.session['mail'] = 'Não informado'
        try:
            request.session['phone'] = result['telephoneNumber']
        except KeyError:
            request.session['phone'] = 'Não informado'

    elif (ret.find(str('G_PSO_LANCHONETE')) > -1):
        request.session['usertip'] = 'lanchonete'
        # Preparar menu user
        request.session['menu'] = ['logo', 'HOME', 'VENDAS', 'RELATÓRIOS', 'sair']
        request.session['url'] = [r('Home').replace('/restaurante/', 'restaurante/'),
                                  r('Home').replace('/restaurante/', 'restaurante/'),
                                  r('Vendas').replace('/restaurante/', 'restaurante/'),
                                  r('Relatorios').replace('/restaurante/', 'restaurante/'), '']
        request.session['img'] = ['if.png', 'home24.png', 'dinheiro24b.png', 'relatorio24.png', '']
        # logou então, adicionar os dados do usuário na sessão
        request.session['userl'] = usuario
        request.session['nome'] = result['displayName'].title()
        try:
            request.session['mail'] = result['mail']
        except KeyError:
            request.session['mail'] = 'Não informado'
        try:
            request.session['phone'] = result['telephoneNumber']
        except KeyError:
            request.session['phone'] = 'Não informado'

    elif (ret.find(str('G_PSO_GERENCIA_LANCHONETE')) > -1):
        request.session['usertip'] = 'glanchonete'
        # Preparar menu admin
        request.session['menu'] = ['logo', 'HOME', 'RELATÓRIOS', 'sair']
        request.session['url'] = [r('Home').replace('/restaurante/', 'restaurante/'),
                                  r('Home').replace('/restaurante/', 'restaurante/'),
                                  r('Relatorios').replace('/restaurante/', 'restaurante/'), '']
        request.session['img'] = ['if.png', 'home24.png', 'relatorio24.png', '']
        # logou então, adicionar os dados do usuário na sessão
        request.session['userl'] = usuario
        request.session['nome'] = result['displayName'].title()
        try:
            request.session['mail'] = result['mail']
        except KeyError:
            request.session['mail'] = 'Não informado'
        try:
            request.session['phone'] = result['telephoneNumber']
        except KeyError:
            request.session['phone'] = 'Não informado'
