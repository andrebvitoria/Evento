from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse, JsonResponse
from .forms import *
from .models import Evento, Lote, Usuario, Carrinho, CarrinhoIngresso
import json
from django.core import serializers
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group

# Create your views here.
"""
    View da Página Inicial
"""


def home(request):
    temp = loader.get_template('evento_site/pages/home.html')
    return HttpResponse(temp.render({}, request))


"""
    View da Página de cadastro de usuário
"""


def criar_conta(request):
    if request.user.is_authenticated:
        return redirect(home)
    msg = ''
    # Carregamento do template
    temp = loader.get_template('evento_site/pages/user_register.html')

    if request.method == 'POST':
        post = request.POST
        user_forms = UserForm(post)
        if user_forms.is_valid():
            # Salva o formulário
            user_object = user_forms.save()

            # Atribui as permissões do Promotor
            user_object.criar_promotor()

            Usuario.autenticar(username=user_object.username, password=user_object.password)
            return redirect(home)
        else:
            msg = user_forms.errors
    else:
        user_forms = UserForm()

    user_forms.format()

    # end_forms = EnderecoForm()
    test = json.dumps({1: 1, 2: 2})
    return HttpResponse(temp.render({
        'message': msg,
        'user_forms': user_forms,
        # 'endereco_forms': end_forms,
        'test': test
    }, request))


"""
    Funções de Construção do JSON da api de eventos 
"""


def build_categoria(evento):
    cat_list = list()
    for categoria in evento.id_categoria.all():
        cat_list.append(categoria.nome)
    return sorted(cat_list)


def build_evento(evento):
    evento_serialized = json.loads(serializers.serialize('json', [evento, ], fields=(
        'status', 'nome', 'banner', 'descricao', 'data_inicio', 'data_fim',)))
    temp_evento_dict = evento_serialized[0]['fields']
    temp_evento_dict['id'] = evento_serialized[0]['pk']
    temp_evento_dict['categoria'] = build_categoria(evento)
    banner = Banner.objects.filter(id_evento=evento).first()
    if banner is not None:
        temp_evento_dict['banner'] = banner.image_url.url
    else:
        temp_evento_dict['banner'] = ''
    return temp_evento_dict


def build_promotor(evento):
    temp_promotor_evento_dict = dict()
    temp_promotor_evento_dict['id'] = evento.id_promotor.id
    temp_promotor_evento_dict['nome'] = evento.id_promotor.first_name + ' ' + evento.id_promotor.last_name
    return temp_promotor_evento_dict


def build_endereco(evento):
    temp_local_evento_dict = dict()
    temp_local_evento_dict["complemento"] = evento.id_endereco.complemento
    temp_local_evento_dict["numero"] = evento.id_endereco.numero
    temp_local_evento_dict["logradouro"] = evento.id_endereco.id_logradouro.nome
    temp_local_evento_dict["bairro"] = evento.id_endereco.id_logradouro.id_bairro.nome
    temp_local_evento_dict["cidade"] = evento.id_endereco.id_logradouro.id_bairro.id_municipio.nome
    temp_local_evento_dict["estado"] = evento.id_endereco.id_logradouro.id_bairro.id_municipio.id_estado.nome
    return temp_local_evento_dict


def build_preco_evento(evento):
    return dict()


def build_evento_list(eventos):
    evento_list = list()
    count = 0
    for evento in eventos:
        evento_dict = dict()

        evento_dict['page'] = 'evento/' + str(evento.id)

        # Recuperando informações sobre o evento e inserindo-as em um dicionario
        evento_dict['evento'] = build_evento(evento)

        # Recuperando informações sobre o promotor do evento e inserindo-as em um dicionario
        evento_dict['promotor'] = build_promotor(evento)

        # Recuperando informações sobre o local do evento e inserindo-as em um dicionario
        evento_dict['endereco'] = build_endereco(evento)

        # Recuperando informação sobre o igresso de menor valor
        evento_dict['ingresso'] = build_preco_evento(evento)

        evento_list.append(evento_dict)
    return {'value': evento_list}


def build_evento_json(eventos):
    evento_list = build_evento_list(eventos)
    return json.dumps(evento_list)


"""
    View da API de eventos 
"""


def get_eventos(request):
    evento_json = ''
    if request.method == 'GET':
        interval = 20
        id_get = int(request.GET['id'])
        eventos = Evento.objects.filter(status='A')[interval * id_get: (id_get + 1) * interval]
        evento_json = build_evento_list(eventos)

    return JsonResponse(evento_json)


"""
    View da Página dos eventos 
"""


def get_evento(request, id):
    if request.method == "GET":
        try:
            evento = Evento.objects.get(pk=id)
            banner = Banner.objects.filter(id_evento=evento).first()
            if banner is None:
                banner = {'image_url': {'url': 'images/evento_cards/evento1.png'}}
            recomendacao = evento.get_recomendacao()

            temp = loader.get_template('evento_site/pages/evento/evento.html')
            return HttpResponse(temp.render({
                'evento': evento,
                'banner': banner,
                'recomendacao': recomendacao
            }, request))
        except:
            return home(request)

    elif request.method == "POST":
        if request.user is not None and request.user.is_authenticated:
            user = Usuario.get_usuario(request.user.id)
        else:
            return redirect(login_evento)
        post = request.POST
        ingresso_list = sorted(post.keys())[:-1]
        for meta in ingresso_list:
            if int(post[meta]) > 0:
                id_ingresso, id_lote = meta.split('-')
                lote = Lote.objects.filter(id=id_lote, id_ingresso=id_ingresso).first()
                if lote is not None:
                    carrinho = user.get_carrinho()
                    CarrinhoIngresso(id_lote=lote, id_carrinho=carrinho, qtd_ingresso=int(post[meta])).save()
        request.method = "GET"
        return redirect(get_carrinho)


