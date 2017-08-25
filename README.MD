# Lanchonete IFTO

Sistema de gerenciamento da utilização de beneficios destinados à alimentação no campus.


## Como utilizar?
1 Clone o repositório.

```console
git clone https://github.com/ricardopimentel/Restaurante.git Restaurante
```

2 Crie um virtualenv com python 3.5

```console
cd Restaurante
python -m venv .Restaurante
```

3 Ative o virtualenv

```console
source .Restaurante/bin/activate
```

4 Instale as dependêcias

```console
sudo apt-get install libmysqlclient-dev
pip install -r requirements.txt
```

5 Configure a instancia com o .env

```console
cp contrib/env-sample .env
nano .env
```

   - Defina uma SECRET_KEY segura para a instância
   - Defina DEBUG=False

6 Rodar as migrações

```console
python manage.py migrate
```

7 Execute os testes

```console
python manage.py test
```