from django import forms
from .models import ConfiguracoesSistema
from .models import Orcamento, Cliente
from django.forms import inlineformset_factory
from .models import MateriaisUtilizados

class OrcamentoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), label="Cliente")

    class Meta:
        model = Orcamento
        fields = [
            'nome', 'cliente', 'quantidade', 'tempo_por_unidade', 
            'margem_lucro', 'folhas_pb', 'folhas_coloridas',
        ]



class ConfiguracoesSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracoesSistema
        fields = '__all__'
        widgets = {
            'valor_mensal_desejado': forms.NumberInput(attrs={'step': '0.01'}),
            'margem_lucro_padrao': forms.NumberInput(attrs={'step': '0.01'}),
            'percentual_energia': forms.NumberInput(attrs={'step': '0.01'}),
            'percentual_internet': forms.NumberInput(attrs={'step': '0.01'}),
            'custo_impressao_pb': forms.NumberInput(attrs={'step': '0.01'}),
            'custo_impressao_colorida': forms.NumberInput(attrs={'step': '0.01'}),
        }


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'endereco': forms.Textarea(attrs={'rows': 2}),
        }



class OrcamentoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), label="Cliente")

    class Meta:
        model = Orcamento
        fields = [
            'nome', 'cliente', 'quantidade', 'tempo_por_unidade', 'margem_lucro',
            'folhas_pb', 'folhas_coloridas'
        ]

MateriaisUtilizadosFormSet = inlineformset_factory(
    Orcamento,
    MateriaisUtilizados,
    fields=['material', 'quantidade_utilizada', 'fornecido_pelo_cliente'],
    extra=1,
    can_delete=True
)
