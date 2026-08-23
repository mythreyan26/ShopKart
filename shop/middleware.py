from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse

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
