import time
from importlib import import_module
from django.conf import settings
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.exceptions import SessionInterrupted
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import http_date
from django.http import HttpResponse


class DualSessionMiddleware(SessionMiddleware):
    """
    Separates Django Admin sessions from Storefront / Customer sessions.
    
    Prevents the issue where logging into a customer account on the storefront
    overwrites the session and logs the user out of the admin panel.
    - Admin requests (/admin/...) use 'admin_sessionid'.
    - Storefront requests use standard 'sessionid'.
    """
    ADMIN_COOKIE_NAME = 'admin_sessionid'

    def _is_admin_path(self, request):
        return request.path_info.startswith('/admin')

    def process_request(self, request):
        if self._is_admin_path(request):
            session_key = request.COOKIES.get(self.ADMIN_COOKIE_NAME)
            if session_key:
                request.session = self.SessionStore(session_key)
            else:
                # If admin cookie not yet present, check if storefront session has a staff user
                main_cookie = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
                seeded = False
                if main_cookie:
                    try:
                        main_session = self.SessionStore(main_cookie)
                        user_id = main_session.get(SESSION_KEY)
                        backend = main_session.get(BACKEND_SESSION_KEY)
                        hash_val = main_session.get(HASH_SESSION_KEY)
                        if user_id:
                            from django.contrib.auth import get_user_model
                            User = get_user_model()
                            u = User.objects.filter(pk=user_id, is_active=True, is_staff=True).first()
                            if u:
                                admin_session = self.SessionStore()
                                admin_session[SESSION_KEY] = user_id
                                admin_session[BACKEND_SESSION_KEY] = backend
                                admin_session[HASH_SESSION_KEY] = hash_val
                                admin_session.save()
                                request.session = admin_session
                                request._force_admin_cookie = True
                                seeded = True
                    except Exception:
                        pass
                if not seeded:
                    request.session = self.SessionStore(None)
        else:
            session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
            request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response

        cookie_name = self.ADMIN_COOKIE_NAME if self._is_admin_path(request) else settings.SESSION_COOKIE_NAME
        forced = getattr(request, '_force_admin_cookie', False)

        if cookie_name in request.COOKIES and empty:
            response.delete_cookie(
                cookie_name,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
            need_vary_cookie = True
        else:
            need_vary_cookie = accessed
            if (modified or settings.SESSION_SAVE_EVERY_REQUEST or forced) and not empty:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = http_date(expires_time)
                if response.status_code < 500:
                    try:
                        request.session.save()
                    except UpdateError:
                        raise SessionInterrupted(
                            "The request's session was deleted before the request completed."
                        )
                    response.set_cookie(
                        cookie_name,
                        request.session.session_key,
                        max_age=max_age,
                        expires=expires,
                        domain=settings.SESSION_COOKIE_DOMAIN,
                        path=settings.SESSION_COOKIE_PATH,
                        secure=settings.SESSION_COOKIE_SECURE or None,
                        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                        samesite=settings.SESSION_COOKIE_SAMESITE,
                    )
                    need_vary_cookie = True
        if need_vary_cookie:
            patch_vary_headers(response, ("Cookie",))
        return response


class APICORSMiddleware(MiddlewareMixin):
    """
    Lightweight CORS middleware for REST API endpoints (/api/).
    Allows cross-platform mobile apps (React Native, Flutter, Expo, Ionic, etc.)
    and web frontends to make requests seamlessly.
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            if request.method == 'OPTIONS':
                response = HttpResponse()
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
                response['Access-Control-Allow-Credentials'] = 'true'
                return response
        return None

    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
        return response
