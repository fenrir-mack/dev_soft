from django.contrib import admin
from .models import Categoria, Trilha, Etapa, Topico, Projeto, ProgressoTrilha, ProgressoTopico


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)


class EtapaInline(admin.TabularInline):
    model = Etapa
    extra = 1
    ordering = ['ordem']


class ProjetoInline(admin.TabularInline):
    model = Projeto
    extra = 1
    ordering = ['ordem']


@admin.register(Trilha)
class TrilhaAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'categoria', 'dificuldade', 'visibilidade', 'total_salvos')
    list_filter = ('dificuldade', 'visibilidade', 'categoria')
    search_fields = ('titulo', 'descricao')
    inlines = [EtapaInline, ProjetoInline]


class TopicoInline(admin.TabularInline):
    model = Topico
    extra = 1
    ordering = ['ordem']


@admin.register(Etapa)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'trilha', 'ordem')
    list_filter = ('trilha',)
    search_fields = ('titulo',)
    inlines = [TopicoInline]
    ordering = ['trilha', 'ordem']


@admin.register(Topico)
class TopicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'etapa', 'ordem', 'texto')
    list_filter = ('etapa__trilha',)
    search_fields = ('texto',)
    ordering = ['etapa', 'ordem']


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('id', 'trilha', 'titulo', 'ordem')
    list_filter = ('trilha',)
    search_fields = ('titulo', 'descricao')
    ordering = ['trilha', 'ordem']


@admin.register(ProgressoTrilha)
class ProgressoTrilhaAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trilha', 'status', 'progresso_percentual', 'data_inicio', 'data_ultima_modificacao')
    list_filter = ('status', 'trilha')
    search_fields = ('user__username', 'trilha__titulo')
    readonly_fields = ('progresso_percentual', 'data_inicio', 'data_ultima_modificacao')
    ordering = ['user', 'trilha']


@admin.register(ProgressoTopico)
class ProgressoTopicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'topico', 'concluido', 'data_conclusao')
    list_filter = ('concluido', 'topico__etapa__trilha')
    search_fields = ('user__username', 'topico__etapa__titulo', 'topico__texto')
    ordering = ['user', 'topico__etapa', 'topico__ordem']
