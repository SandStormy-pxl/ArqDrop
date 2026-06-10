from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Arquivo
import json
import sys
import io
import subprocess

@login_required
def lista_arquivos(request, arquivo_id=None):
    arquivos = Arquivo.objects.filter(autor=request.user).order_by('-id')
    arquivo_editando = None
    if arquivo_id:
        arquivo_editando = get_object_or_404(Arquivo, id=arquivo_id, autor=request.user)

    return render(request, 'gerenciador/index.html', {
        'arquivos': arquivos,
        'arquivo_editando': arquivo_editando
    })

@login_required
def criar_arquivo(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_do_arquivo', '').strip()
        if nome:
            extensoes_validas = ('.txt', '.py', '.html', '.json')
            if not nome.lower().endswith(extensoes_validas):
                nome += '.txt'

            Arquivo.objects.create(
                autor=request.user,
                nome_do_arquivo=nome,
                conteudo_do_arquivo="Escreva o conteúdo aqui..."
            )
    return redirect('lista_arquivos')

@login_required
def salvar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(Arquivo, id=arquivo_id, autor=request.user)
    if request.method == 'POST':
        arquivo.conteudo_do_arquivo = request.POST.get('conteudo_do_arquivo')
        arquivo.save()
    return redirect('lista_arquivos')

@login_required
def deletar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(Arquivo, id=arquivo_id, autor=request.user)
    arquivo.delete()
    return redirect('lista_arquivos')

@login_required
def upload_arquivo(request):
    if request.method == 'POST' and request.FILES.get('arquivo_fisico'):
        arquivo_enviado = request.FILES['arquivo_fisico']
        nome = arquivo_enviado.name

        extensoes_validas = ('.txt', '.py', '.html', '.json')
        if not nome.lower().endswith(extensoes_validas):
            messages.error(request, 'Formato não suportado! Use .txt, .py, .html ou .json.')
            return redirect('lista_arquivos')

        try:
            conteudo = arquivo_enviado.read().decode('utf-8')
        except UnicodeDecodeError:
            messages.error(request, 'Erro ao ler o arquivo. Certifique-se de que é texto puro.')
            return redirect('lista_arquivos')

        Arquivo.objects.create(
            autor=request.user,
            nome_do_arquivo=nome,
            conteudo_do_arquivo=conteudo
        )
        messages.success(request, f'"{nome}" carregado com sucesso!')

    return redirect('lista_arquivos')

def cadastro(request):
    if request.user.is_authenticated:
        return redirect('lista_arquivos')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'gerenciador/cadastro.html', {'form': form})

def visualizar_html(request, arquivo_id):
    arquivo = get_object_or_404(Arquivo, id=arquivo_id)
    return HttpResponse(arquivo.conteudo_do_arquivo, content_type="text/html")

@csrf_exempt
def executar_codigo_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            codigo = data.get('codigo', '')
            respostas = data.get('respostas', []) 

            iterador_respostas = iter(respostas)

            def input_simulado(prompt=""):
                try:
                    return next(iterador_respostas)
                except StopIteration:
                    raise EOFError("Entrada de dados não fornecida pelo usuário.")

            def exit_simulado(*args, **kwargs):
                print("Sessão finalizada pelo comando exit().")
                return

            stdout_antigo = sys.stdout
            sys.stdout = buffer_saida = io.StringIO()

            ambiente_execucao = {
                '__builtins__': __builtins__.copy(),
            }
            ambiente_execucao['__builtins__']['input'] = input_simulado
            ambiente_execucao['__builtins__']['exit'] = exit_simulado
            ambiente_execucao['__builtins__']['quit'] = exit_simulado

            erro = None
            try:
                exec(codigo, ambiente_execucao)
            except Exception as e:
                erro = str(e)

            sys.stdout = stdout_antigo
            saida_terminal = buffer_saida.getvalue()

            return JsonResponse({
                'saida': saida_terminal,
                'erro': erro
            })
        except Exception as e:
            return JsonResponse({'saida': '', 'erro': f'Erro interno no servidor: {str(e)}'})

@csrf_exempt
def executar_bash_view(request):
    if request.method == 'POST':
        # Retorna uma resposta fixa sem usar subprocess
        return JsonResponse({
            'saida': "Conexao com a view Bash realizada com sucesso (Modo Teste).",
            'erro': None
        })
