from django.db import models
from decimal import Decimal, ROUND_HALF_UP
from cloudinary.models import CloudinaryField

class Empresa(models.Model):
    nome_fantasia = models.CharField("Nome Fantasia", max_length=150)
    razao_social = models.CharField("Razão Social", max_length=150)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    endereco = models.TextField("Endereço", blank=True)
    logotipo = CloudinaryField("Logotipo", blank=True, null=True)

    def __str__(self):
        return self.nome_fantasia



class Cliente(models.Model):
    nome = models.CharField("Nome", max_length=150)
    cpf_cnpj = models.CharField("CPF ou CNPJ", max_length=18, unique=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    endereco = models.TextField("Endereço", blank=True)

    def __str__(self):
        return f"{self.nome} ({self.cpf_cnpj})"


class ConfiguracoesSistema(models.Model):
    valor_mensal_desejado = models.DecimalField(
        "Valor mensal desejado", max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    dias_por_semana = models.PositiveIntegerField("Dias por semana", default=5)
    horas_por_dia = models.PositiveIntegerField("Horas por dia", default=8)
    margem_lucro_padrao = models.DecimalField(
        "Margem de lucro padrão (%)", max_digits=5, decimal_places=2, default=Decimal('10.00')
    )

    percentual_energia = models.DecimalField("Energia (%)", max_digits=5, decimal_places=2, default=Decimal('0.00'))
    percentual_internet = models.DecimalField("Internet (%)", max_digits=5, decimal_places=2, default=Decimal('0.00'))

    custo_impressao_pb = models.DecimalField("Custo impressão PB", max_digits=6, decimal_places=2, default=Decimal('0.00'))
    custo_impressao_colorida = models.DecimalField("Custo impressão colorida", max_digits=6, decimal_places=2, default=Decimal('0.00'))

    def valor_hora(self):
        semanas_mes = Decimal('4.33')
        total_horas = Decimal(self.dias_por_semana * self.horas_por_dia) * semanas_mes
        if total_horas == 0:
            return Decimal('0.00')
        valor = self.valor_mensal_desejado / total_horas
        return valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def __str__(self):
        return "Parâmetros do Sistema"


class Material(models.Model):
    nome = models.CharField("Nome do material", max_length=100)
    preco_pacote = models.DecimalField("Preço por pacote", max_digits=10, decimal_places=2)
    quantidade_por_pacote = models.PositiveIntegerField("Quantidade por pacote")
    unidade = models.CharField("Unidade", max_length=20, default="un")  # <-- campo adicionado

    def valor_unitario(self):
        if self.quantidade_por_pacote == 0:
            return Decimal('0.00')
        return (self.preco_pacote / self.quantidade_por_pacote).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

    def __str__(self):
        return f"{self.nome} ({self.unidade}) - R$ {self.valor_unitario()} por {self.unidade}"


from decimal import Decimal, ROUND_HALF_UP

class Orcamento(models.Model):
    nome = models.CharField("Nome do orçamento", max_length=200)
    cliente = models.ForeignKey("Cliente", on_delete=models.CASCADE)
    empresa = models.ForeignKey("Empresa", on_delete=models.CASCADE)

    quantidade = models.PositiveIntegerField("Quantidade")
    tempo_por_unidade = models.PositiveIntegerField("Tempo por unidade (minutos)")
    margem_lucro = models.DecimalField("Margem de lucro (%)", max_digits=5, decimal_places=2, null=True, blank=True)

    folhas_pb = models.PositiveIntegerField("Folhas PB", default=0)
    folhas_coloridas = models.PositiveIntegerField("Folhas coloridas", default=0)

    data_criacao = models.DateTimeField("Data de criação", auto_now_add=True)

    def calcular(self):
        config = ConfiguracoesSistema.objects.first()
        if not config:
            raise Exception("Cadastre as configurações do sistema primeiro.")

        arredonda = lambda v: v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        margem = self.margem_lucro or config.margem_lucro_padrao
        valor_hora = config.valor_hora()

        # Tempo total e custo mão de obra
        tempo_total_horas = (Decimal(self.tempo_por_unidade) * Decimal(self.quantidade)) / Decimal(60)
        custo_mao_obra = tempo_total_horas * valor_hora

        # Materiais: calcula custo só para materiais NÃO fornecidos pelo cliente
        materiais_detalhados = []
        custo_materiais = Decimal('0.00')
        for uso in self.materiaisutilizados.all():
            material = uso.material
            total = material.valor_unitario() * uso.quantidade_utilizada

            fornecido = getattr(uso, 'fornecido_pelo_cliente', False)
            if not fornecido:
                custo_materiais += total

            materiais_detalhados.append({
                "nome": material.nome,
                "quantidade": uso.quantidade_utilizada,
                "unidade": "un",  # ajuste conforme seu modelo, se tiver campo unidade
                "valor_unitario": arredonda(material.valor_unitario()),
                "total": arredonda(total),
                "fornecido_pelo_cliente": fornecido,
            })

        # Despesas (%)
        subtotal_sem_despesas = custo_mao_obra + custo_materiais
        percentual_despesas = (config.percentual_energia + config.percentual_internet) / Decimal(100)
        custo_despesas = subtotal_sem_despesas * percentual_despesas
        custo_total = subtotal_sem_despesas + custo_despesas

        # Custos de impressão fixos (não entram no custo para cálculo de lucro)
        valor_pb_unit = config.custo_impressao_pb
        valor_colorida_unit = config.custo_impressao_colorida

        valor_impressao_pb = Decimal(self.folhas_pb) * valor_pb_unit
        valor_impressao_colorida = Decimal(self.folhas_coloridas) * valor_colorida_unit
        valor_total_impressao = valor_impressao_pb + valor_impressao_colorida

        # Lucro somente sobre materiais NÃO fornecidos
        lucro_materiais = custo_materiais * (margem / Decimal(100))

        # Preço final
        preco_total = custo_total + lucro_materiais + valor_total_impressao
        preco_unitario = preco_total / Decimal(self.quantidade)
        lucro_total = preco_total - custo_total

        return {
            "tempo_por_unidade": self.tempo_por_unidade,

            "custo_mao_obra": arredonda(custo_mao_obra),
            "custo_materiais": arredonda(custo_materiais),
            "custo_despesas": arredonda(custo_despesas),
            "custo_total": arredonda(custo_total),

            "custo_mao_obra_unit": arredonda(custo_mao_obra / self.quantidade),
            "custo_materiais_unit": arredonda(custo_materiais / self.quantidade),
            "custo_despesas_unit": arredonda(custo_despesas / self.quantidade),
            "custo_unitario": arredonda(custo_total / self.quantidade),

            "valor_pb_unit": arredonda(valor_pb_unit),
            "valor_colorida_unit": arredonda(valor_colorida_unit),
            "valor_impressao_pb": arredonda(valor_impressao_pb),
            "valor_impressao_colorida": arredonda(valor_impressao_colorida),
            "valor_total_impressao": arredonda(valor_total_impressao),

            "preco_unitario": arredonda(preco_unitario),
            "preco_total": arredonda(preco_total),
            "lucro": arredonda(lucro_total),

            "materiais_detalhados": materiais_detalhados,
            "salario_desejado": arredonda(config.valor_mensal_desejado),
            "dias_semana": config.dias_por_semana,
            "horas_dia": config.horas_por_dia,
            "horas_semana": config.dias_por_semana * config.horas_por_dia,
            "horas_mes": Decimal(config.dias_por_semana * config.horas_por_dia) * Decimal('4.33'),
            "valor_hora": arredonda(valor_hora),
            "valor_minuto": arredonda(valor_hora / Decimal(60)),
        }

    def __str__(self):
        return f"Orçamento: {self.nome}"

class MateriaisUtilizados(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='materiaisutilizados')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantidade_utilizada = models.DecimalField("Quantidade utilizada", max_digits=10, decimal_places=2)
    fornecido_pelo_cliente = models.BooleanField("Fornecido pelo cliente?", default=False)

    def __str__(self):
        fornecido = "✅ Cliente fornece" if self.fornecido_pelo_cliente else "❌ Compra"
        return f"{self.quantidade_utilizada}x {self.material.nome} ({fornecido}) para {self.orcamento.nome}"

