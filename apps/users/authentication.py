# apps/users/authentication.py
"""
Backends d'authentification pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class EmailAuthBackend(ModelBackend):
    """
    Authentification par email ou nom d'utilisateur.
    Permet aux utilisateurs de se connecter avec leur email OU leur nom d'utilisateur.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifie un utilisateur par email ou username
        """
        if username is None:
            username = kwargs.get('username')
        
        if password is None or username is None:
            return None
        
        try:
            # Recherche par email ou username
            user = User.objects.get(
                Q(email__iexact=username) | 
                Q(username__iexact=username)
            )
            
            # Vérifier le mot de passe
            if user.check_password(password):
                # Vérifier si le compte est actif
                if self.user_can_authenticate(user):
                    logger.info(f"✅ Authentification réussie pour {username}")
                    return user
                else:
                    logger.warning(f"⚠️ Compte inactif ou désactivé: {username}")
                    return None
            
            logger.warning(f"❌ Mot de passe incorrect pour {username}")
            
        except User.DoesNotExist:
            logger.warning(f"❌ Utilisateur non trouvé: {username}")
            return None
        
        except Exception as e:
            logger.error(f"🔴 Erreur d'authentification: {str(e)}")
            return None
        
        return None
    
    def get_user(self, user_id):
        """
        Récupère un utilisateur par son ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class APIAuthBackend(ModelBackend):
    """
    Backend d'authentification spécifique pour l'API.
    Vérifie si l'utilisateur a l'accès API activé.
    Nécessite que le modèle User possède un champ `api_access_enabled` (booléen).
    À ajouter dans le modèle si nécessaire, ou supprimer ce backend.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentification avec vérification de l'accès API
        """
        user = super().authenticate(request, username, password, **kwargs)
        
        if user and getattr(user, 'api_access_enabled', True):
            return user
        
        if user and not getattr(user, 'api_access_enabled', True):
            logger.warning(f"❌ Accès API désactivé pour {user.email}")
        
        return None


class TokenAuthBackend(ModelBackend):
    """
    Backend pour l'authentification par token (API) - optionnel.
    Utilise le modèle Token de DRF (si installé).
    Pour IntelliOLT, on utilise JWT, ce backend n'est pas nécessaire par défaut.
    On le garde si vous utilisez aussi des tokens statiques.
    """
    
    def authenticate(self, request, token=None, **kwargs):
        """
        Authentification par token API
        """
        if not token:
            return None
        
        try:
            from rest_framework.authtoken.models import Token
            token_obj = Token.objects.get(key=token)
            user = token_obj.user
            
            if user and user.is_active:
                logger.info(f"✅ Authentification par token réussie pour {user.email}")
                return user
            
        except Exception as e:
            logger.error(f"🔴 Erreur d'authentification par token: {str(e)}")
            return None