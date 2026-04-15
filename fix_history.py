import os
import django
import datetime
import sys

# Setup Django
sys.path.append('d:\\Documentos\\Projetos\\Restaurante')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurante.settings")
django.setup()

from restaurante.core.models import venda
from restaurante.ticket_estudante.models import TicketAluno

def backfill_origem():
    # Pegamos todos os tickets que já foram usados
    tickets = TicketAluno.objects.filter(usado=True)
    total_tickets = tickets.count()
    print(f"Iniciando processamento de {total_tickets} tickets usados...")
    
    count = 0
    not_found = 0
    
    for t in tickets:
        if t.data_utilizacao:
            # Procuramos uma venda associada a este aluno no mesmo intervalo de tempo (2 minutos de margem)
            # e que ainda esteja como MANUAL
            start = t.data_utilizacao - datetime.timedelta(minutes=2)
            end = t.data_utilizacao + datetime.timedelta(minutes=2)
            
            vendas = venda.objects.filter(
                id_aluno=t.id_aluno,
                data__range=[start, end],
                origem='MANUAL'
            )
            
            if vendas.exists():
                # Geralmente haverá apenas uma, mas marcamos todas as correspondentes
                for v in vendas:
                    v.origem = 'TICKET'
                    v.save()
                    count += 1
            else:
                not_found += 1

        if (count + not_found) % 500 == 0:
            print(f"Progresso: {count + not_found}/{total_tickets} processados. Atualizados: {count}")

    print(f"Concluído!")
    print(f"Total de vendas atualizadas para 'TICKET': {count}")
    print(f"Tickets sem venda correspondente (provavelmente muito antigos): {not_found}")

if __name__ == "__main__":
    backfill_origem()
