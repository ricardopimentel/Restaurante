# encoding: utf-8
import sys
from ldap3 import Server, Connection, AUTO_BIND_NO_TLS, SUBTREE, ALL_ATTRIBUTES
from ldap3.core.exceptions import LDAPInvalidCredentialsResult

from restaurante.administracao.models import config


class conexaoAD(object):

    def __init__(self, username, password):
        try:
            conf = config.objects.get(id=1)
            self.username = username
            self.password = password
            self.base = config.base
            self.dominio = conf.dominio
            self.endservidor = conf.endservidor
            self.filter = conf.filter
        except:
            self.username = username
            self.password = password
            self.base = ''
            self.dominio = ''
            self.endservidor = ''
            self.felter = ''

        # servidor ad
        self.LDAP_SERVER = 'ldap://%s' % self.endservidor
        # nome completo do usuario no AD
        self.LDAP_USERNAME = self.username + '@' + self.dominio
        # sua senha
        self.LDAP_PASSWORD = self.password

    def Login(self):
        try:
            with Connection(Server(self.endservidor, use_ssl=True),
                            auto_bind=AUTO_BIND_NO_TLS,
                            read_only=True,
                            check_names=True,
                            user=self.LDAP_USERNAME, password=self.password) as c:
                user_filter = '(&' + self.filter + '(|(name=%s)))' % self.username
                print(user_filter)
                c.search(search_base=self.base, search_filter=user_filter, search_scope=SUBTREE,
                         attributes=['displayName', 'memberof'], get_operational_attributes=False)

            # print(c.response_to_json())
            # print(c.result)
            res = (c.response)
            if 'searchResEntry' in str(res):
                return res[0]['attributes']
            else:
                return 'o'  # Usuario fora do escopo permitido

        except:
            if 'invalidCredentials' in str(sys.exc_info()):
                return 'i'  # Credenciais Invalidas
            elif 'LDAPSocketOpenError' in str(sys.exc_info()):
                print(sys.exc_info())
                return 'n'  # Servidor não encotrado


    def ListaAlunos(self):
        try:
            with Connection(Server(self.endservidor, use_ssl=True),
                            auto_bind=AUTO_BIND_NO_TLS,
                            read_only=True,
                            check_names=True,
                            user=self.LDAP_USERNAME, password=self.password) as c:
                user_filter = '(&(!(userAccountControl:1.2.840.113556.1.4.803:=2))(memberof=CN=G_PARAISO_DO_TOCANTINS_ALUNOS, CN=Users,DC=ifto,DC=local))'
                c.search(search_base=self.base, search_filter=user_filter, search_scope=SUBTREE,
                         attributes=['description', 'mail', 'sAMAccountName', 'displayName'],
                         get_operational_attributes=False)

            res = (c.response)
            return res
        except:
            print('excessão')
            print(sys.exc_info())
            if 'invalidCredentials' in str(sys.exc_info()):
                return 'i'  # Credenciais Invalidas
            elif 'LDAPSocketOpenError' in str(sys.exc_info()):
                print(sys.exc_info())
                return 'n'  # Servidor não encotrado

    def DadosAluno(self, cpf):
        try:
            with Connection(Server(self.endservidor, use_ssl=True),
                            auto_bind=AUTO_BIND_NO_TLS,
                            read_only=True,
                            check_names=True,
                            user=self.LDAP_USERNAME, password=self.password) as c:
                user_filter = '(&(memberof=CN=G_PARAISO_DO_TOCANTINS_ALUNOS, CN=Users,DC=ifto,DC=local)(sAMAccountName=*%s*))' % cpf
                c.search(search_base=self.base, search_filter=user_filter, search_scope=SUBTREE,
                         attributes=['description', 'mail', 'sAMAccountName', 'displayName'],
                         get_operational_attributes=False)

            res = (c.response)
            return res
        except:
            if 'invalidCredentials' in str(sys.exc_info()):
                return 'i'  # Credenciais Invalidas
            elif 'LDAPSocketOpenError' in str(sys.exc_info()):
                print(sys.exc_info())
                return 'n'  # Servidor não encotrado

    def PrimeiroLogin(self, Username, Password, Dominio, Endservidor, Filtro):
        # servidor ad
        LDAP_SERVER = 'ldap://%s' % Endservidor
        # nome completo do usuario no AD
        LDAP_USERNAME = Username + '@' + Dominio

        try:
            with Connection(Server(Endservidor, use_ssl=True),
                            auto_bind=AUTO_BIND_NO_TLS,
                            read_only=True,
                            check_names=True,
                            user=LDAP_USERNAME, password=Password) as c:
                user_filter = '(&' + Filtro + '(name=%s)' % Username
                c.search(search_base=self.base, search_filter=user_filter, search_scope=SUBTREE,
                         attributes=['displayName', 'memberof'], get_operational_attributes=False)

            res = (c.response)
            print(res)
            if res:
                return res[0]['attributes']
            else:
                return 'o'  # Usuario fora do escopo permitido

        except:
            if 'invalidCredentials' in str(sys.exc_info()):
                return 'i'  # Credenciais Invalidas
            elif 'LDAPSocketOpenError' in str(sys.exc_info()):
                print(sys.exc_info())
                return 'n'  # Servidor não encotrado
    
    #def TestarCredenciais(self): # desconsiderar metodo, apenas testes
        #try:
            # build a client
            #ldap_client = ldap.initialize(self.LDAP_SERVER)
            # perform a synchronous bind
            #ldap_client.set_option(ldap.OPT_REFERRALS, 0)
            #ldap_client.simple_bind_s(self.LDAP_USERNAME, self.LDAP_PASSWORD)
            #ldap_client.unbind()
            #return 's'
        #except ldap.INVALID_CREDENTIALS:
            #ldap_client.unbind()
            #return 'i'
        #except ldap.SERVER_DOWN:
            #return 'n'
        # all is well
        # get all user groups and store it in cerrypy session for future use
        #cherrypy.session[username] = str(ldap_client.search_s(base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs)[0][1]['memberOf'])


