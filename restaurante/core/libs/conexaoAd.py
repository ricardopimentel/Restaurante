# -*- coding: utf-8 -*-
#import ldap
import ldap3 as ldap

class conexaoAD(object):
    
    def __init__(self, username, password, base):
        self.username = username
        self.password = password
        self.base = base
        self.dominio = 'ifto.local'
        self.endservidor = '10.9.10.12'
        # servidor ad
        self.LDAP_SERVER = 'ldap://%s' % self.endservidor
        # nome completo do usuario no AD
        self.LDAP_USERNAME = self.username+ '@'+ self.dominio
        # sua senha
        self.LDAP_PASSWORD = self.password
        #base_dn = 'DC=xxx,DC=xxx'
        #ldap_filter = 'userPrincipalName=%s@%s' % username, dominio
        #attrs = ['memberOf']
        
    def Login(self):
        try:
            l=ldap.initialize(self.LDAP_SERVER)
            l.set_option(ldap.OPT_REFERRALS, 0)
            l.simple_bind_s(self.LDAP_USERNAME, self.LDAP_PASSWORD)
            user_filter = '(name=%s)' %self.username
            base_dn = self.base
            res = l.search_ext_s(base_dn, ldap.SCOPE_SUBTREE, user_filter, ['description', 'mail', 'sAMAccountName', 'displayName', 'memberof'])
            l.unbind()
            try:
                return res[0]
            except:
                return 'o' # Usuario fora do escopo permitido
        except ldap.INVALID_CREDENTIALS:
            l.unbind()
            return 'i' # Credenciais Invalidas
        except ldap.SERVER_DOWN:
            return 'n' # Servidor não encotrado

    def ListaAlunos(self):
        try:
            l=ldap.initialize(self.LDAP_SERVER)
            l.set_option(ldap.OPT_REFERRALS, 0)
            l.simple_bind_s(self.LDAP_USERNAME, self.LDAP_PASSWORD)
            user_filter = '(memberof=CN=G_PARAISO_DO_TOCANTINS_ALUNOS_BOLSISTAS, CN=Users,DC=ifto,DC=local)'
            #user_filter = '(groupMembership=cn=G_PARAISO_DO_TOCANTINS_ALUNOS_BOLSISTAS,ou=Groups,o=CUST)' #'(&(objectCategory=user)(objectClass=user)(memberOf=name=G_ADMINS_AD_IFTO))'
            base_dn = self.base
            res = l.search_ext_s(base_dn, ldap.SCOPE_SUBTREE, user_filter, ['description', 'mail', 'sAMAccountName', 'displayName'])
            l.unbind()
            return res
        except ldap.INVALID_CREDENTIALS:
            l.unbind()
            return 'i'
        except ldap.SERVER_DOWN:
            return 'n'
    
    def TestarCredenciais(self):
        try:
            # build a client
            ldap_client = ldap.initialize(self.LDAP_SERVER)
            # perform a synchronous bind
            ldap_client.set_option(ldap.OPT_REFERRALS, 0)
            ldap_client.simple_bind_s(self.LDAP_USERNAME, self.LDAP_PASSWORD)
            ldap_client.unbind()
            return 's'
        except ldap.INVALID_CREDENTIALS:
            ldap_client.unbind()
            return 'i'
        except ldap.SERVER_DOWN:
            return 'n'
        # all is well
        # get all user groups and store it in cerrypy session for future use
        #cherrypy.session[username] = str(ldap_client.search_s(base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attrs)[0][1]['memberOf'])


