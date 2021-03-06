import os
import qrcode
from django.contrib.auth import authenticate
from django.utils.text import slugify

from django.db import models
from django.db.models import Model
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone


def upload_to(instance, filename):
    filename_base, filename_ext = os.path.splitext(filename)
    return "media/{evento}/{filename}{extension}".format(
        evento=slugify(instance.id_evento.id),
        filename=slugify(filename_base),
        extension=filename_ext.lower(),
    )

def gerar_qr_code(instance, filename):
    filename_base, filename_ext = os.path.splitext(filename)
    return "media/qr_code/{usuario}/{filename}{extension}".format(
        usuario=slugify(instance.id_usuario.id),
        filename=slugify(filename_base),
        extension=filename_ext.lower(),
    )


# ========={ Endereço }========== #

class Estado(Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200, blank=False)

    def __str__(self):
        return self.get_address()

    def get_address(self):
        return self.nome


class Municipio(Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200, blank=False)
    id_estado = models.ForeignKey('Estado', on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return self.get_address()

    def get_estado(self):
        return self.id_estado

    def get_address(self):
        return self.nome + ', ' + self.get_estado().get_address()


class Bairro(Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200, blank=False)
    id_municipio = models.ForeignKey('Municipio', on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return self.get_address()

    def get_estado(self):
        return self.id_municipio.get_estado()

    def get_municipio(self):
        return self.id_municipio

    def get_address(self):
        return self.nome + ', ' + self.get_municipio().get_address()


class Logradouro(Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200, blank=False)
    cep = models.CharField(max_length=8, blank=False, validators=[RegexValidator(regex='\d\d\d\d\d\d\d\d')])
    id_bairro = models.ForeignKey('Bairro', on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return self.get_address()

    def get_estado(self):
        return self.id_bairro.get_estado()

    def get_municipio(self):
        return self.id_bairro.get_municipio()

    def get_bairro(self):
        return self.id_bairro

    def get_address(self):
        return self.nome + ', ' + self.get_bairro().get_address()


class Endereco(Model):
    id = models.AutoField(primary_key=True)
    complemento = models.CharField(max_length=200, blank=True)
    numero = models.PositiveIntegerField(blank=True)
    id_logradouro = models.ForeignKey('Logradouro', on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return self.get_address()

    def get_estado(self):
        return self.id_logradouro.get_estado()

    def get_municipio(self):
        return self.id_logradouro.get_municipio()

    def get_bairro(self):
        return self.id_logradouro.get_bairro()

    def get_logradouro(self):
        return self.id_logradouro

    def get_address(self):
        if self.numero is not None:
            addr = self.get_logradouro().nome + ' ' + self.numero.__str__() + ', ' + self.get_bairro().get_address()
        else:
            addr = self.get_logradouro().get_address()
        return addr

    def get_endereco_abreviado(self):
        return self.get_municipio().nome + '/' + self.get_estado().nome


# =============={ Usuários }=============#
class Usuario(User):
    cpf = models.CharField(max_length=11, blank=False,
                           validators=[RegexValidator(regex='[\d]+')])  # Verificar se é possivel usar o Regex
    data_nasc = models.DateField(verbose_name='Data de Nascimento', blank=False)
    genero = models.CharField(max_length=5, blank=False, choices=(('M', 'Masculino'), ('F', 'Feminino')))
    id_endereco = models.ForeignKey('Endereco', on_delete=models.CASCADE, blank=True)

    @staticmethod
    def autenticar(username, password):
        user = authenticate(username=username, password=password)
        return user

    @staticmethod
    def get_usuario(id):
        return Usuario.objects.filter(id=id).first()

    def criar_promotor(self):
        self.set_password(self.password)
        self.is_staff = True
        promotor_profile = Group.objects.filter(name='Promotor').first()
        self.groups.add(promotor_profile)
        self.save()
        return

    def get_carrinho(self):
        cart = Carrinho.objects.filter(id_user=self.id, status=True).first()
        if cart is None:
            cart = Carrinho(id_user=self)
            cart.save()
        return cart


class Carrinho(Model):
    id = models.AutoField(primary_key=True)
    id_user = models.ForeignKey('Usuario', blank=False, on_delete=models.CASCADE)
    ingressos = models.ManyToManyField('Lote', through='CarrinhoIngresso')
    status = models.BooleanField(default=True)

    def total_ingressos(self):
        count = 0
        item_list = self.get_item()
        for item in item_list:
            count += item.qtd_ingresso
        return count

    def calcular_total(self):
        carrinho_list = CarrinhoIngresso.objects.filter(id_carrinho=self.id)
        total = 0
        for carrinho_item in carrinho_list:
            total += carrinho_item.total()
        return total

    def total(self):
        total = float(self.calcular_total())
        return "%.2f" % total

    def get_item(self):
        return CarrinhoIngresso.objects.filter(id_carrinho=self.id)

    def get_item_by_id(self, id):
        return self.get_item().filter(id=id).first()

    def size(self):
        return len(self.get_item())


class CarrinhoIngresso(Model):
    id = models.AutoField(primary_key=True)
    id_carrinho = models.ForeignKey('Carrinho', on_delete=models.CASCADE, blank=False)
    id_lote = models.ForeignKey('Lote', on_delete=models.CASCADE, blank=False)
    qtd_ingresso = models.PositiveIntegerField(blank=False, validators=[MinValueValidator(1)])

    def total(self):
        return self.id_lote.valor * self.qtd_ingresso

    def update_qtd_ingresso(self,qtd_ingresso):
        if self.qtd_ingresso != qtd_ingresso:
            self.qtd_ingresso = qtd_ingresso
            self.save()
            return True
        return False

    def get_ingresso(self):
        return self.id_lote.id_ingresso


# ============={ Eventos }===============#
class Categoria(Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200, blank=False)

    def __str__(self):
        return self.nome

    def get_recomendacao(self):
        return Evento.objects.filter(id_categoria=self)[:10]


class Banner(Model):
    id = models.AutoField(primary_key=True)
    # image_url = models.ImageField(upload_to='media/', default='media/no-img.png')
    image_url = models.ImageField(upload_to=upload_to, default='media/no-img.png')
    id_evento = models.ForeignKey('Evento', on_delete=models.CASCADE, blank=False)


"""
    Status Evento:
    E - Em Análise
    A - Aprovado
    R - Reprovado
    O - Ocorrendo
    F - Finalizado
"""
class Evento(Model):
    id = models.AutoField(primary_key=True)
    status = models.CharField(default='E', max_length=1, editable=False)
    id_promotor = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    id_categoria = models.ManyToManyField('Categoria', blank=False, verbose_name='Categorias')
    nome = models.CharField(max_length=200, blank=False)
    descricao = models.TextField(blank=False, verbose_name='Descrição')
    id_endereco = models.ForeignKey('Endereco', on_delete=models.CASCADE, blank=True, verbose_name='Endereço')
    data_hora_criacao = models.DateTimeField(auto_now_add=True, editable=False)
    data_inicio_venda = models.DateField(blank=False, verbose_name='Inicio das vendas')
    hora_inicio_venda = models.TimeField(blank=False, verbose_name='Inicio das vendas')
    data_fim_venda = models.DateField(blank=False, verbose_name='Fim das vendas')
    hora_fim_venda = models.TimeField(blank=False, verbose_name='Fim das vendas')
    
    def __str__(self):
        return self.nome

    def get_ingresso(self):
        return Ingresso.objects.filter(id_evento=self.id)

    def get_banners(self):
        return Banner.objects.filter(id_evento=self.id)

    def get_first_banner(self):
        return self.get_banners().first()

    def get_categoria(self):
        return self.id_categoria.all()

    def get_first_categoria(self):
        return self.get_categoria().first()

    def aprovar(self):
        if self.status == 'E':
            self.status = 'A'
            self.save()
            return True
        return False

    def reprovar(self):
        if self.status == 'E':
            self.status = 'R'
            self.save()
            return True
        return False

    def iniciar(self):
        if self.status == 'A':
            self.status = 'O'
            self.save()
            return True
        return False

    def finalizar(self):
        if self.status == 'O':
            self.status = 'F'
            self.save()
            return True
        return False

    def get_recomendacao(self):
        return self.id_categoria.first().get_recomendacao()



class Ingresso(Model):
    id = models.AutoField(primary_key=True)
    id_evento = models.ForeignKey('Evento', on_delete=models.CASCADE, blank=False)
    tipo = models.CharField(max_length=200, blank=False, verbose_name='Tipo de ingresso')

    def __str__(self):
        return self.id_evento.nome + ' - ' + self.tipo

    def get_meta_nome(self):
        lote = self.get_lote()
        if lote is None:
            return self.__str__() + ' - ESGOTADO'
        return self.__str__() + ' - ' + lote.nome

    def get_lote(self):
        lote_list = Lote.objects.filter(id_ingresso=self.id).order_by('nome')
        for lote in lote_list:
            if lote.status():
                return lote
        return None


class Lote(Model):
    id = models.AutoField(primary_key=True)
    id_ingresso = models.ForeignKey('Ingresso', on_delete=models.CASCADE, blank=False)
    nome = models.CharField(max_length=200, verbose_name='Nome do Lote')
    valor = models.FloatField(blank=False,
                              validators=[MinValueValidator(0.0)])  # Adicionar verificação de valor negativo
    qtd_max = models.PositiveIntegerField(blank=False, verbose_name='Quantidade')
    data_inicio_venda = models.DateField(blank=False, verbose_name='Inicio das vendas')
    hora_inicio_venda = models.TimeField(blank=False, verbose_name='Inicio das vendas')
    data_fim_venda = models.DateField(blank=False, verbose_name='Fim das vendas')
    hora_fim_venda = models.TimeField(blank=False, verbose_name='Fim das vendas')
    qtd_vendido = models.PositiveIntegerField(blank=False, default=0)

    def __str__(self):
        return self.id_ingresso.id_evento.__str__() + ' | ' + self.id_ingresso.__str__() + ' - ' + self.nome

    def status(self):
        return self.qtd_vendido < self.qtd_max


# Revisar com a Ju e o Caio
class Eticket(Model):
    id = models.AutoField(primary_key=True)
    cpf = models.CharField(max_length=11, blank=True, validators=[RegexValidator(regex='[\d]+')])
    status = models.BooleanField(default=True)
    nome = models.CharField(max_length=200, blank=True)
    id_usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, blank=False)
    id_ingresso = models.ForeignKey('Ingresso', on_delete=models.CASCADE, blank=False)
    id_compra = models.ForeignKey('Compra', on_delete=models.CASCADE, blank=False)
    qr_code = models.ImageField(upload_to=gerar_qr_code, default='media/no-img.png')

    def __str__(self):
        nome = ''
        if self.nome is not None:
            nome = self.nome
        return self.id_ingresso.id_evento.__str__() + ' - ' + nome

    def gerar_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.id)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        img_file_name = str(self.id) + '.jpg'

        img_path = 'media/qr_code/' + str(self.id_usuario.id) + '/'
        try:
            os.mkdir(img_path)
        except FileExistsError:
            pass
        img.save(img_path + img_file_name)
        self.qr_code = img_path + img_file_name
        self.save()

# ============{ Pagamento }===========
class FormaPagamento(Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200, blank=False)

    def __str__(self):
        return self.nome


"""
    Status da Compra:
    A - Aguardando Pagamento
    P - Pagamento Efetuado com Sucesso
    N - Pagamento Não Efetuado
"""
class Compra(Model):
    id = models.AutoField(primary_key=True)
    status = models.CharField(default='A', max_length=1)
    data_compra = models.DateTimeField(blank=False)
    data_pagamento = models.DateTimeField()
    id_carrinho = models.ForeignKey('Carrinho', on_delete=models.CASCADE, blank=False)
    id_forma_pagamento = models.ForeignKey('FormaPagamento', on_delete=models.CASCADE, blank=False)
    id_user = models.ForeignKey('Usuario', on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return self.id_carrinho.id_user.__str__() + ' - ' + self.data_compra.__str__()

    def get_forma_pagamento(self):
        return self.id_forma_pagamento

    def pagar(self):
        self.status = 'P'

    # A implementar
    def gerar_eticket(self):
        etickets = Eticket.objects.filter(id_compra=self.id)
        if self.status == 'P' and len(etickets) == 0:
            carrinho = self.id_carrinho

            user = carrinho.id_user

            ingresso_list = carrinho.get_item()

            for ingresso in ingresso_list:
                for i in range(ingresso.qtd_ingresso):
                    et = Eticket(id_ingresso=ingresso.get_ingresso(), id_compra=self, id_usuario=user)
                    et.save()
                    et.gerar_qr_code()
        return
