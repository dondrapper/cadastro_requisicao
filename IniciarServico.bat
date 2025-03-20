@echo off
echo Iniciando o Sistema de Controle...
sc start SistemaRequisicao
start "" "http://localhost:8501"
echo Serviço iniciado e navegador aberto.