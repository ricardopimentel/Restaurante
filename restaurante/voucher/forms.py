from django import forms

from restaurante.voucher.models import liberacao


class GeraLiberacaoForm(forms.ModelForm):

    class Meta:  # Define os campos vindos do Model
        model = liberacao
        fields = ('nome', 'telefone', 'id_voucher')

    def __init__(self, *args, **kwargs):  # INIT define caracteristicas para os campos de formulário vindos do Model (banco de dados)
        super(GeraLiberacaoForm, self).__init__(*args, **kwargs)
        self.fields['nome'].widget = forms.TextInput(attrs={
            'placeholder': 'Nome',
            'title': 'Nome'})
        self.fields['telefone'].widget = forms.TextInput(attrs={
            'placeholder': 'Telefone',
            'title': 'Telefone'})

        self.fields['nome'].label = ""
        self.fields['telefone'].label = ""
        self.fields['id_voucher'].label = ""


class CadastroVouchersForm(forms.Form):
    vouchers = forms.CharField(label="", max_length=30000, widget=forms.Textarea(attrs={'placeholder': 'Lista de Vouchers'}))

    def __init__(self, *args, **kwargs):
        super(CadastroVouchersForm, self).__init__(*args, **kwargs)


    def clean(self):
        cleaned_data = self.cleaned_data
        vouchers = cleaned_data.get("vouchers")

        # Sempre retorne a coleção completa de dados válidos.
        return cleaned_data
