from django import forms
from django.core.exceptions import ObjectDoesNotExist

from restaurante.administracao.models import config
from restaurante.core.libs.conexaoAD3 import conexaoAD


class AdForm(forms.ModelForm):
    # Cria dois campos que não estão no banco de dados, são eles: usuário e senha. Os dados desses campos são providos pelo Active Directory
    usuario = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Usuário'}))
    senha = forms.CharField(label="", widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))
    filter = forms.CharField(label="Filtro", widget=forms.Textarea)

    class Meta:  # Define os campos vindos do Model
        model = config
        fields = ('dominio', 'endservidor', 'gadmin', 'ou')

    def __init__(self, request, *args, **kwargs):  # INIT define caracteristicas para os campos de formulário vindos do Model (banco de dados)
        super(AdForm, self).__init__(*args, **kwargs)
        self.request = request
        self.fields['dominio'].widget = forms.TextInput(attrs={
            'placeholder': 'Dominio',
            'title': 'Dominio'})
        self.fields['endservidor'].widget = forms.TextInput(attrs={
            'placeholder': 'Endereço Servidor',
            'title': 'Endereço IP do controlador de dominio'})
        self.fields['gadmin'].widget = forms.TextInput(attrs={
            'placeholder': 'Grupo Administradores',
            'title': 'Grupo dos administradores do sistema'})
        self.fields['ou'].widget = forms.TextInput(attrs={
            'placeholder': 'Base',
            'title': 'Estrutura completa de onde o sistema irá buscar os elementos'})
        self.fields['dominio'].label = ""
        self.fields['endservidor'].label = ""
        self.fields['gadmin'].label = ""
        self.fields['ou'].label = ""

    def clean(self):
        # Inicializa váriaveis com os dados digitados no formulario
        cleaned_data = self.cleaned_data
        Usuario = cleaned_data.get("usuario")
        Senha = cleaned_data.get("senha")
        Dominio = cleaned_data.get("dominio")
        Endservidor = cleaned_data.get("endservidor")
        Gadmin = cleaned_data.get("gadmin")
        Ou = cleaned_data.get("ou")
        Filter = cleaned_data.get("filter")

        if Usuario and Senha:  # Usuário e senha OK
            # Cria Conexão LDAP ou = 'OU=ca-paraiso, OU=reitoria, OU=ifto, DC=ifto, DC=local'
            c = conexaoAD(Usuario, Senha)
            result = c.PrimeiroLogin(Usuario, Senha, Dominio, Endservidor, Filter)  # tenta login no ldap e salva resultado em result
            if (result == ('i')):  # Credenciais invalidas (usuario e/ou senha)
                # Adiciona erro na validação do formulário
                raise forms.ValidationError("Usuário ou senha incorretos", code='invalid')
            elif (result == ('n')):  # Server Down
                # Adiciona erro na validação do formulário
                raise forms.ValidationError("Erro na Conexão", code='invalid')
            else:  # se logou
                try:  # Tenta salvar tudo no banco de dados no id 1
                    # Pega uma instancia do item conf do banco de dados
                    conf = config.objects.get(id=1)
                    conf.dominio = Dominio
                    conf.endservidor = Endservidor
                    conf.gadmin = Gadmin
                    conf.ou = Ou
                    conf.filter = Filter
                    conf.save()
                except ObjectDoesNotExist:  # caso não exista nada no bd cria um id 1 com os dados passados
                    conf = config(id=1, dominio=Dominio, endservidor=Endservidor, gadmin=Gadmin, ou=Ou, filter=Filter)
                    conf.save()
        # Sempre retorne a coleção completa de dados válidos.
        return cleaned_data