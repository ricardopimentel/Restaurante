from django import forms


class RelatorioVendasForm(forms.Form):
    campo_data_inicial = forms.DateField(label="Data Inicial", widget=forms.DateInput(attrs={'type': 'date'}))
    campo_data_final = forms.DateField(label="Data Final", widget=forms.DateInput(attrs={'type': 'date'}))
    campo_aluno = forms.ChoiceField(label="Aluno")

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(RelatorioVendasForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data
        campo_data_inicial = cleaned_data.get("campo_data_inicial")
        campo_data_final = cleaned_data.get("campo_data_final")
        campo_aluno = cleaned_data.get("campo_aluno")

        if campo_data_final < campo_data_inicial:
            raise forms.ValidationError("A data inicial deve ser menor que a data final", code='invalid')

        return cleaned_data