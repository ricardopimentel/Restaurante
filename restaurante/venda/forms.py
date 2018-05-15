from django import forms

from restaurante.core.libs.conexaoAD3 import conexaoAD


class ConfirmacaoVendaForm(forms.Form):
    usuario = forms.CharField(label="", max_length=20, widget=forms.HiddenInput(attrs={'placeholder': 'Login'}))
    senha = forms.CharField(label="", widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))

    def __init__(self, request, *args, **kwargs):
        super(ConfirmacaoVendaForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        cleaned_data = self.cleaned_data
        usuario = cleaned_data.get("usuario")
        senha = cleaned_data.get("senha")

        c = conexaoAD(usuario, senha)
        result = c.Login()  # tenta login no ldap

        if (result == ('i')):  # Credenciais invalidas
            # Adiciona erro na validação do formulário
            raise forms.ValidationError("Usuário ou senha incorretos", code='invalid')
        elif (result == ('n')):  # Server Down
            # Adiciona erro na validação do formulário
            raise forms.ValidationError("Servidor AD não encontrado", code='invalid')
        else:  # se logou
            pass
        # Sempre retorne a coleção completa de dados válidos.
        return cleaned_data