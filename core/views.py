# views.py

# =======================
# IMPORTAÇÕES DJANGO
# =======================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django import forms
from decimal import Decimal

# =======================
# IMPORTAÇÕES INTERNAS
# =======================
from .models import (
    Orcamento, Empresa, ConfiguracoesSistema,
    Material, MateriaisUtilizados, Cliente
)
from .forms import (
    OrcamentoForm, MateriaisUtilizadosFormSet,
    ClienteForm, ConfiguracoesSistemaForm
)

# =======================
# FORMSET
# =======================
from django.forms import inlineformset_factory

MateriaisFormset = inlineformset_factory(
    Orcamento, MateriaisUtilizados,
    fields=('material', 'quantidade_utilizada', 'fornecido_pelo_cliente'),
    extra=1,
    can_delete=True
)

# =======================
# NOVO ORÇAMENTO
# =======================
def novo_orcamento(request):
    if request.method == 'POST':
        form = OrcamentoForm(request.POST)
        formset = MateriaisFormset(request.POST)
        
        if form.is_valid() and formset.is_valid():
            orcamento = form.save(commit=False)
            orcamento.empresa = Empresa.objects.first()  # Ajuste conforme regra
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


# =======================
# RESULTADO DO ORÇAMENTO
# =======================
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

    custo_pb = Decimal(orcamento.folhas_pb) * config.custo_impressao_pb
    custo_colorida = Decimal(orcamento.folhas_coloridas) * config.custo_impressao_colorida
    custo_impressao_total = custo_pb + custo_colorida

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

    resultado.update({
        'quantidade': quantidade,
        'tempo_total_minutos': tempo_total_minutos,
        'tempo_total_horas': round(tempo_total_horas, 2),
        'valor_hora': round(valor_hora, 2),
        'valor_minuto': round(valor_minuto, 4),
        'custo_pb': round(custo_pb, 2),
        'custo_colorida': round(custo_colorida, 2),
        'valor_pb_unit': config.custo_impressao_pb,
        'valor_colorida_unit': config.custo_impressao_colorida,
        'custo_materiais': custo_materiais.quantize(Decimal('0.01')),
        'materiais_detalhados': materiais,
        'custo_impressao_total': custo_impressao_total.quantize(Decimal('0.01')),
    })

    return render(request, 'core/resultado_orcamento.html', {
        'orcamento': orcamento,
        'resultado': resultado
    })

# =======================
# DASHBOARD
# =======================
@login_required
def dashboard(request):
    empresa = Empresa.objects.first()
    return render(request, 'core/dashboard.html', {'empresa': empresa})


# =======================
# PARÂMETROS DO SISTEMA
# =======================
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


# =======================
# LISTA DE ORÇAMENTOS
# =======================
def lista_orcamentos(request):
    orcamentos = Orcamento.objects.all()
    return render(request, 'core/lista_orcamentos.html', {'orcamentos': orcamentos})


# =======================
# GERAR ORÇAMENTO HTML
# =======================
def gerar_orcamento_html(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)
    resultado = orcamento.calcular()

    return render(request, 'core/orcamento_gerado.html', {
        'orcamento': orcamento,
        'resultado': resultado,
        'cliente': orcamento.cliente,
        'empresa': orcamento.empresa,
    })


# =======================
# CADASTRAR CLIENTE
# =======================
def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente cadastrado com sucesso!')
            return redirect('dashboard')
    else:
        form = ClienteForm()

    return render(request, 'core/form.html', {'form': form})


# =======================
# CADASTRAR PRODUTO
# =======================
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


# =======================
# EDITAR ORÇAMENTO
# =======================
def editar_orcamento(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)

    if request.method == 'POST':
        form = OrcamentoForm(request.POST, instance=orcamento)
        formset = MateriaisUtilizadosFormSet(request.POST, instance=orcamento)

        if form.is_valid() and formset.is_valid():
            orc = form.save(commit=False)
            orc.empresa = orcamento.empresa
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


# =======================
# EXCLUIR ORÇAMENTO
# =======================
def excluir_orcamento(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)
    orcamento.delete()
    return redirect('lista_orcamentos')

def detalhes_preco(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)
    resultado = orcamento.calcular()

    tempo_total_minutos = orcamento.tempo_por_unidade * orcamento.quantidade

    return render(request, 'core/detalhes_preco.html', {
        'orcamento': orcamento,
        'resultado': resultado,
        'tempo_total_minutos': tempo_total_minutos,
    })
