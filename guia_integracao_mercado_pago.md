# Guia de Integração: Mercado Pago PIX 🚀💳

Este guia explica como configurar sua conta do Mercado Pago para que o sistema de Restaurante processe pagamentos PIX reais.

## Passo 1: Acessar o Painel de Desenvolvedores
1.  Acesse o [Painel do Mercado Pago Developers](https://www.mercadopago.com.br/developers/panel).
2.  Faça login com sua conta do Mercado Pago (a mesma que você usa no app).

## Passo 2: Criar uma Aplicação
1.  Clique em **"Criar aplicação"**.
2.  Dê um nome (ex: `Restaurante IFTO`).
3.  Tipo de solução: **"Pagamentos Online"**.
4.  Produto: **"Checkout Pro"** ou **"Checkout Transparente"** (funciona para ambos).
5.  Responda "Sim" para as perguntas de segurança e clique em **"Criar"**.

## Passo 3: Obter sua Chave (Access Token)
1.  No menu lateral da sua nova aplicação, clique em **"Credenciais de Produção"**.
2.  Você verá um campo chamado **Access Token**. Ele começa com `APP_USR-...`.
3.  **Copie este token**. Ele é a "Senha" que permite ao sistema falar com o banco.

> [!CAUTION]
> **Segurança:** Nunca compartilhe seu Access Token com ninguém. Ele dá acesso total à sua conta de vendedor.

## Passo 4: Configurar o Webhook (Notificação Automática)
Isso é o que avisa o sistema que o aluno pagou, sem que ele precise te mostrar o comprovante!

1.  No menu lateral, vá em **"Webhooks"**.
2.  No campo de **URL**, coloque o endereço do seu site seguido de: `/ticket/pix/webhook/`
    *   Exemplo: `https://seu-dominio.com.br/ticket/pix/webhook/`
3.  Em **"Eventos"**, marque a opção: **`payment`** (pagamentos).
4.  Clique em **"Salvar"**.

## Passo 5: Salvar no Sistema do Restaurante
1.  Acesse seu sistema como **Administrador**.
2.  Vá em **Administração > Configuração PIX**.
3.  No campo **Access Token**, cole a chave que você copiou no Passo 3.
4.  No campo **Webhook URL**, cole a URL que você definiu no Passo 4.
5.  Clique em **Salvar**.

---

### ✅ Pronto! 
Agora, quando um aluno gerar um PIX, o Mercado Pago saberá para onde enviar o dinheiro, e o seu sistema saberá instantaneamente quando o pagamento for aprovado para liberar o ticket.

> [!TIP]
> **Modo de Teste:** Se você quiser testar sem gastar dinheiro real, pode usar as **"Credenciais de Teste"** no Passo 3 e simular pagamentos no ambiente de Sandbox do Mercado Pago.
