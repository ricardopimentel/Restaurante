from django import forms

from restaurante.core.libs.conexaoAD3 import conexaoAD


class ConfirmacaoVendaForm(forms.Form):
    campo_usuario = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Usuário', 'readonly':'readonly'}))
    campo_senha = forms.CharField(label="", widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))

    def __init__(self, request, *args, **kwargs):
        super(ConfirmacaoVendaForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        cleaned_data = self.cleaned_data
        campo_usuario = cleaned_data.get("campo_usuario")
        campo_senha = cleaned_data.get("campo_senha")

        c = conexaoAD(campo_usuario, campo_senha)
        result = c.Login()  # tenta login no ldap

        if (result == ('i')):  # Credenciais invalidas
            # Adiciona erro na validação do formulário
            raise forms.ValidationError("Usuário ou senha incorretos", code='invalid')
        elif (result == ('n')):  # Server Down
            # Adiciona erro na validação do formulário
            raise forms.ValidationError("Servidor AD não encontrado", code='invalid')
        elif (result == ('o')):  # Usuario fora do escopo permitido
            # Adiciona erro na validação do formulário
            raise forms.ValidationError("Usuário não tem permissão para acessar essa página", code='invalid')
        else:  # se logou
            pass

        # Sempre retorne a coleção completa de dados válidos.

        return cleaned_data