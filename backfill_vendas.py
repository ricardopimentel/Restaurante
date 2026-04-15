import os
import django
from datetime import timedelta

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurante.settings')
django.setup()

from restaurante.core.models import venda
from restaurante.ticket_estudante.models import TicketAluno

def backfill():
    print("Iniciando backfill de origens de venda...")
    
    # Busca todos os tickets que já foram utilizados
    tickets_usados = TicketAluno.objects.filter(usado=True).select_related('id_aluno')
    total_tickets = tickets_usados.count()
    vendas_atualizadas = 0
    
    print(f"Encontrados {total_tickets} tickets utilizados para processar.")
    
    for ticket in tickets_usados:
        if not ticket.data_utilizacao:
            continue
            
        # Define uma janela de 5 minutos antes e depois da utilização do ticket
        # para encontrar a venda correspondente no log de vendas
        margem = timedelta(minutes=5)
        inicio = ticket.data_utilizacao - margem
        fim = ticket.data_utilizacao + margem
        
        # Busca vendas para o mesmo aluno nesse período que ainda estejam como MANUAL
        vendas = venda.objects.filter(
            id_aluno=ticket.id_aluno,
            data__range=(inicio, fim),
            origem='MANUAL'
        )
        
        for v in vendas:
            v.origem = 'TICKET'
            v.save()
            vendas_atualizadas += 1
            
    print("-" * 30)
    print(f"Processamento concluído!")
    print(f"Vendas migradas para TICKET: {vendas_atualizadas}")
    print(f"Total de tickets processados: {total_tickets}")
    print("-" * 30)

if __name__ == "__main__":
    backfill()