def get_carrinho(request):
    # Só responde requisições do tipo GET ou DELETE
    if request.method == "GET" or request.method == "DELETE":
        # Recupera Objeto Usuario com base no ID do usuário logado no sistema
        user = Usuario.get_usuario(request.user.id)

        # Recupera o Carrinho do usuário
        carrinho = user.get_carrinho()

        if 'DELETE' in request.GET.keys():  # request.method == 'DELETE':
            user.get_carrinho()
            id = request.GET['id']
            item = carrinho.get_item_by_id(id)
            if item is not None:
                item.delete()

        # Recupera os itens dentro do carrinho
        carrinho_ingresso = carrinho.get_item()

        # Carrega o Template
        temp = loader.get_template('evento_site/pages/carrinho.html')

        return HttpResponse(temp.render({'carrinho': carrinho, 'carrinho_ingresso': carrinho_ingresso}, request))
    elif request.method == 'POST':
        # Recupera Objeto Usuario com base no ID do usuário logado no sistema
        user = Usuario.get_usuario(request.user.id)

        # Recupera o Carrinho do usuário
        carrinho = user.get_carrinho()

        # Dados do Formulário de Carrinho
        post = request.POST

        # Atualizando a quantidade de ingressos
        for key in post:
            if 'ci-' in key:
                ci_id = int(key.split('-')[1])
                ci_qtd = int(post[key])
                if ci_qtd > 0:
                    item = carrinho.get_item_by_id(ci_id)
                    item.update_qtd_ingresso(ci_qtd)
                else:
                    carrinho.get_item_by_id(ci_id).delete()
        return redirect(pagamento)


def pagamento(request):
    if request.method == 'POST':
        post = request.POST
        carrinho_id = post['carrinhoID']
        total = float(post['total'])
        data = post.get('data', False)
        tipo_pagamento = post['type']

        carrinho = Carrinho.objects.filter(id=carrinho_id, status=True).first()
        forma_pagamento = FormaPagamento.objects.filter(nome=tipo_pagamento).first()
        compra = Compra.objects.filter(id_carrinho=carrinho.id)
        if carrinho is not None and forma_pagamento is not None and carrinho.calcular_total() == total and len(
                compra) == 0:
            compra = Compra(data_compra=timezone.now(), data_pagamento=timezone.now(), id_carrinho=carrinho,
                            id_forma_pagamento=forma_pagamento, id_user=carrinho.id_user)

            compra.pagar()
            compra.save()

            compra.gerar_eticket()
            carrinho.status = False
            carrinho.save()
        return redirect(home)
    else:
        user = Usuario.get_usuario(request.user.id)

        carrinho = user.get_carrinho()

        temp = loader.get_template('evento_site/pages/pagamento.html')

        forma_pagamento = FormaPagamento.objects.all()

        return HttpResponse(temp.render({
            'carrinho': carrinho,
            'forma_pagamento': forma_pagamento,
        }, request))


# Mensagem de erro de da Usuário ou senha tela do Login
def error_msg():
    msg = {'class': 'red-text', 'text': 'Usuário ou senha inválidos!'}
    return msg


# Mensagem de erro de Usuário desabilitado
def disabled_msg():
    msg = {'class': 'yellow-text', 'text': 'Seu usuário foi desativado. Por favor contacte o administrador.'}
    return msg


def login_evento(request):
    if request.user is not None and request.user.is_authenticated:
        return redirect(home)

    loginForm = LoginForm()
    temp = loader.get_template('evento_site/pages/login.html')
    msg = {'class': '', 'text': ''}

    if request.method == 'POST':
        username_request = request.POST.get('user')
        password_request = request.POST.get('password')
        user = Usuario.autenticar(username=username_request, password=password_request)

        if user is None:
            msg = error_msg()
        elif user.is_active:
            login(request, user)
            return redirect(home)
        else:
            msg = disabled_msg()

    return HttpResponse(temp.render({
        'login': loginForm,
        'msg': msg
    }, request))


def logout_evento(request):
    logout(request)
    return redirect(login_evento)


def criar_evento(request):
    if not request.user.is_authenticated:
        return redirect(login_evento)

    if request.method == 'POST':
        a = request._post
        1 + None

    evento = EventoForm()
    evento.format()

    endereco = EnderecoForm()

    ingresso = IngressoForm()

    lote = LoteForm()

    categoria_list = Categoria.objects.all()
    categoria_dict = {}
    for cat in categoria_list:
        categoria_dict[cat.nome] = 'null'
    categoria = json.dumps(categoria_dict)

    temp = loader.get_template('evento_site/pages/evento/criar_evento.html')
    return HttpResponse(temp.render({
        'evento': evento,
        'endereco': endereco,
        'ingresso': ingresso,
        'lote': lote,
        'categoria': categoria,
    }, request))
