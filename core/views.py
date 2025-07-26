from django.shortcuts import render, redirect, get_object_or_404
from .models import Orcamento, ConfiguracoesSistema, Material, MateriaisUtilizados, Cliente
from .models import Orcamento, ConfiguracoesSistema, Material, MateriaisUtilizados, Empresa
from django.forms import ModelForm, inlineformset_factory
from django.contrib import messages
from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import Orcamento, MateriaisUtilizados, Empresa

class OrcamentoForm(ModelForm):
    class Meta:
        model = Orcamento
        fields = [
            'cliente', 'nome', 'quantidade', 'tempo_por_unidade', 'margem_lucro',
            'folhas_pb', 'folhas_coloridas',
        ]

MateriaisFormset = inlineformset_factory(
    Orcamento, MateriaisUtilizados,
    fields=('material', 'quantidade_utilizada', 'fornecido_pelo_cliente'),  # checkbox do cliente fornece aqui
    extra=1,
    can_delete=True
)

def novo_orcamento(request):
    if request.method == 'POST':
        form = OrcamentoForm(request.POST)
        formset = MateriaisFormset(request.POST)
        
        if form.is_valid() and formset.is_valid():
            orcamento = form.save(commit=False)
            empresa = Empresa.objects.first()  # ajuste conforme sua regra
            orcamento.empresa = empresa
            orcamento.save()

            formset.instance = orcamento
            formset.save()
            return redirect('resultado_orcamento', pk=orcamento.pk)
    else:
        form = OrcamentoForm()
        formset = MateriaisFormset()

    return render(request, 'core/novo_orcamento.html', {
        'form': form,
        'formset': formset
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal

from .models import Orcamento, ConfiguracoesSistema

def resultado_orcamento(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)

    try:
        resultado = orcamento.calcular()
    except Exception as e:
        messages.error(request, str(e))
        return redirect('novo_orcamento')

    config = ConfiguracoesSistema.objects.first()
    quantidade = orcamento.quantidade
    tempo_total_minutos = orcamento.tempo_por_unidade * quantidade
    tempo_total_horas = Decimal(tempo_total_minutos) / Decimal(60)
    valor_hora = config.valor_hora()
    valor_minuto = valor_hora / Decimal(60)

    # Impressão – apenas para exibição (não entra no custo)
    custo_pb = Decimal(orcamento.folhas_pb) * config.custo_impressao_pb
    custo_colorida = Decimal(orcamento.folhas_coloridas) * config.custo_impressao_colorida
    valor_pb_unit = config.custo_impressao_pb
    valor_colorida_unit = config.custo_impressao_colorida

    # Materiais detalhados — incluir só materiais NÃO fornecidos pelo cliente (fornecido_pelo_cliente == False)
    materiais = []
    custo_materiais = Decimal('0.00')
    for uso in orcamento.materiaisutilizados.all():
        if not uso.fornecido_pelo_cliente:
            material = uso.material
            valor_unit = material.valor_unitario()
            total = valor_unit * Decimal(uso.quantidade_utilizada)
            custo_materiais += total
            materiais.append({
                "nome": material.nome,
                "quantidade": uso.quantidade_utilizada,
                "unidade": getattr(material, 'unidade', ''),
                "valor_unitario": valor_unit.quantize(Decimal('0.01')),
                "total": total.quantize(Decimal('0.01')),
                "fornecido_pelo_cliente": uso.fornecido_pelo_cliente,
            })

    # Atualiza o custo dos materiais no resultado (calculado só com materiais não fornecidos)
    resultado['custo_materiais'] = custo_materiais.quantize(Decimal('0.01'))
    resultado['materiais_detalhados'] = materiais

    # Totais (unitário * quantidade)
    resultado['custo_mao_obra_total'] = (resultado['custo_mao_obra_unit'] * quantidade).quantize(Decimal('0.01'))
    resultado['custo_materiais_total'] = custo_materiais.quantize(Decimal('0.01'))
    resultado['custo_despesas_total'] = (resultado['custo_despesas_unit'] * quantidade).quantize(Decimal('0.01'))
    resultado['custo_impressao_total'] = (custo_pb + custo_colorida).quantize(Decimal('0.01'))

    resultado.update({
        'quantidade': quantidade,
        'tempo_total_minutos': tempo_total_minutos,
        'tempo_total_horas': round(tempo_total_horas, 2),
        'valor_hora': round(valor_hora, 2),
        'valor_minuto': round(valor_minuto, 4),
        'custo_pb': round(custo_pb, 2),
        'custo_colorida': round(custo_colorida, 2),
        'valor_pb_unit': valor_pb_unit,
        'valor_colorida_unit': valor_colorida_unit,
    })

    return render(request, 'core/resultado_orcamento.html', {
        'orcamento': orcamento,
        'resultado': resultado
    })



from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Empresa
@login_required
def dashboard(request):
    empresa = Empresa.objects.first()  # pega a primeira empresa cadastrada, ajuste se precisar
    return render(request, 'core/dashboard.html', {'empresa': empresa})


from django.shortcuts import render, redirect
from .models import ConfiguracoesSistema
from .forms import ConfiguracoesSistemaForm

def parametros_sistema(request):
    configuracao, created = ConfiguracoesSistema.objects.get_or_create(pk=1)

    if request.method == 'POST':
        form = ConfiguracoesSistemaForm(request.POST, instance=configuracao)
        if form.is_valid():
            form.save()
            return redirect('parametros_sistema')
    else:
        form = ConfiguracoesSistemaForm(instance=configuracao)

    return render(request, 'core/parametros_sistema.html', {'form': form})


from django.shortcuts import render
from .models import Orcamento

def lista_orcamentos(request):
    orcamentos = Orcamento.objects.all()
    return render(request, 'core/lista_orcamentos.html', {'orcamentos': orcamentos})

from django.shortcuts import render, get_object_or_404
from .models import Orcamento

def gerar_orcamento_html(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)
    resultado = orcamento.calcular()

    return render(request, 'core/orcamento_gerado.html', {
        'orcamento': orcamento,
        'resultado': resultado,
        'cliente': orcamento.cliente,
        'empresa': orcamento.empresa,
    })

# views.py
from django.shortcuts import render, redirect
from .forms import ClienteForm
from django.contrib import messages

def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente cadastrado com sucesso!')
            return redirect('dashboard')  # ou 'lista_orcamentos', se preferir
    else:
        form = ClienteForm()

    return render(request, 'core/form.html', {'form': form})

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['nome', 'preco_pacote', 'quantidade_por_pacote', 'unidade']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'preco_pacote': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantidade_por_pacote': forms.NumberInput(attrs={'class': 'form-control'}),
            'unidade': forms.TextInput(attrs={'class': 'form-control'}),
        }

def cadastrar_produto(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto cadastrado com sucesso!')
            return redirect('cadastrar_produto')
    else:
        form = MaterialForm()
    return render(request, 'core/cadastrar_produto.html', {'form': form})

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Orcamento
from .forms import OrcamentoForm, MateriaisUtilizadosFormSet
from core.forms import MateriaisUtilizadosFormSet



def editar_orcamento(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)

    if request.method == 'POST':
        form = OrcamentoForm(request.POST, instance=orcamento)
        formset = MateriaisUtilizadosFormSet(request.POST, instance=orcamento)

        if form.is_valid() and formset.is_valid():
            print("Formulários válidos, salvando...")
            orc = form.save(commit=False)
            orc.empresa = orcamento.empresa  # mantém a empresa original aqui
            orc.save()
            formset.save()
            return redirect('resultado_orcamento', pk=orc.pk)
    else:
        
        form = OrcamentoForm(instance=orcamento)
        formset = MateriaisUtilizadosFormSet(instance=orcamento)

    return render(request, 'core/editar_orcamento.html', {
        'form': form,
        'formset': formset,
        'orcamento': orcamento,
    })


