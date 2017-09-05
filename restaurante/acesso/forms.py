# -*- coding: utf-8 -*-

from django import forms
from restaurante.core.libs.conexaoAD3 import conexaoAD

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
                result = eval(ret)
                print(result)
                # Verificar se usuário é servidor ou aluno
                if(ret.find(str('G_PSO_SERVIDORES')) > -1):
                    self.request.session['usertip'] = 'admin'
                    # Preparar menu admin
                    self.request.session['menu'] = ['logo', 'HOME', 'RELATÓRIOS', 'ADMINISTRAÇÃO', 'AJUDA', 'sair']
                    self.request.session['url'] = ['restaurante/', 'restaurante/', 'restaurante/relatorios/', 'restaurante/administracao', 'restaurante/', '']
                    self.request.session['img'] = ['if.png', 'home24.png', 'relatorio24.png', 'admin24.png', 'ajuda24.png', '']
                    #logou então, adicionar os dados do usuário na sessão
                    self.request.session['userl'] = usuario
                    self.request.session['nome'] = result['displayName'].title()
                    
                elif(ret.find(str('G_PARAISO_DO_TOCANTINS_ALUNOS')) > -1):
                    self.request.session['usertip'] = 'aluno'
                    # Preparar menu user
                    self.request.session['menu'] = ['HOME']
                    self.request.session['url'] = ['restaurante/']
                    self.request.session['img'] = ['home24.png']
                    #logou então, adicionar os dados do usuário na sessão
                    self.request.session['userl'] = usuario
                    self.request.session['nome'] = result['displayName'].title()
                    try:
                        self.request.session['mail'] = result['mail']
                    except KeyError:
                        self.request.session['mail'] = 'Não informado'
                    self.request.session['curso'] = result['description']
                    
                
        # Sempre retorne a coleção completa de dados válidos.
        return cleaned_data